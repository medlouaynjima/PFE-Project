from trustcall import create_extractor
import os
import time
from langchain_core.messages import SystemMessage
from langchain_core.runnables.config import RunnableConfig
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.store.base import BaseStore
import json
from typing import Dict, Any

from src.core.Configuration import Configuration
from src.agents.agentstage import AgentState
from src.models.adherent_memory import AdherentProfile
from src.models.medecin_memory import MedecinProfile

# Initialize the LLM - use the same model as your workflow
def get_model():
    return ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# Create the extractor for adherent profiles
def get_adherent_extractor():
    return create_extractor(
        get_model(),
    tools=[AdherentProfile],
        tool_choice="AdherentProfile"  # Enforces use of the AdherentProfile tool
)

# Create the extractor for medecin profiles
def get_medecin_extractor():
    return create_extractor(
        get_model(),
    tools=[MedecinProfile],
        tool_choice="MedecinProfile"  # Enforces use of the MedecinProfile tool
)

# Note: trustcall's create_extractor automatically handles JSON-Patch operations
# when an existing profile is provided. No separate patcher needed.



# Instructions pour l'extraction de la mémoire
EXTRACT_INSTRUCTION = """Extract ONLY factual information about the adherent/medecin from the conversation. 

VERY IMPORTANT: 
1. ONLY extract information that was EXPLICITLY mentioned in the conversation
2. NEVER make up or infer information that wasn't directly stated
3. NEVER add any FAQs unless the user explicitly asked a question multiple times
4. If a field doesn't have information from the conversation, leave it empty or use the existing value
5. For frequent_asked_questions, only include questions the user actually asked more than once

Focus on extracting:
- Personal information (name, ID, family members)
- Medical history and active cases
- Past claims and reimbursements
- Frequently asked questions
- Preferences and special needs
- Recent interactions and questions"""


def format_adherent_memory(memory_dict):
    """Format the adherent memory for inclusion in prompts (health/insurance assistant style)."""
    if not memory_dict:
        return "No previous information about this adherent."

    # Format past_reclamations
    reclamations_str = ""
    if memory_dict.get("past_reclamations"):
        reclamations_str = "\n".join([
            f"- {reclamation.get('date', 'Unknown date')}: {reclamation.get('description', 'Unknown issue')}" 
            for reclamation in memory_dict.get("past_reclamations", [])
        ])

    # Format FAQs
    faqs_str = ""
    if memory_dict.get("frequent_asked_questions"):
        faqs_str = "\n".join([
            f"- Q: {faq.get('question', 'N/A')} (asked {faq.get('frequency', 1)} times)"
            for faq in memory_dict.get("frequent_asked_questions", [])
        ])


    # Compile the formatted memory
    formatted_memory = f"""Adhérent: {memory_dict.get('adherent_name', 'Inconnu')}
ID: {memory_dict.get('adherent_id', 'Inconnu')}
"""

    if reclamations_str:
        formatted_memory += f"\nRéclamations passées:\n{reclamations_str}\n"

    if faqs_str:
        formatted_memory += f"\nQuestions fréquentes:\n{faqs_str}\n"

    if memory_dict.get("preferences"):
        formatted_memory += f"\nPreferences: {', '.join(memory_dict.get('preferences', []))}\n"
    
    if memory_dict.get("notes"):
        formatted_memory += f"\nNotes: {memory_dict.get('notes', '')}\n"

    return formatted_memory

