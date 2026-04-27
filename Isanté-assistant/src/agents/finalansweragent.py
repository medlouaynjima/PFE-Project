from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_core.runnables.config import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, FunctionMessage
from src.agents.agentstage import AgentState
from src.agents.utils.llm import llm
from src.agents.utils.postprocess import analyze_rows
import json
import time
import copy
import re
from datetime import datetime
from typing import Any, Optional, Dict, List, Union
from src.agents.utils.summarization import get_messages_with_summary, should_summarize, update_state_with_summary


def extract_period_from_sql(sql_query: str) -> str:
    """
    Extract time period information from SQL query for context-aware responses.
    Returns empty string if no period is found or if period is not relevant.
    """
    if not sql_query:
        return ""
    
    sql_lower = sql_query.lower()
    
    # Look for year patterns
    year_patterns = [
        r"year\([^)]+\)\s*=\s*(\d{4})",  # YEAR(date) = 2024
        r"like\s*['\"](\d{2})%['\"]",     # LIKE '24%' (for 2024)
        r"like\s*['\"](\d{4})%['\"]",     # LIKE '2024%'
        r"between\s*['\"](\d{4})",        # BETWEEN '2024-01-01'
        r"(\d{4})-\d{2}-\d{2}",           # 2024-01-01
    ]
    
    for pattern in year_patterns:
        import re
        match = re.search(pattern, sql_lower)
        if match:
            year = match.group(1)
            if len(year) == 2:  # Convert 24 to 2024
                year = f"20{year}"
            return f"en {year}"
    
    # Look for month patterns
    month_patterns = [
        r"month\([^)]+\)\s*=\s*(\d{1,2})",  # MONTH(date) = 12
        r"date_format\([^,]+,\s*['\"]%m['\"]\)\s*=\s*['\"](\d{2})['\"]",  # DATE_FORMAT(date, '%m') = '03'
    ]
    
    month_names = {
        '1': 'janvier', '2': 'février', '3': 'mars', '4': 'avril',
        '5': 'mai', '6': 'juin', '7': 'juillet', '8': 'août',
        '9': 'septembre', '10': 'octobre', '11': 'novembre', '12': 'décembre'
    }
    
    for pattern in month_patterns:
        match = re.search(pattern, sql_lower)
        if match:
            month_num = match.group(1)
            if month_num in month_names:
                return f"en {month_names[month_num]}"
    
    return ""


finalanswer_instructions = """Tu es un assistant virtuel expert, spécialisé dans la santé et l'assurance. 
Ta mission est de présenter les résultats d'une requête SQL de façon claire, naturelle, humaine et personnalisée, pour un adhérent ou un médecin.

Règles d'or :
- Utilise un ton naturel, chaleureux et conversationnel (comme un humain qui parle à un ami)
- Évite TOUJOURS les formulations robotiques comme "Voici le résultat de votre requête :" ou "Si vous avez d'autres questions, je suis là pour vous aider."
- Personnalise la réponse (nom, bénéficiaire, date, montant, etc.) dès que possible
- Ne donne jamais d'informations techniques (pas de SQL, pas de noms de colonnes, pas d'ID, pas de structure de table)
- Utilise des phrases courtes, simples, et va droit au but
- Si plusieurs éléments, tu peux utiliser des bullet points ou des phrases séparées
- Utilise au maximum 2 émojis pertinents (jamais plus)
- Si aucune donnée, explique-le de façon naturelle et propose d'aider
- Réponds directement à la question posée, comme un humain le ferait
- Utilise le "tu" ou "vous" selon le contexte, mais reste naturel
- Sois empathique et compréhensif

Exemples de réponses naturelles et humaines :

🔹 **Reste à payer**
> Votre dossier pour Lamia a été traité le 2 mars 2024. Il reste 150,25 DT à payer.

🔹 **Remboursement**
> Votre remboursement de 85,50 DT a été validé le 12 mai 2024.

🔹 **Statut de réclamation**
> Votre dernière réclamation concernant le dossier de votre fille a été résolue le 18 avril 2024. Le commentaire indique que votre dossier a été clôturé suite au remboursement.

🔹 **Aucune donnée**
> Je n'ai trouvé aucune information pour votre demande. Peux-tu reformuler ta question ?

🔹 **Question d'identité**
> Votre nom est Ines.

Contexte utilisateur : {adherent_name} ou {medecin_name}
Date : {timestamp}
Résumé de la conversation : "{summary}"
"""


