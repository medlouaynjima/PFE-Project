from typing import List, Dict, Any, Optional, Union
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable
from langchain_core.runnables.config import RunnableConfig
from src.agents.agentstage import ClaimsAgentState, AgentState
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from datetime import datetime
import copy
import time
import json
import re
from src.agents.utils.summarization import get_messages_with_summary, should_summarize, update_state_with_summary
from src.agents.utils.token_logs import log_step
from src.agents.utils.email_utils import send_support_email_mailhog


claims_instructions = """Vous êtes un expert en traitement des réclamations santé/assurance.
Votre rôle est d'analyser et de traiter les réclamations des adhérents et des médecins.

TYPES DE RÉCLAMATIONS :

1. RÉCLAMATIONS SIMPLES (réponse immédiate possible) :
   - Vérification de statut de remboursement
   - Questions sur les délais de traitement
   - Demandes de montant de remboursement
   - Vérification de dossier médical
   - Questions sur la couverture
   - Suivi de dossier standard

2. RÉCLAMATIONS COMPLEXES (intervention humaine nécessaire) :
   - Litiges et contestations
   - Demandes de documents spéciaux
   - Problèmes techniques complexes
   - Cas d'exception non standard
   - Réclamations multiples
   - Problèmes de facturation complexes
   - Contestations de décisions
   - Plainte, désaccord, recours, injustice, contestation, refus, arbitrage

LOGIQUE DE TRAITEMENT :

Pour les réclamations simples :
- Identifier qu'elles peuvent être résolues avec les données disponibles
- Marquer comme "SIMPLE_CLAIM" pour traitement automatique
- Préciser les informations à vérifier dans la base de données
- Ajouter needs_database = True si nécessair

NOTE : Si l'utilisateur est un MEDECIN, il peut poser des questions sur les réclamations liées à ses patients. Ces réclamations peuvent aussi être simples si elles concernent uniquement un suivi de statut ou une consultation.


Pour les réclamations complexes :
- Identifier les points nécessitant une intervention humaine
- Marquer comme "COMPLEX_CLAIM" pour escalade
- Activer needs_human = True
- Collecter toutes les informations pertinentes

IMPORTANT :
- Ne jamais générer de réponse métier directement
- Toujours déterminer le type de réclamation
- Pour les simples : permettre l'accès à la base de données
- Pour les complexes : préparer l'escalade humaine

**À LA FIN DE VOTRE ANALYSE, AJOUTEZ TOUJOURS LE MARQUEUR EXPLICITE :**
- SIMPLE_CLAIM (si la réclamation est simple)
- COMPLEX_CLAIM (si la réclamation est complexe)

Répondez de manière professionnelle et structurée.
"""

