from typing import List, Dict, Any, Optional, Annotated, Union
from typing_extensions import NotRequired, TypedDict
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
import re

# Custom reducer that appends, drops small-talk, and trims to last 6 exchanges (12 msgs)
SMALL_TALK_PATTERNS = [
    r"^\s*(bonjour|salut|hello|hi)\s*!*\s*$",
    r"^\s*(merci|thanks|thank\s+you)\s*!*\s*$",
    r"^\s*(ok|d'accord|bien|parfait|super)\.?\s*$",
    r"^\s*(au\s+revoir|bye|goodbye)\s*!*\s*$",
]
_SMALL_TALK_RE = re.compile("|".join(SMALL_TALK_PATTERNS), re.IGNORECASE)

def compact_messages(existing, new):
    """Reducer used for all `messages` fields:
    - append new messages via LangGraph's add_messages
    - drop trivial small-talk
    - keep only last 12 messages (~6 user/assistant exchanges)
    """
    merged = add_messages(existing, new) or []
    cleaned = []
    for msg in merged:
        try:
            content = msg.content if hasattr(msg, "content") else ""
            if isinstance(content, str) and _SMALL_TALK_RE.match(content.strip()):
                continue
        except Exception:
            pass
        cleaned.append(msg)
    # Trim to last 12 messages to approximate 6 exchanges
    if len(cleaned) > 12:
        cleaned = cleaned[-12:]
    return cleaned

class ConversationalAgentState(TypedDict):
    """État pour l'agent conversationnel (classification, routage, chitchat)"""
    messages: Annotated[List[AnyMessage], compact_messages]
    response: str
    error: NotRequired[str]
    needs_claims: NotRequired[bool]
    needs_database: NotRequired[bool]
    claim_type: NotRequired[str]

class ClaimsAgentState(TypedDict):
    """État pour l'agent de traitement des réclamations"""
    messages: Annotated[List[AnyMessage], compact_messages]
    response: str
    claim_id: NotRequired[str]
    claim_status: NotRequired[str]
    claim_type: NotRequired[str]
    needs_human: NotRequired[bool]
    adherent_id: NotRequired[str]
    medecin_id: NotRequired[str]
    error: NotRequired[str]

class DatabaseAgentState(TypedDict):
    """State for the database agent that converts natural language to SQL queries"""
    messages: Annotated[List[AnyMessage], compact_messages]  # Conversation messages with reducer
    question: str                   # Original question from the user
    response: str                   # Response from the agent
    sql_query: str                  # Generated SQL query
    query_result: str               # Result of the SQL query execution
    query_rows: List[Dict]          # Query results as a list of dictionaries
    table_schemas: Dict             # Schema information for relevant tables
    error: NotRequired[str]         # Any error that occurred during processing
    reasoning: NotRequired[str]     # Agent's reasoning about the query
    _query_history: List[str]       # Internal tracking of previous queries


class FinalAnswerAgentState(TypedDict):
    """État pour l'agent de réponse finale qui formate les résultats pour l'adhérent/médecin"""
    messages: Annotated[List[AnyMessage], compact_messages]  # Conversation messages with reducer
    response: str                   # Réponse formulée pour l'adhérent/médecin
    adherent_name: NotRequired[str] # The adherent's name for personalization
    error: NotRequired[str]         # Any error that occurred during processing

class AgentState(MessagesState):
    """État global partagé pour tout le workflow santé/assurance"""
    # Infos utilisateur
    question: str
    response: str
    summary: NotRequired[str]
    adherent_id: NotRequired[str]
    medecin_id: NotRequired[str]
    adherent_name: NotRequired[str]
    medecin_name: NotRequired[str]
    role: NotRequired[str]
    adherent_memory: NotRequired[str]
    adherent_memory_dict: NotRequired[Dict]
    # Routage
    needs_claims: NotRequired[bool]
    needs_database: NotRequired[bool]
    # Résultats partagés
    query_rows: NotRequired[List[Dict]]
 
    # Détails réclamation
    claim_details: NotRequired[Dict]
    claim_file_path: NotRequired[str]
    # États spécifiques agents
    conversational: ConversationalAgentState
    claims: ClaimsAgentState
    database: DatabaseAgentState
    final_answer: FinalAnswerAgentState