class FinalAnswerAgent(Runnable):
    """Agent qui formate les résultats SQL en réponse claire pour l'utilisateur santé/assurance."""
    
    def __init__(self):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", finalanswer_instructions),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{question}")
        ])

    async def arun(self, state: AgentState) -> AgentState:
        new_state = copy.deepcopy(state)

        # Extract data from state (dict-safe access)
        question = state.get("question", "")

        db_block = {}
        try:
            db_block = state.get("database", {})
        except Exception:
            db_block = {}

        query_result = db_block.get("query_result", "")
        sql_query = db_block.get("sql_query", "")
        error = db_block.get("error", None)

        # Get query rows from various possible locations (prefer top-level, then database block)
        db_query_rows = []
        try:
            if state.get("query_rows"):
                db_query_rows = state.get("query_rows")
            elif db_block.get("query_rows"):
                db_query_rows = db_block.get("query_rows")
        except Exception:
            db_query_rows = []
        
        has_results = db_query_rows and len(db_query_rows) > 0
        
        # Extract user information
        adherent_name = state.get("adherent_name", "")
        medecin_name = state.get("medecin_name", "")
        adherent_id = state.get("adherent_id", "")
        medecin_id = state.get("medecin_id", "")
        
        # Try to get names from query results if not already set
        if not adherent_name and has_results:
            if "adherent_name" in db_query_rows[0]:
                adherent_name = db_query_rows[0]["adherent_name"]
        if not medecin_name and has_results:
            if "medecin_name" in db_query_rows[0]:
                medecin_name = db_query_rows[0]["medecin_name"]
        
        # Set user name
        user_name = adherent_name if adherent_name else medecin_name
        
        # Initialize final_answer state
        if not hasattr(new_state, "final_answer") or not new_state.get("final_answer"):
            new_state["final_answer"] = {
                "messages": [],
                "response": "",
                "adherent_name": user_name
            }
        else:
            new_state["final_answer"]["adherent_name"] = user_name
        
        response = ""
        
        try:
            # DEBUG: Log the data we're working with
            print(f"[DEBUG FINAL ANSWER] Question: {question}")
            print(f"[DEBUG FINAL ANSWER] Has results: {has_results}")
            print(f"[DEBUG FINAL ANSWER] Query rows count: {len(db_query_rows) if db_query_rows else 0}")
            if db_query_rows:
                print(f"[DEBUG FINAL ANSWER] First row: {db_query_rows[0]}")
            print(f"[DEBUG FINAL ANSWER] SQL query: {sql_query}")

            # Short-circuit for simple yes/no presence questions (confirmation d'enregistrement)
            question_lower = (question or "").lower()
            presence_markers = ["enregistr", "confirmation", "confirm", "reçu", "reception", "réception"]
            if has_results and any(m in question_lower for m in presence_markers):
                concise = "Oui, le dossier est bien enregistré."
                ai_message = AIMessage(content=concise)
                new_state["final_answer"]["messages"].append(ai_message)
                new_state["final_answer"]["response"] = concise
                new_state["response"] = concise
                return new_state
            
            # --- Post-SQL reasoning layer (automatic analysis) ---
            auto_analysis = {}
            try:
                auto_analysis = analyze_rows(question, db_query_rows or [])
            except Exception as _e:
                auto_analysis = {"insights": [], "facts": {}, "summary": "Analyse automatique indisponible."}

            # We'll surface this non-technically in the context for the LLM to use
            analysis_summary = auto_analysis.get("summary", "")
            analysis_insights = auto_analysis.get("insights", [])

            # Additional targeted analysis: ticket modérateur + reste à payer ⇒ base et remboursé estimés
            def _to_float(x):
                try:
                    return float(x)
                except Exception:
                    return None

            analysis_notes: List[str] = []
            if db_query_rows:
                try:
                    row0 = db_query_rows[0] or {}
                    tm = _to_float(row0.get("ticket_moderateur"))
                    reste = _to_float(row0.get("reste_a_payer"))
                    if tm is not None and reste is not None:
                        tm_rate = tm / 100.0 if tm > 1.0 else tm
                        if tm_rate and tm_rate > 0:
                            base_estimee = reste / tm_rate
                            remb_estime = base_estimee - reste
                            analysis_notes.append(
                                f"Ticket modérateur {round(tm_rate*100,2)}% ⇒ base estimée ≈ {base_estimee:.2f} DT, reste à payer {reste:.2f} DT, remboursé ≈ {remb_estime:.2f} DT."
                            )
                except Exception:
                    pass

            # Prepare context message
            messages = get_messages_with_summary(new_state, "final_answer")
            
            # Extract period from SQL query for context
            extracted_period = extract_period_from_sql(sql_query)
            
            # Prepare natural context instead of technical one
            context = f"Question de l'utilisateur : {question}\n"
            
            # Add period context if found
            if extracted_period:
                context += f"Période concernée : {extracted_period}\n"
            
            if has_results:
                # Format data in a more natural way
                context += f"\nInformations trouvées ({len(db_query_rows)} résultat(s)) :\n"
                for i, row in enumerate(db_query_rows, 1):
                    context += f"\nRésultat {i} :\n"
                    
                    # Special handling for delay reasons (motif_retard)
                    if "motif_retard" in row and row.get("motif_retard"):
                        context += f"Justification du retard : {row['motif_retard']}\n"
                    
                    # Filtrer les identifiants techniques (ne pas exposer au user)
                    id_like_keys = {
                        "dossier_id", "remboursement_id", "reclamation_id", "reclamationresolu_id",
                        "medecin_id", "adherent_id", "agent_id", "num_dossier", "id", "num_transaction"
                    }
                    for key, value in row.items():
                        if value is not None:
                            if key in id_like_keys or key.endswith("_id"):
                                continue
                            # Clean up column names for better readability
                            clean_key = key.replace('_', ' ').title()
                            context += f"  {clean_key} : {value}\n"
                
                # Handle NULL values naturally
                if len(db_query_rows) == 1 and any(val is None for val in db_query_rows[0].values()):
                    null_count = sum(1 for val in db_query_rows[0].values() if val is None)
                    total_count = len(db_query_rows[0])
                    if null_count == total_count:
                        context += f"\nAucune information disponible {extracted_period if extracted_period else 'pour cette période'}.\n"
                    else:
                        available_fields = [key.replace('_', ' ').title() for key, val in db_query_rows[0].items() if val is not None]
                        context += f"\nInformations disponibles : {', '.join(available_fields)}\n"
            else:
                context += f"\nAucune information trouvée."
                if extracted_period:
                    context += f" Aucun résultat pour {extracted_period}."
            
            # Append automatic analysis to context if available
            if analysis_summary:
                context += f"\nAnalyse automatique (post-traitement) : {analysis_summary}\n"
                if analysis_insights:
                    for m in analysis_insights[:6]:
                        context += f"  • {m}\n"

            if error:
                context += f"\n\nErreur technique : {error}"
            
            # Add visualization information if available
            has_visualization = state.get("has_visualization", False)
            visualization_paths = state.get("visualization_paths", [])
            if has_visualization and visualization_paths:
                context += f"\nVisualisations disponibles : {', '.join(visualization_paths)}\n"
            
            # Add context message
            context_message = FunctionMessage(
                name="database_results",
                content=context
            )
            new_state["final_answer"]["messages"].append(context_message)
            
            # Prepare prompt
            messages = get_messages_with_summary(new_state, "final_answer")
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Determine user type and prepare instructions
            if medecin_id and medecin_name:
                user_type = "médecin"
                prompt_instructions = finalanswer_instructions.replace(
                    "{adherent_name}",
                    "{medecin_name}"
                ).replace(
                    "- Nom de l'adhérent : {adherent_name}",
                    "- Nom du médecin : {medecin_name}"
                ).replace(
                    "- Vous vous adressez directement à l'adhérent",
                    "- Vous vous adressez directement au médecin"
                ).replace(
                    "- Toujours utiliser le nom de l'adhérent, jamais son identifiant",
                    "- Toujours utiliser le nom du médecin, jamais son identifiant"
                )
            else:
                user_type = "adherent"
                prompt_instructions = finalanswer_instructions
            
            # Format instructions with correct variable
            formatted_instructions = prompt_instructions.format(
                adherent_name=adherent_name or "",
                medecin_name=medecin_name or "",
                timestamp=current_time,
                summary=new_state.get("summary", "")
            )
            # Steer the tone to use automatic analysis insights when present
            formatted_instructions += "\nUtilise les éléments d'« Analyse automatique » si présents pour expliquer les écarts (délais, pourcentages, montants) en langage simple, sans détails techniques."
            
            # Instruction pour être concis et répondre seulement à ce qui est demandé
            formatted_instructions += "\nIMPORTANT: Réponds de manière concise et directe. Ne donne que l'information demandée. Si l'utilisateur demande juste 'est-ce qu'il y a un remboursement', réponds simplement oui/non avec les détails essentiels, pas tous les calculs techniques."
            
            # Special instruction for delay questions
            if any(keyword in question.lower() for keyword in ["délai", "retard", "pourquoi", "temps", "attente"]):
                formatted_instructions += "\nIMPORTANT: Si une 'Justification du retard' est fournie dans les données, utilise-la pour expliquer pourquoi le délai est plus long que prévu. Cette information est cruciale pour répondre aux questions sur les délais."
            
            # Create prompt and get response
            prompt = ChatPromptTemplate.from_messages([
                ("system", formatted_instructions),
                MessagesPlaceholder(variable_name="messages"),
                ("human", "Réponds de manière simple et directe à la question. Ne donne que l'information demandée, sans détails techniques inutiles. Sois concis et naturel.")
            ])
            
            response_message = await self.llm.ainvoke(
                prompt.format_messages(
                    messages=messages,
                    question=question
                )
            )
            
            raw_response = response_message.content if hasattr(response_message, "content") else str(response_message)

            # Post-traitement: supprimer toute fuite d'identifiants techniques dans la réponse finale
            def _sanitize_ids(text: str) -> str:
                import re as _re
                patterns = [
                    r"\b(dossier\s*(num(é|e)ro)?\s*)\d+\b",
                    r"\b(id|identifiant)\s*[:#]?\s*\d+\b",
                    r"\b(reclamation|remboursement|transaction)\s*id\s*\d+\b",
                ]
                cleaned = text
                for p in patterns:
                    cleaned = _re.sub(p, "", cleaned, flags=_re.IGNORECASE)
                return cleaned

            response = _sanitize_ids(raw_response)
            
            # Add response to state
            ai_message = AIMessage(content=response)
            new_state["final_answer"]["messages"].append(ai_message)
            new_state["final_answer"]["response"] = response
            new_state["response"] = response
            
        except Exception as e:
            # Professional error response without exposing technical details
            error_msg = (
                "Je rencontre actuellement un problème pour accéder à vos informations. "
                "Veuillez réessayer plus tard ou contacter le support si le problème persiste."
            )
            error_message = FunctionMessage(
                name="final_answer_error",
                content=str(e)  # Log technical error but don't show to user
            )
            new_state["final_answer"]["messages"].append(error_message)
            new_state["final_answer"]["error"] = str(e)
            new_state["response"] = error_msg
            
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
            print(f"Erreur dans FinalAnswerAgent.run : {str(e)}")
            raise

    def __call__(self, state: AgentState, config: RunnableConfig = None) -> AgentState:
        return self.run(state)

    def invoke(self, input: Union[Dict[str, Any], AgentState], config: Optional[RunnableConfig] = None) -> AgentState:
        if isinstance(input, dict):
            state = AgentState(**input)
        else:
            state = input
            
        if should_summarize(state):
            state = update_state_with_summary(state, "final_answer")
            
        try:
            result = self.run(state)
        except Exception as e:
            # Professional error response without exposing technical details
            error_msg = (
                "Je rencontre actuellement un problème pour accéder à vos informations. "
                "Veuillez réessayer plus tard ou contacter le support si le problème persiste."
            )
            state["final_answer"] = state.get("final_answer", {})
            state["final_answer"]["error"] = str(e)
            state["response"] = error_msg
            result = state
            
        return result 