from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.store.base import BaseStore
from langchain_core.runnables.config import RunnableConfig
from src.agents.agentstage import AgentState
from src.agents.conversationalagent import ConversationalAgent
from src.agents.claimsagent import ClaimsAgent
from src.agents.databaseagent import DatabaseAgent
from src.agents.finalansweragent import FinalAnswerAgent
from src.core.memory_manager import load_profile_memory, update_profile_memory
from src.core.Configuration import Configuration

load_dotenv()

# Create instances of the agents
conversational_agent = ConversationalAgent()
claims_agent = ClaimsAgent()
database_agent = DatabaseAgent()
final_answer_agent = FinalAnswerAgent()

# Create the workflow
builder = StateGraph(AgentState, config_schema=Configuration)

# Add memory nodes
def load_memory_node(state: AgentState, config: RunnableConfig, store: BaseStore):
    print(f"[DEBUG WORKFLOW] load_memory_node called")
    actual_store = Configuration.get_store(config)  # ✅ unified
    print(f"[DEBUG WORKFLOW] Actual store from config: {type(actual_store)}")

    new_state = state.copy()
    original_question = new_state.get("question", "")
    try:
        result = load_profile_memory(new_state, config, actual_store)
    except Exception as e:
        print(f"[DEBUG WORKFLOW] load_profile_memory failed: {e}")
        result = new_state
    if original_question:
        result["question"] = original_question
    return result

def update_memory_node(state: AgentState, config: RunnableConfig, store: BaseStore):
    print(f"[DEBUG WORKFLOW] update_memory_node called")
    actual_store = Configuration.get_store(config)  # ✅ unified
    try:
        result = update_profile_memory(state, config, actual_store)
        return result
    except Exception as e:
        print(f"[DEBUG WORKFLOW] update_profile_memory failed: {e}")
        return state

# Process input node - handles text input
def process_input(state: AgentState, config: RunnableConfig = None, store: BaseStore = None) -> AgentState:
    """
    Process the input and ensure a fresh state for each conversation.
    """
    import time
    
    # Debug logging to understand what's in the state
    print(f"[process_input] Input state - question: '{state.get('question', '')}'")
    
    # Check if memory is already loaded
    if not state.get("profile_memory") and store is not None:
        print(f"[process_input] Memory not loaded, loading now...")
        state = load_profile_memory(state, config, store)
    
    # Create a fresh state, but preserve conversation history for follow-up detection
    fresh_state = AgentState(
        adherent_id=state.get("adherent_id", ""),
        medecin_id=state.get("medecin_id", ""),
        adherent_name=state.get("adherent_name", ""),
        medecin_name=state.get("medecin_name", ""),
        messages=state.get("messages", []),  # Preserve conversation history for follow-up detection
        response="",
        # Preserve summary across turns for reliable follow-up detection
        summary=state.get("summary", ""),
        adherent_memory=state.get("adherent_memory", ""),
        adherent_memory_dict=state.get("adherent_memory_dict", {}),
        # Preserve agent message history for proper summarization
        conversational=state.get("conversational", {"messages": []}),
        claims=state.get("claims", {"messages": []}),
        database=state.get("database", {"messages": []}),
        final_answer=state.get("final_answer", {"messages": []})
    )
    
    print("[process_input] Created fresh state, ensuring no state contamination")
    
    # Always start with an empty question to avoid stale questions persisting
    fresh_state["question"] = ""
    
    # Check for text input (non-empty question)
    has_text_input = state.get("question", "").strip() != ""
    
    if has_text_input:
        question = state.get("question", "")
        print(f"[process_input] Processing text input: '{question}'")
        fresh_state["question"] = question
        return fresh_state
    else:
        # No text input - use empty question
        print("[process_input] No input provided")
        fresh_state["question"] = ""
        
    return fresh_state

# Add nodes
builder.add_node("load_memory", load_memory_node)
builder.add_node("process_input", process_input)
builder.add_node("conversational_agent", conversational_agent)
builder.add_node("claims_agent", claims_agent)
builder.add_node("database_agent", database_agent)
builder.add_node("final_answer_agent", final_answer_agent)
builder.add_node("update_memory", update_memory_node)

# Add a summarization node
from src.agents.utils.summarization import update_state_with_summary