class ClaimsAgent(Runnable):
    """Agent qui analyse et traite les réclamations santé/assurance."""
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.2)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", claims_instructions),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "Analysez cette réclamation et déterminez la meilleure approche pour la traiter.")
        ])

    # --------- LLM doc-requirements classifier ---------
    def _classify_doc_requirements_llm(self, question: str) -> Optional[dict]:
        """
        Demande au LLM si la demande nécessite des pièces justificatives avant vérification.
        Retour: dict ou None si non exploitable.
        """
        examples = [
            {
                "q": "Le montant remboursé ne correspond pas à ma facture d'analyses. Vérifiez le calcul.",
                "json": {
                    "needs_documents": True,
                    "reason": "Vérification de calcul/écart nécessite facture + ordonnance.",
                    "required_docs": [
                        "Ordonnance médicale signée",
                        "Facture détaillée des analyses",
                        "Attestation de paiement (si disponible)"
                    ],
                    "required_fields": [
                        "Numéro de dossier",
                        "Nom du bénéficiaire",
                        "Date des soins",
                        "Montant total facturé",
                        "Montant remboursé"
                    ]
                }
            },
            {
                "q": "Quel est le délai normal de traitement d’un dossier ?",
                "json": {
                    "needs_documents": False,
                    "reason": "Question FAQ générale (délais).",
                    "required_docs": [],
                    "required_fields": []
                }
            },
            {
                "q": "Le total_ordonnance est-il correct pour le dossier de ma fille ?",
                "json": {
                    "needs_documents": True,
                    "reason": "Contrôle du total facture nécessite justificatifs.",
                    "required_docs": [
                        "Facture détaillée",
                        "Ordonnance médicale"
                    ],
                    "required_fields": [
                        "Numéro de dossier",
                        "Date des soins",
                        "Montants détaillés (lignes de facture)"
                    ]
                }
            }
        ]

        sys = (
            "Tu es un classifieur. Réponds STRICTEMENT en JSON minifié avec les clés: "
            "needs_documents (bool), reason (str), required_docs (list[str]), required_fields (list[str]). "
            "Détermine si la demande nécessite des pièces justificatives pour conclure. "
            "Si la demande concerne un recalcul, un écart facture/remboursement, ou le total_ordonnance → souvent OUI. "
            "Si c’est une FAQ générale (délais, définitions) → souvent NON."
        )
        shots = "\n".join([f"Q: {e['q']}\nJSON: {json.dumps(e['json'], ensure_ascii=False)}" for e in examples])
        user = f"Q: {question}\nJSON:"

        try:
            msg = [SystemMessage(content=sys), HumanMessage(content=shots + "\n" + user)]
            out = self.llm.invoke(msg).content.strip()
            m = re.search(r"\{.*\}", out, re.S)
            if not m:
                return None
            data = json.loads(m.group(0))
            data.setdefault("needs_documents", False)
            data.setdefault("reason", "")
            data.setdefault("required_docs", [])
            data.setdefault("required_fields", [])
            # Normalisation types
            data["needs_documents"] = bool(data["needs_documents"])
            data["required_docs"] = list(map(str, data["required_docs"]))
            data["required_fields"] = list(map(str, data["required_fields"]))
            return data
        except Exception:
            return None

    def _detect_doc_requirements(self, question: str, analysis: str) -> dict:
        """
        D’abord le LLM, sinon fallback heuristique.
        """
        llm_decision = self._classify_doc_requirements_llm(question)
        if llm_decision is not None:
            return llm_decision

        # Fallback simple (robuste aux reformulations)
        q = (question or "").lower() + " " + (analysis or "").lower()
        need = any(re.search(p, q) for p in [
            r"\b(v(é|e)rifier|contr(ô|o)ler|recalculer)\b.*\b(montant|calcul|remboursement|ticket|ordonnance)\b",
            r"\b(ne\s+correspond\s+pas|diff(é|e)rence|(e|é)cart)\b.*\b(facture|remboursement|montant)\b",
            r"\btotal(?:e)?\s*ordonnance\b",
        ])
        if not need:
            return {"needs_documents": False, "reason": "", "required_docs": [], "required_fields": []}
        return {
            "needs_documents": True,
            "reason": "Vérification de montants/calculs nécessitant justificatifs (fallback).",
            "required_docs": [
                "Ordonnance médicale signée",
                "Facture détaillée",
                "Attestation de paiement (si disponible)"
            ],
            "required_fields": [
                "Numéro de dossier",
                "Bénéficiaire",
                "Date des soins",
                "Montants facturé et remboursé"
            ]
        }

    # --------------------------------------------------------

    async def arun(self, state: AgentState) -> AgentState:
        start_time = time.time()
        new_state = copy.deepcopy(state)

        messages = get_messages_with_summary(new_state, "claims")
        try:
            # Générer l'analyse de la réclamation
            print(f"[DEBUG ClaimsAgent] Starting claim analysis...")
            chain_result = await self.llm.ainvoke(
                self.prompt.format_messages(messages=messages)
            )
            analysis = chain_result.content if hasattr(chain_result, 'content') else str(chain_result)

            processing_time = time.time() - start_time
            print(f"[DEBUG ClaimsAgent] Analysis completed in {processing_time:.2f}s")

            new_state.setdefault("claims", {"messages": [], "response": ""})
            new_state["claims"]["messages"] = messages
            new_state["claims"]["response"] = analysis
            new_state["claims"]["processing_time"] = processing_time

            # Flags init
            is_simple_claim = False
            is_complex_claim = False
            needs_human = False
            needs_database = False
            claim_type = "simple"

            # --- contexte question & capacités ---
            original_question = (new_state.get("question") or "")
            q_lower = original_question.lower()
                # Exclude medical data queries from doctors (not claims)
            role = new_state.get("role", "").upper()
            if role == "MEDECIN":
                    if any(re.search(p, q_lower) for p in [
                        r"\b(patients?|consultations?|trait[ée]s?)\b",
                        r"\b(remboursements?|dossiers?)\b",
                        r"\b(coordonn[ée]es?|nom\s+(du\s+)?parent|adhérent\s+parent|adherent\s+parent|contact)\b"
                    ]):
                        print("[ClaimsAgent] Skipping non-claim medical query from MEDECIN.")
                    return new_state  # Let router continue to DatabaseAgent or fallback

            caps = new_state.get("capabilities", {}) or {}
            can_compute_tm = bool(caps.get("can_compute_ticket_moderateur", True))
            has_amount_cols = bool(caps.get("has_amount_columns", True))

            # --- Intentions SIMPLES prioritaires ---
            def has(words: List[str]) -> bool:
                return any(w in q_lower for w in words)

            # A) Confirmation / enregistrement dossier
            is_confirm_intent = (
                has(["confirm", "confirmation", "confirmer", "bien enregistr", "réception du dossier", "reception du dossier"])
                or has(["est-il bien enregistré", "est il bien enregistré", "est-ce que le dossier", "dossier reçu", "dossier bien reçu"])
            )
            if is_confirm_intent:
                is_simple_claim = True
                is_complex_claim = False
                needs_human = False
                needs_database = True
                claim_type = "simple"

            # Indicateur “montants / ticket / délais / statut”
            is_amount_like = any(k in q_lower for k in [
                "ticket", "modérat", "moderateur", "montant", "reste à payer",
                "total", "délai", "delai", "statut"
            ])

            # --- Simple consultation patterns (prioritaires aussi) ---
            if not is_simple_claim:
                simple_consultation_patterns = [
                    r"je\s+veux\s+consulter\s+mes?\s+réclamations?",
                    r"consulter\s+mes?\s+réclamations?",
                    r"voir\s+mes?\s+réclamations?",
                    r"afficher\s+mes?\s+réclamations?",
                    r"lister\s+mes?\s+réclamations?",
                    r"mes?\s+réclamations?",
                    r"statut\s+de\s+mes?\s+réclamations?",
                    r"suivi\s+de\s+mes?\s+réclamations?",
                    r"consulter.*réclamations?",
                    r"voir.*réclamations?",
                    r"mes.*réclamations?",
                    # sans accent
                    r"je\s+veux\s+consulter\s+mes?\s+reclamations?",
                    r"consulter\s+mes?\s+reclamations?",
                    r"voir\s+mes?\s+reclamations?",
                    r"mes?\s+reclamations?",
                    r"consulter.*reclamations?",
                    r"voir.*reclamations?",
                    r"mes.*reclamations?"
                ]
                if any(re.search(p, q_lower, re.IGNORECASE) for p in simple_consultation_patterns):
                    is_simple_claim = True
                    is_complex_claim = False
                    needs_human = False
                    needs_database = True
                    claim_type = "simple"

            print(f"[DEBUG ClaimsAgent] LLM Analysis: {analysis[:200]}...")
            # Si pas décidé par intentions, utiliser mots-clés sur l'analyse LLM
            if not (is_simple_claim or is_complex_claim):
                simple_keywords = [
                    "statut", "remboursement", "montant", "délai", "dossier",
                    "couverture", "vérification", "information", "question",
                    "suivi", "consultation", "ordonnance", "facture"
                ]
                complex_keywords = [
                    "litige", "contestation", "problème", "exception", "spécial",
                    "document", "technique", "multiple", "facturation", "erreur",
                    "refus", "rejet", "dispute", "arbitrage", "médiation",
                    "conteste", "injuste", "plainte", "désaccord", "recours", "injustice"
                ]
                s_count = sum(1 for w in simple_keywords if w in analysis.lower())
                c_count = sum(1 for w in complex_keywords if w in analysis.lower())

                if s_count > c_count:
                    is_simple_claim = True
                elif c_count > s_count:
                    is_complex_claim = True
                else:
                    is_simple_claim = True  # défaut

            # Garde-fou: si “complexe” mais on peut calculer depuis DB (montants/ticket/délais)
            if (is_complex_claim and is_amount_like and can_compute_tm and has_amount_cols and not is_confirm_intent):
                is_complex_claim = False
                is_simple_claim = True

            # Raccourcis métier supplémentaires
            status_terms = [
                "statut", "status", "suivi", "où en est", "ou en est",
                "verifier le statut", "vérifier le statut", "je veux verifier", "je veux vérifier",
            ]
            if ("reclamation" in q_lower or "réclamation" in q_lower or "reclamations" in q_lower or "réclamations" in q_lower) \
               and any(t in q_lower for t in status_terms):
                is_simple_claim = True
                is_complex_claim = False

            family_terms = [
                "femme", "épouse", "epouse", "époux", "epoux", "enfant", "enfants",
                "fille", "fils", "famille", "ayant droit", "bénéficiaire", "beneficiaire",
                "conjoint", "conjointe", "mari"
            ]
            data_terms = [
                "remboursement", "rembours", "dossier", "statut", "montant", "paiement", "prise en charge"
            ]
            mentions_family = any(t in q_lower for t in family_terms)
            mentions_data = any(t in q_lower for t in data_terms)
            is_follow_up = bool(new_state.get("is_follow_up", False))

            if mentions_family and mentions_data:
                is_simple_claim = True
                is_complex_claim = False
            if mentions_family and not mentions_data and is_follow_up:
                is_simple_claim = True
                is_complex_claim = False

            # --- Détection documents requis (sans forcer complexe si DB peut répondre) ---
            original_q_for_docs = new_state.get("question", "") or ""
            doc_req = self._detect_doc_requirements(original_q_for_docs, analysis)

            # Stocker l'info
            new_state["claims"]["needs_documents"] = bool(doc_req.get("needs_documents"))
            new_state["claims"]["required_docs"] = doc_req.get("required_docs", [])
            new_state["claims"]["required_fields"] = doc_req.get("required_fields", [])
            new_state["claims"]["doc_reason"] = doc_req.get("reason", "")

            if doc_req.get("needs_documents") and not (is_amount_like and can_compute_tm and has_amount_cols):
                # Réel besoin de pièces : force complexe
                is_complex_claim = True
                is_simple_claim = False

            # Déterminer flags finaux
            if is_complex_claim:
                claim_type = "complexe"
                needs_human = True
                needs_database = False
            else:
                claim_type = "simple"
                needs_human = False
                needs_database = True  # simple => DB

            # Mettre à jour l'état
            new_state["claims"]["needs_human"] = needs_human
            new_state["claims"]["claim_type"] = claim_type
            new_state["claims"]["is_simple_claim"] = is_simple_claim
            new_state["claims"]["is_complex_claim"] = is_complex_claim
            previous_needs_database = bool(new_state.get("needs_database", False))
            new_state["needs_database"] = bool(needs_database or previous_needs_database)

            # --- Personnalisation destinataire ---
            adherent_name = new_state.get('adherent_name', None)
            medecin_name = new_state.get('medecin_name', None)
            adherent_id = new_state.get('adherent_id', None)
            medecin_id = new_state.get('medecin_id', None)

            if medecin_id:
                destinataire = f"Docteur {medecin_name or medecin_id}"
                destinataire_id = f"ID Médecin : {medecin_id}"
            elif adherent_id:
                destinataire = f"Cher(e) {adherent_name or adherent_id}"
                destinataire_id = f"ID Adhérent : {adherent_id}"
            else:
                destinataire = "Utilisateur"
                destinataire_id = "ID inconnu"

            # --- Réponses ---
            if needs_human:
                new_state["claims"]["response"] = f"""
{destinataire},

Votre réclamation nécessite une attention particulière de notre part. 

Ce qui va se passer :
• Un de nos agents spécialisés va examiner votre dossier en détail
• Il vous contactera dans les 24-48h pour discuter de votre situation
• Il vous proposera une solution adaptée à votre cas

En attendant, n'hésitez pas si vous avez d'autres questions sur vos dossiers !
"""
                # Notification admin (MailHog)
                try:
                    user_id = new_state.get("adherent_id") or new_state.get("medecin_id") or "inconnu"
                    user_name = new_state.get("adherent_name") or new_state.get("medecin_name") or "inconnu"
                    question = new_state.get("question", "")
                    summary = new_state.get("summary", "")

                    subject = "[Isanté] Réclamation complexe - intervention humaine requise"
                    body = (
                        "Une réclamation complexe nécessite l'intervention d'un administrateur.\n\n"
                        "Détails de la demande :\n"
                        f"- ID utilisateur: {user_id}\n"
                        f"- Nom: {user_name}\n"
                        f"- Question: {question}\n\n"
                        f"Résumé de la conversation: {summary}\n\n"
                        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )

                    import os
                    admin_emails = os.getenv("ADMIN_EMAILS", "admin@isante.tn,support@isante.tn").split(",")
                    admin_emails = [email.strip() for email in admin_emails if email.strip()]

                    email_sent = send_support_email_mailhog(
                        subject=subject,
                        body=body,
                        to_emails=admin_emails
                    )
                    if email_sent:
                        print(f"[SUCCESS] Notification admin envoyée via MailHog à {admin_emails}")
                    else:
                        print("[ERROR] Envoi notification admin via MailHog a échoué")

                except Exception as email_error:
                    print(f"[ERROR] Erreur lors de l'envoi de la notification admin: {str(email_error)}")

            else:
                new_state["claims"]["response"] = f"""
{destinataire},

Parfait ! Votre demande peut être traitée automatiquement.

**Je vais maintenant :**
• Vérifier vos informations dans notre base de données
• Analyser le dossier (montants, ticket modérateur, délais…)
• Vous donner une réponse précise et complète

**Type de réclamation :** {claim_type}
**Traitement :** Automatique

Je consulte vos données pour vous répondre...
"""

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Erreur lors du traitement de la réclamation : {str(e)}"
            print(f"[ERROR ClaimsAgent] {error_msg} (after {processing_time:.2f}s)")

            new_state["claims"] = new_state.get("claims", {})
            new_state["claims"]["error"] = error_msg
            new_state["claims"]["processing_time"] = processing_time

            new_state["claims"]["response"] = f"""
Je suis désolé, une erreur technique s'est produite lors de l'analyse de votre réclamation.

**Que faire :**
• Veuillez réessayer dans quelques instants
• Si le problème persiste, contactez notre support technique
• Votre demande a été enregistrée et sera traitée

**Détails techniques :** Erreur de traitement (durée: {processing_time:.2f}s)
"""
        return new_state

    def run(self, state: AgentState) -> AgentState:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.arun(state))
        except Exception as e:
            print(f"Erreur dans ClaimsAgent.run : {str(e)}")
            raise

    def __call__(self, state: AgentState, config: RunnableConfig = None) -> AgentState:
        return self.run(state)

    def invoke(self, input: Union[Dict[str, Any], AgentState], config: Optional[RunnableConfig] = None) -> AgentState:
        if isinstance(input, dict):
            state = AgentState(**input)
        else:
            state = input
        if should_summarize(state):
            state = update_state_with_summary(state, "claims")
        try:
            result = self.run(state)
        except Exception as e:
            error_msg = f"Erreur dans ClaimsAgent.invoke : {str(e)}"
            state["claims"] = state.get("claims", {})
            state["claims"]["error"] = error_msg
            state["claims"]["response"] = error_msg
            result = state
        return result