def format_medecin_memory(memory_dict):
    """Format the medecin memory for inclusion in prompts."""
    if not memory_dict:
        return "No previous information about this doctor."
    
    # Format past_reclamations
    reclamations_str = ""
    if memory_dict.get("past_reclamations"):
        reclamations_str = "\n".join([
            f"- {reclamation.get('date', 'Unknown date')}: {reclamation.get('description', 'Unknown issue')}" 
            for reclamation in memory_dict.get("past_reclamations", [])
        ])
    
    # Format FAQs as a string
    faqs_str = ""
    if memory_dict.get("frequent_asked_questions"):
        faqs_str = "\n".join([
            f"- Q: {faq.get('question', 'N/A')} (asked {faq.get('frequency', 1)} times)" 
            for faq in memory_dict.get("frequent_asked_questions", [])
        ])
    
    # Compile the formatted memory
    formatted_memory = f"""Médecin: {memory_dict.get('nom', 'Inconnu')}
ID: {memory_dict.get('medecin_id', 'Inconnu')}
"""

    if reclamations_str:
        formatted_memory += f"\nPatients en charge:\n{reclamations_str}\n"
    
    if faqs_str:
        formatted_memory += f"\nFrequently Asked Questions:\n{faqs_str}\n"
    
    if memory_dict.get("preferences"):
        formatted_memory += f"\nPreferences: {', '.join(memory_dict.get('preferences', []))}\n"
    
    if memory_dict.get("notes"):
        formatted_memory += f"\nNotes: {memory_dict.get('notes', '')}\n"
    
    return formatted_memory

def load_profile_memory(state: AgentState, config: RunnableConfig, store: BaseStore = None) -> AgentState:
    """Load adherent or doctor memory from the store and add it to the state."""
    if store is None:
        # Si pas de store, retourner l'état sans mémoire
        new_state = state.copy()
        new_state["profile_memory"] = "Aucune information précédente disponible."
        new_state["profile_memory_dict"] = {}
        return new_state
    
    configurable = Configuration.from_runnable_config(config)
    adherent_id = state.get("adherent_id") or configurable.adherent_id
    medecin_id = state.get("medecin_id") or configurable.medecin_id
    
    if adherent_id:
        # Ensure adherent_id is a string for the namespace
        adherent_id_str = str(adherent_id)
        namespace = ("adherent_memory", adherent_id_str)
        key = "adherent_profile"
        formatter = format_adherent_memory
    elif medecin_id:
        # Ensure medecin_id is a string for the namespace
        medecin_id_str = str(medecin_id)
        namespace = ("medecin_memory", medecin_id_str)
        key = "medecin_profile"
        formatter = format_medecin_memory
    else:
        return state
    
    # TTL helpers
    def _ttl_seconds() -> int:
        try:
            return int(os.getenv("PROFILE_TTL_SECONDS", "604800"))  # 7 days default
        except Exception:
            return 604800
    def _now() -> float:
        return time.time()

    meta_key = f"{key}_meta"
    vec_key = "profile_vectors"

    # Retrieve memory and meta from the store
    existing_memory = store.get(namespace, key)
    meta = store.get(namespace, meta_key)

    # Check expiration
    is_expired = False
    try:
        if meta and meta.value and isinstance(meta.value, dict):
            expires_at = meta.value.get("expires_at")
            if isinstance(expires_at, (int, float)) and expires_at < _now():
                is_expired = True
    except Exception:
        is_expired = False

    if is_expired:
        # Invalidate profile and vectors on expiry
        store.put(namespace, key, {})
        store.put(namespace, vec_key, {"texts": [], "vectors": []})
        existing_memory = None
    
    # If memory exists, format it and add to state
    if existing_memory and existing_memory.value:
        memory_dict = existing_memory.value
        formatted_memory = formatter(memory_dict)
        print(f"[DEBUG MEMORY] Loaded existing profile for {adherent_id or medecin_id}")
    else:
        memory_dict = {}
        formatted_memory = formatter({})
        print(f"[DEBUG MEMORY] No existing profile found for {adherent_id or medecin_id}")
    
    # Add memory to state
    new_state = state.copy()
    if adherent_id:
        new_state["adherent_profile"] = memory_dict
    elif medecin_id:
        new_state["medecin_profile"] = memory_dict
    
    new_state["profile_memory"] = formatted_memory
    new_state["profile_memory_dict"] = memory_dict

    # Bump TTL for active user
    try:
        store.put(namespace, meta_key, {
            "last_access": _now(),
            "expires_at": _now() + _ttl_seconds()
        })
    except Exception as e:
        print(f"[DEBUG MEMORY] TTL bump failed: {e}")

    # --- Optional embeddings + retrieval on profile memory (for better recall) ---
    try:
        question_text = (state.get("question") or "").strip()
        if question_text and store is not None and (adherent_id or medecin_id):
            embeddings = OpenAIEmbeddings()
            # Build namespace/keys
            ns = namespace
            # Fetch vectors cache
            cached = store.get(ns, vec_key)
            texts: list[str] = []
            vectors: list[list[float]] = []
            if cached and cached.value:
                texts = cached.value.get("texts", [])
                vectors = cached.value.get("vectors", [])
            else:
                # Build chunks from memory_dict for embedding
                chunks: list[str] = []
                def add(k,v):
                    if isinstance(v, (str, int, float)) and str(v).strip():
                        chunks.append(f"{k}: {v}")
                    elif isinstance(v, list):
                        for idx,item in enumerate(v):
                            if isinstance(item, (str, int, float)) and str(item).strip():
                                chunks.append(f"{k}[{idx}]: {item}")
                            elif isinstance(item, dict):
                                for sk, sv in item.items():
                                    if str(sv).strip():
                                        chunks.append(f"{k}.{sk}: {sv}")
                    elif isinstance(v, dict):
                        for sk, sv in v.items():
                            if str(sv).strip():
                                chunks.append(f"{k}.{sk}: {sv}")
                for key, val in (memory_dict or {}).items():
                    add(key, val)
                if not chunks and formatted_memory:
                    chunks = [formatted_memory]
                texts = chunks[:100]
                if texts:
                    vectors = embeddings.embed_documents(texts)
                    store.put(ns, vec_key, {"texts": texts, "vectors": vectors})
            # Do retrieval if we have vectors
            if texts and vectors:
                import math
                def cosine(a,b):
                    num = sum(x*y for x,y in zip(a,b))
                    da = math.sqrt(sum(x*x for x in a))
                    db = math.sqrt(sum(y*y for y in b))
                    return (num/(da*db)) if da>0 and db>0 else 0.0
                q_vec = embeddings.embed_query(question_text)
                scored = [(cosine(q_vec, v), t) for v,t in zip(vectors, texts)]
                scored.sort(key=lambda x: x[0], reverse=True)
                top_texts = [t for _,t in scored[:3]]
                new_state["profile_retrieval"] = top_texts
    except Exception as e:
        # Fail open: retrieval is optional
        print(f"[DEBUG MEMORY] Retrieval skipped due to error: {e}")
    
    return new_state