def summarize_conversations(state: AgentState):
    """Summarize the conversation before ending"""
    # DEBUG: Log the summary before processing
    print(f"[DEBUG WORKFLOW] summarize_conversations called with summary: '{state.get('summary', '')[:100] if state.get('summary') else 'EMPTY'}...'")
    
    # Start by summarizing the conversational agent interaction
    state = update_state_with_summary(state, "conversational")
    
    # If we used the claims agent, summarize that interaction too
    if state.get("needs_claims", False):
        state = update_state_with_summary(state, "claims")
        
        # IMPORTANT: Ensure claims response is propagated to final response
        claims_response = state.get("claims", {}).get("response", "")
        if claims_response and not state.get("response"):
            state["response"] = claims_response
            print(f"[DEBUG WORKFLOW] Propagated claims response to final response")
    
    # If we used the database, summarize that interaction too
    if state.get("needs_database", False):
        state = update_state_with_summary(state, "database")
            
        # Summarize the final answer if we went through the database route
        state = update_state_with_summary(state, "final_answer")
        
        # IMPORTANT: Ensure final answer response is propagated to final response
        final_response = state.get("final_answer", {}).get("response", "")
        if final_response and not state.get("response"):
            state["response"] = final_response
            print(f"[DEBUG WORKFLOW] Propagated final answer response to final response")
    
    # DEBUG: Log the summary after processing
    print(f"[DEBUG WORKFLOW] summarize_conversations finished with summary: '{state.get('summary', '')[:100] if state.get('summary') else 'EMPTY'}...'")
        
    return state

builder.add_node("summarize_conversation", summarize_conversations)




# Add router function to determine the next step after conversational agent
def route_from_conversational(state: AgentState) -> str:
    """Route based on whether the question needs claims processing or database processing"""
    if state.get("needs_claims", False):
        print("[ROUTER] Réclamation detected, routing to claims agent")
        return "claims_agent"
    else:
        print("[ROUTER] Question handled by conversational agent, skipping to summarization")
        return "summarize_conversation"

# Add router function for claims agent
def route_from_claims(state: AgentState) -> str:
    if state.get("claims", {}).get("needs_human", False):
        print("[ROUTER] Complex claim detected, routing to summarization for human intervention")
        return "summarize_conversation"
    elif state.get("needs_database", False):
        print("[ROUTER] Après claims, besoin de database, on route vers database_agent")
        return "database_agent"
    else:
        print("[ROUTER] Simple claim processed, routing to summarization")
        return "summarize_conversation"

# Add edges - load memory first, then process input, then conversational agent, followed by conditional routing
builder.add_edge(START, "load_memory")
builder.add_edge("load_memory", "process_input")
builder.add_edge("process_input", "conversational_agent")

# Add conditional routing based on whether the question needs claims or database processing
builder.add_conditional_edges(
    "conversational_agent",
    route_from_conversational,
    {
        "claims_agent": "claims_agent",
        "summarize_conversation": "summarize_conversation"
    }
)

# Add conditional routing for claims agent
builder.add_conditional_edges(
    "claims_agent",
    route_from_claims,
    {
        "database_agent": "database_agent",
        "summarize_conversation": "summarize_conversation"
    }
)

builder.add_edge("database_agent", "final_answer_agent")
builder.add_edge("final_answer_agent", "summarize_conversation")



# Update memory before ending
builder.add_edge("summarize_conversation", "update_memory")
builder.add_edge("update_memory", END)

# Helper function to initialize the state properly for all agents
def create_initial_state(question="", adherent_id="", medecin_id="", adherent_name="", medecin_name="", role=""):
    
    """Create an initial state for the workflow with proper structure for all agents"""
    # Create a basic state with the essential fields
    initial_state = AgentState(
        question=question,
        response="",
        adherent_id=adherent_id,
        medecin_id=medecin_id,
        adherent_name=adherent_name,
        medecin_name=medecin_name,
        role=role,
        messages=[],
        # Initialize adherent memory fields
        adherent_memory="",  # Formatted memory for prompts
        adherent_memory_dict={},  # Raw memory dictionary
        # Initialize agent-specific state dictionaries with empty message lists
        conversational={"messages": []},
        claims={"messages": []},
        database={"messages": []},
        final_answer={"messages": []}
    )
        
    return initial_state

# Use Redis checkpointer if available, otherwise fallback to MemorySaver
import os

def _build_checkpointer():
    redis_url = os.getenv("REDIS_URL", "")
    if redis_url:
        try:
            from langgraph.checkpoint.redis import RedisSaver
            return RedisSaver.from_url(redis_url)
        except ImportError:
            print("[WARN] RedisSaver not available in this LangGraph version")
        except Exception as e:
            print(f"[WARN] Redis unavailable ({e})")
    
    from langgraph.checkpoint.memory import MemorySaver
    return MemorySaver()

graph = builder.compile(checkpointer=_build_checkpointer())

# View and save the graph
try:
    image_data = graph.get_graph(xray=True).draw_mermaid_png()
    with open("graph_image.png", "wb") as file:
        file.write(image_data)
    print("Updated graph visualization saved to 'graph_image.png'")
except Exception as viz_error:
    print(f"Warning: Could not generate graph visualization: {str(viz_error)}")
    
    # Fallback to text representation
    mermaid_code = graph.get_graph().draw_mermaid()
    print("Mermaid graph code:")
    print(mermaid_code)
    
    # Save mermaid code to file as fallback
    with open("workflow_graph.mmd", "w") as f:
        f.write(mermaid_code)
    print("Mermaid graph code saved to: workflow_graph.mmd")