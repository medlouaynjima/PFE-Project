# src/agents/conversationalagent.py
import re
import json
from typing import Optional, Dict, Any, Union
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from .agentstage import AgentState
from ..core.memory_manager import load_profile_memory


# =========================
# Utilitaires internes
# =========================

_FAMILY_MAP = {
    # variantes → valeur canonique pour malade_qualite
    "femme": "épouse",
    "épouse": "épouse",
    "conjointe": "épouse",

    "mari": "époux",
    "époux": "époux",
    "conjoint": "époux",

    "fils": "fils",
    "garçon": "fils",
    "garcon": "fils",

    "fille": "fille",

    "enfant": "*children*",
    "enfants": "*children*",

    "ayant droit": "*dependents*",
    "ayants droit": "*dependents*",
}

_MONTHS_FR = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "août": 8, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12
}


def _safe_json_loads(s: str) -> Optional[dict]:
    """Parse JSON en sécurité, retourne None si échec."""
    try:
        return json.loads(s)
    except Exception:
        # tente extraction JSON minifié
        try:
            start = s.find("{")
            end = s.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(s[start:end+1])
        except Exception:
            return None
    return None


def _simple_followup_rules(question: str) -> Dict[str, Any]:
    """
    Fallback rules-based detector → retourne un dict structuré minimal:
    {"is_follow_up": bool, "base_hint": "...", "deltas": {...}, "confidence": float}
    """
    q = (question or "").lower().strip()
    is_short = len(q.split()) <= 6

    patterns = [
        r"\bet\s+pour\b",
        r"\bet\s+(mon|ma|mes|le|la|les)\b",
        r"qu'en\s+est-il",
        r"\bet\s+alors\b",
        r"\bet\s+sinon\b",
        r"\bet\s+aussi\b",
        r"\bet\s+le\s+dernier\b",
        r"\b(prochain|suivant|dernier)\b",
        r"\bet\s+ça\b",
        r"\bet\s+cel(l|l)e(-| )?\s*(ci|là)\b",
        r"^\s*\w+\s*\?*\s*$",
        r"\b(par|sur)\s+(mois|année|an|trimestre|quarter|semaine|jour|janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\b",
        r"\b\d{4}\b",
        r"^\s*\d{1,4}\s*\?*\s*$",
        r"\bstatut\b",
        r"\bmontant\b",
        r"\bcombien\b",
    ]
    is_fu = is_short or any(re.search(p, q) for p in patterns)

    deltas: Dict[str, Any] = {}

    # famille
    for k, v in _FAMILY_MAP.items():
        if re.search(rf"\b{k}\b", q):
            deltas["malade_qualite"] = v
            break

    # période (année)
    year_m = re.search(r"\b(20\d{2}|19\d{2})\b", q)
    if year_m:
        deltas.setdefault("periode", {})["year"] = int(year_m.group(1))

    # période (mois)
    for mname, mid in _MONTHS_FR.items():
        if re.search(rf"\b{mname}\b", q):
            deltas.setdefault("periode", {})["month"] = mid
            break

    # catégorie
    if re.search(r"\b(pharmacie|médicaments|medicaments)\b", q):
        deltas["categorie"] = "Pharmacie"
    elif re.search(r"\b(analyses?)\b", q):
        deltas["categorie"] = "Analyses"
    elif re.search(r"\b(radio|radiologie)\b", q):
        deltas["categorie"] = "Radio"

    # hint de base si on voit "remboursement" etc. (sinon inconnu)
    base_hint = "inconnu"
    if re.search(r"\b(remboursement|remboursé|rembourser|payer|paiement|montant|ticket|reste à payer|reste\s*a\s*payer)\b", q):
        base_hint = "remboursement"
    if re.search(r"\b(réclamation|reclamation|plainte|litige|contestation)\b", q):
        base_hint = "reclamation"
    if re.search(r"\b(dossier|ticket\s*modérateur)\b", q):
        base_hint = "dossier"
    if re.search(r"\b(médecin|medecin|traitant)\b", q):
        base_hint = "medecin"

    confidence = 0.55 if is_fu else 0.2
    if "malade_qualite" in deltas or "periode" in deltas or "categorie" in deltas:
        confidence = max(confidence, 0.65)

    return {
        "is_follow_up": bool(is_fu),
        "base_hint": base_hint,
        "deltas": deltas or {},
        "confidence": confidence
    }


# =========================
# Agent conversationnel
# =========================