def update_profile_memory(state: AgentState, config: RunnableConfig, store: BaseStore = None):
    """
    Extract and update either adherent or medecin memory profile from the conversation.
    Uses JSON-Patch operations for atomic updates.
    """
    if store is None:
        # Si pas de store, retourner l'état sans mise à jour
        return state

    new_state = state.copy()

    # Determine role and user ID
    configurable = Configuration.from_runnable_config(config)
    adherent_id = state.get("adherent_id") or configurable.adherent_id
    medecin_id = state.get("medecin_id") or configurable.medecin_id

    role = "adherent" if adherent_id else "medecin"
    user_id = str(adherent_id or medecin_id or "unknown")

    # Set up namespace and memory key
    namespace = (f"{role}_memory", user_id)
    memory_key = f"{role}_profile"
    existing = store.get(namespace, memory_key)

    # Get existing profile or create empty one
    existing_profile = existing.value if existing else {}

    # Gather all conversation messages
    all_messages = []
    if "messages" in state:
        all_messages.extend(state["messages"])
    for agent_key in ["conversational", "database", "claims", "final_answer"]:
        if agent_key in state and "messages" in state[agent_key]:
            all_messages.extend(state[agent_key]["messages"])

    # Set up extraction instructions
    system_messages = [
        SystemMessage(content=EXTRACT_INSTRUCTION),
        SystemMessage(content="IMPORTANT: DO NOT MAKE UP ANY INFORMATION. Only extract what was explicitly mentioned.")
    ]

    # Choose extractor (trustcall handles JSON-Patch automatically when existing profile provided)
    extractor = get_adherent_extractor() if role == "adherent" else get_medecin_extractor()
    
    try:
        # Use trustcall extractor - it automatically handles JSON-Patch operations
        # when an existing profile is provided
        result = extractor.invoke({
            "messages": system_messages + all_messages,
            "existing": {f"{role.capitalize()}Profile": existing_profile} if existing_profile else None
        })

        if result.get("responses") and len(result["responses"]) > 0:
            updated_profile = result["responses"][0].model_dump()
            if existing_profile:
                print(f"[DEBUG MEMORY] Applied JSON-Patch to {role} profile")
            else:
                print(f"[DEBUG MEMORY] Created new {role} profile")
        else:
            updated_profile = existing_profile
            print(f"[DEBUG MEMORY] No updates needed for {role} profile")

    except Exception as e:
        print(f"[DEBUG MEMORY] Error updating {role} profile: {e}")
        # Fallback to existing profile
        updated_profile = existing_profile

    # Save updated profile atomically
    if updated_profile:
        store.put(namespace, memory_key, updated_profile)
        print(f"[DEBUG MEMORY] Successfully saved {role} profile to store")

    # Refresh TTL metadata on update
    try:
        def _ttl_seconds() -> int:
            try:
                return int(os.getenv("PROFILE_TTL_SECONDS", "604800"))
            except Exception:
                return 604800
        def _now() -> float:
            return time.time()
        meta_key = f"{memory_key}_meta"
        store.put(namespace, meta_key, {
            "last_access": _now(),
            "expires_at": _now() + _ttl_seconds()
        })
        print(f"[DEBUG MEMORY] TTL refreshed for {role} profile")
    except Exception as e:
        print(f"[DEBUG MEMORY] TTL refresh skipped due to error: {e}")

    # Refresh embeddings immediately after saving the updated profile
    try:
        if store is not None and updated_profile:
            embeddings = OpenAIEmbeddings()
            ns = namespace
            vec_key = "profile_vectors"

            # Build chunks from the updated profile for embedding
            chunks: list[str] = []
            def add_chunk(key: str, value):
                if isinstance(value, (str, int, float)) and str(value).strip():
                    chunks.append(f"{key}: {value}")
                elif isinstance(value, list):
                    for idx, item in enumerate(value):
                        if isinstance(item, (str, int, float)) and str(item).strip():
                            chunks.append(f"{key}[{idx}]: {item}")
                        elif isinstance(item, dict):
                            for sub_key, sub_val in item.items():
                                if str(sub_val).strip():
                                    chunks.append(f"{key}.{sub_key}: {sub_val}")
                elif isinstance(value, dict):
                    for sub_key, sub_val in value.items():
                        if str(sub_val).strip():
                            chunks.append(f"{key}.{sub_key}: {sub_val}")

            for k, v in (updated_profile or {}).items():
                add_chunk(k, v)

            if not chunks:
                # Fallback to formatted text if no granular chunks
                fallback_text = format_adherent_memory(updated_profile) if role == "adherent" else format_medecin_memory(updated_profile)
                if fallback_text:
                    chunks = [fallback_text]

            texts = chunks[:100]
            vectors: list[list[float]] = []
            if texts:
                vectors = embeddings.embed_documents(texts)
            store.put(ns, vec_key, {"texts": texts, "vectors": vectors})
            print(f"[DEBUG MEMORY] Refreshed embeddings for {role} profile with {len(texts)} chunks")
    except Exception as e:
        print(f"[DEBUG MEMORY] Embedding refresh skipped due to error: {e}")

    # Format memory for prompts
    if role == "adherent":
        formatted_memory = format_adherent_memory(updated_profile) if updated_profile else "No profile data found."
    else:
        formatted_memory = format_medecin_memory(updated_profile) if updated_profile else "No profile data found."

    # Update state
    new_state[f"{role}_memory"] = formatted_memory
    new_state[f"{role}_memory_dict"] = updated_profile if updated_profile else {}

    return new_state