class ConversationalAgent(Runnable):
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,      # détection déterministe
            max_tokens=300,
        )

    # ---------- Détection Follow-up (LLM JSON) ----------
    def _llm_followup_probe(self, question: str, state: AgentState) -> Optional[Dict[str, Any]]:
        """Appel LLM cadré → JSON minifié. Retourne None si parsing échoue."""
        prev_intent = state.get("last_intent", "") or state.get("intent_label", "") or ""
        prev_table = state.get("last_table", "") or ""
        prev_plan = state.get("last_query_plan", "") or ""
        summary = state.get("summary", "") or ""

        sys = (
            "Tu es un détecteur de 'follow-up'. Réponds UNIQUEMENT en JSON minifié (une seule ligne), "
            "sans aucun texte autour, sans explication.\n"
            "Schéma JSON:\n"
            '{"is_follow_up": bool, "base_hint": "remboursement|reclamation|dossier|medecin|inconnu", '
            '"deltas": {"malade_qualite": "épouse|époux|fils|fille|*children*|*dependents*", '
            '"periode": {"year": int|null, "month": int|null}, "categorie": "Pharmacie|Analyses|Radio|null"}, '
            '"confidence": float}\n'
            "Règles:\n"
            "- Follow-up = même sujet que la question précédente mais avec un paramètre changé (personne, période, catégorie...).\n"
            "- Mappe le langage → malade_qualite: 'ma femme/mon épouse'→'épouse'; 'mon mari'→'époux'; 'mon fils'→'fils'; "
            "'ma fille'→'fille'; 'mes enfants'→'*children*'; 'mes ayants droit'→'*dependents*'.\n"
            "- Périodes: détecte années (ex: 2024) et mois FR (janvier..décembre → 1..12).\n"
            "- Catégories: 'pharmacie|médicaments'→'Pharmacie'; 'analyses'→'Analyses'; 'radio|radiologie'→'Radio'.\n"
            "- base_hint: déduis à partir du contexte précédent + message actuel; sinon 'inconnu'.\n"
            "- confidence: 0..1.\n"
        )

        user = (
            f"previous_intent: {prev_intent}\n"
            f"previous_table: {prev_table}\n"
            f"previous_plan: {prev_plan}\n"
            f"summary: {summary[:1000]}\n"
            f"user_message: {question}"
        )

        try:
            resp = self.llm.invoke([SystemMessage(content=sys), HumanMessage(content=user)])
            parsed = _safe_json_loads(resp.content or "")
            return parsed
        except Exception:
            return None

    def _detect_follow_up_hybrid(self, question: str, state: AgentState) -> Dict[str, Any]:
        """
        Détection robuste: LLM JSON + fallback règles.
        Retourne dict structuré avec clés:
          - is_follow_up (bool)
          - base_hint (str)
          - deltas (dict)
          - confidence (float)
          - source ("llm"|"rules")
        """
        # 1) probe LLM
        parsed = self._llm_followup_probe(question, state)
        if isinstance(parsed, dict) and "is_follow_up" in parsed:
            parsed["source"] = "llm"
            # sanity checks
            if not isinstance(parsed.get("deltas", {}), dict):
                parsed["deltas"] = {}
            return parsed

        # 2) fallback règles
        rb = _simple_followup_rules(question)
        rb["source"] = "rules"
        return rb

    # ---------- Intentions spécifiques ----------
    def _is_claim_intent_strong(self, question: str) -> bool:
        """Détecte une intention forte de réclamation (refus / révision / contestation)."""
        import re as _re
        q = (question or "").lower()
        claim_triggers = [
            r"\brefus(e|é|)\b", r"\brefus\b",
            r"\brévision\b", r"\brevision\b", r"\b(re)?examen\b", r"\brecours\b",
            r"\bcontestation\b", r"\bcontester\b", r"\blitige\b", r"\blitiges?\b",
            r"\binjustice\b", r"\binjuste\b", r"\barbitrage\b", r"\bmédiation\b", r"\bmediation\b",
        ]
        return any(_re.search(p, q) for p in claim_triggers)

    def _attach_claim_context(self, state):
        """Passe des indices au ClaimsAgent, sans classer la complexité."""
        checks = [
            "Vérifier le code acte (nomenclature CNAM)",
            "Comparer le tarif conventionnel CNAM appliqué",
            "Contrôler la présence et la lisibilité des pièces jointes",
            "Vérifier la concordance d'identité (adhérent/ayant-droit/dossier/prescriptions)",
            "Vérifier que le médecin est conventionné et que l’acte est prescrit",
        ]
        state["needs_claims"] = True
        state["claims_expected_checks"] = checks
        state["claims_intent"] = "appeal_or_refusal"
        return state

    def _detect_claim_question(self, question: str) -> bool:
        q = question.lower()

        claim_patterns = [
            r"réclamation", r"reclamation", r"claim", r"problème", r"probleme",
            r"erreur", r"incident", r"dysfonctionnement",
            r"plainte", r"conflit", r"litige", r"désaccord", r"contestation",

            r"vérifier\s+le\s+statut\s+de\s+ma\s+réclamation",
            r"statut\s+de\s+ma\s+réclamation",
            r"où\s+en\s+est\s+ma\s+réclamation",
            r"suivre\s+ma\s+réclamation",
            r"avancement\s+de\s+ma\s+réclamation",
            r"état\s+de\s+ma\s+réclamation",

            r"remboursement\s+concernant",
            r"remboursement\s+de\s+(ma|mon|mes)",
            r"remboursement\s+pour\s+(ma|mon|mes)",
            r"faire\s+le\s+remboursement",
            r"ont\s+fait\s+le\s+remboursement",
            r"questionné\s+.*\s+remboursement",
            r"question\s+.*\s+remboursement",

            r"(femme|épouse|fils|fille|enfant|mari|époux|conjoint|conjointe)",
            r"pour\s+(ma|mon|mes)\s+(femme|épouse|fils|fille|enfant|mari|époux|conjoint|conjointe)",
            r"concernant\s+(ma|mon|mes)\s+(femme|épouse|fils|fille|enfant|mari|époux|conjoint|conjointe)",
            r"de\s+(ma|mon|mes)\s+(femme|épouse|fils|fille|enfant|mari|époux|conjoint|conjointe)",

            r"(montant|argent|paiement|payé|remboursé)\s+\d+",
            r"combien\s+(ai|j'ai)\s+(reçu|obtenu|touché)",

            r"statut\s+de\s+(mon|ma|mes)",
            r"dossier\s+de\s+(ma|mon|mes)",

            r"(mon|ma|mes)\s+remboursement",
            r"remboursement\s+(de|du|des)\s+(mon|ma|mes)",
        ]
        return any(re.search(p, q) for p in claim_patterns)

    # ---------- API Runnable ----------
    def invoke(self, input: Union[Dict[str, Any], AgentState], config: Optional[RunnableConfig] = None) -> AgentState:
        if isinstance(input, dict):
            state = AgentState(**input)
        else:
            state = input
        return self._process_question(state, config)

    # ---------- Cœur du routage ----------
    def _process_question(self, state: AgentState, config: Optional[RunnableConfig] = None) -> AgentState:
        try:
            question = state.get("question", "")
            print(f"[CONVERSATIONAL] Processing question: {question}")

            # Charger mémoire profil (adherent/medecin)
            new_state = load_profile_memory(state, config)

            # 0) Garde-fous sécurité (hors périmètre)
            policy_patterns = [
                r"\b(adherent|médecin|medecin|user|compte)\s+id\s*[:=]\s*\d+",
                r"\b(un\s+autre|autres|tous|tout le monde|n'importe\s+qui)\b",
                r"\bcompar(er|aison)\b\s+.*\b(adherents?|medecins?)\b",
            ]
            if any(re.search(p, question.lower()) for p in policy_patterns):
                new_state["response"] = (
                    "Désolé, je ne peux pas répondre à des demandes hors périmètre ou concernant d'autres "
                    "personnes. Pour protéger la confidentialité, je n'accède qu'à vos propres données."
                )
                new_state["needs_database"] = False
                new_state["needs_claims"] = False
                return new_state

            
            # 0bis) Traitement médecin spécifique : si demande sur patients/dossiers/remboursements
            role = state.get("role", "").upper()
            if role == "MEDECIN":
                if any(kw in question.lower() for kw in ["patients", "trait", "dossier", "rembourse", "consult"]):
                    print("[ROUTER] Medecin data request detected")
                    new_state["needs_database"] = True
                    new_state["needs_claims"] = True
                    new_state["response"] = "Très bien, je vais chercher les informations concernant vos patients."
                    new_state["last_intent"] = "medecin_data_request"
                    return new_state
            
            
            # 1) Intention forte de réclamation → Claims
            if self._is_claim_intent_strong(question):
                print("[ROUTER] Strong claim intent detected → route to ClaimsAgent")
                new_state = self._attach_claim_context(new_state)
                new_state["last_intent"] = "strong_claim"
                return new_state

            # 2) Questions spécifiques dossier (vérifications ticket/modérateur…)
            if any(re.search(p, question.lower()) for p in [
                r"ticket.*modérateur.*\d+%.*dossier.*(fille|fils|enfant|épouse|époux)",
                r"dossier.*(fille|fils|enfant|épouse|époux).*ticket.*modérateur",
                r"remboursement.*(fille|fils|enfant|épouse|époux).*incorrect",
                r"montant.*(fille|fils|enfant|épouse|époux).*ne.*correspond",
                r"calcul.*(fille|fils|enfant|épouse|époux).*incorrect"
            ]):
                print("[ROUTER] Détection question spécifique sur dossier → route to ClaimsAgent")
                new_state["needs_claims"] = True
                new_state["needs_database"] = True
                new_state["intent_label"] = "verification_dossier_specifique"
                new_state["last_intent"] = "verification_dossier_specifique"
                return new_state

            # 3) Vérification d'enregistrement de dossier
            if any(re.search(p, question.lower()) for p in [
                r"confirmation.*réception.*dossier",
                r"est.*bien.*enregistré",
                r"vérifier.*enregistrement",
                r"reçu.*confirmation",
                r"dossier.*enregistré"
            ]):
                print("[ROUTER] Détection question vérification d'enregistrement → route to ClaimsAgent")
                new_state["needs_claims"] = True
                new_state["needs_database"] = True
                new_state["intent_label"] = "verification_enregistrement"
                new_state["last_intent"] = "verification_enregistrement"
                return new_state

            # 4) Salutations / small talk
            is_general = any(re.search(p, question.lower()) for p in [
                r"bonjour", r"salut", r"merci", r"au revoir", r"bye",
                r"comment allez-vous", r"ça va", r"qui êtes-vous", r"que faites-vous", r"aide"
            ])
            if is_general and not self._detect_claim_question(question):
                if question.lower().strip() in ["bonjour", "salut", "hello", "hi"]:
                    resp = "Bonjour ! Je suis votre assistant virtuel pour les questions d'assurance santé. Comment puis-je vous aider aujourd'hui ?"
                elif question.lower().strip() in ["merci", "thank you", "thanks"]:
                    resp = "De rien ! N'hésitez pas si vous avez d'autres questions."
                elif question.lower().strip() in ["au revoir", "bye", "goodbye"]:
                    resp = "Au revoir ! Prenez soin de vous."
                else:
                    resp = "Bonjour ! Je suis là pour vous aider avec vos questions d'assurance santé. Que puis-je faire pour vous ?"
                new_state["response"] = resp
                new_state["needs_database"] = False
                new_state["needs_claims"] = False
                new_state["last_intent"] = "chitchat"
                return new_state

            # 5) Détection follow-up (hybride) si contexte existe
            has_context = bool(state.get("summary", "").strip()) or bool(state.get("adherent_memory", "").strip())
            # On tente la détection hybride si la question est courte OU si mots-clés follow-up
            quick_trigger = _simple_followup_rules(question)["is_follow_up"]
            if has_context and quick_trigger:
                fu = self._detect_follow_up_hybrid(question, state)
                if fu.get("is_follow_up") and fu.get("confidence", 0) >= 0.5:
                    print(f"[DEBUG FOLLOW-UP] Detected follow-up question (source={fu.get('source')}, conf={fu.get('confidence'):.2f})")
                    new_state["is_follow_up"] = True
                    new_state["follow_up"] = fu  # {is_follow_up, base_hint, deltas, confidence, source}

                    base_hint = fu.get("base_hint", "inconnu")
                    # Routage: par défaut Claims + (Database si hint data)
                    new_state["needs_claims"] = True
                    new_state["needs_database"] = base_hint in ("remboursement", "dossier", "medecin")
                    # Pose un last_intent stable pour les agents en aval
                    new_state["last_intent"] = f"follow_up_{base_hint}"
                    return new_state

            # 6) Question data/claim générique
            if self._detect_claim_question(question):
                print(f"[DEBUG] Detected claim/data question")
                new_state["needs_claims"] = True
                new_state["needs_database"] = False
                new_state["is_follow_up"] = False
                new_state["last_intent"] = "claim_or_data"
                return new_state

            # 7) Sinon, demande générique
            new_state["response"] = (
                "Je suis là pour vous aider avec vos questions d'assurance santé. "
                "Pouvez-vous me donner plus de détails sur ce que vous recherchez ?"
            )
            new_state["needs_database"] = False
            new_state["needs_claims"] = False
            new_state["last_intent"] = "generic"
            return new_state

        except Exception as e:
            err = f"Erreur dans l'agent conversationnel : {str(e)}"
            new_state = state.copy()
            new_state["conversational"] = {"messages": []}
            new_state["response"] = f"Je suis désolé, une erreur est survenue lors du traitement de votre demande. {err}"
            new_state["needs_database"] = False
            new_state["needs_claims"] = False
            new_state["last_intent"] = "error"
            return new_state
