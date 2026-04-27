from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, FunctionMessage, RemoveMessage, trim_messages
from typing import List, Dict, Any, Optional
from src.agents.utils.llm import llm
from langchain_openai import ChatOpenAI
import copy

def should_summarize(messages: List) -> bool:
    """
    Determine whether conversation should be summarized.
    Now always returns True since we want to summarize after every interaction.
    
    Args:
        messages: List of conversation messages
        
    Returns:
        bool: True if summarization is needed
    """
    # Always summarize, regardless of message count
    return True

def summarize_conversation(state: Dict[str, Any], agent_key: str) -> Dict[str, Any]:
    """
    Create or update a summary of the conversation.
    
    Args:
        state: Current agent state
        agent_key: Key for the agent in the state dictionary
        
    Returns:
        Updated state with summary and trimmed messages
    """
    # Create a deep copy to avoid modifying the original state
    new_state = copy.deepcopy(state)
    
    # First, get any existing summary
    summary = new_state.get("summary", "")
    
    # Initialize the agent key in the state if it doesn't exist
    if agent_key not in new_state:
        new_state[agent_key] = {"messages": []}
    elif "messages" not in new_state[agent_key]:
        new_state[agent_key]["messages"] = []
    
    # Get the actual conversation messages
    messages = new_state[agent_key]["messages"]
    
    # Only summarize if we have actual conversation messages
    if not messages:
        return new_state
    
    # Create a more specific summarization prompt for healthcare/insurance context
    if summary:
        # A summary already exists
        summary_message = (
            f"Previous conversation summary: {summary}\n\n"
            "Based on the conversation messages above, update the summary to include:\n"
            "- User questions about reimbursements, medical files, family members\n"
            "- Assistant responses with specific data (amounts, dates, statuses)\n"
            "- Any family member references (wife, son, daughter, etc.)\n"
            "- Keep it concise but preserve key details for follow-up questions"
        )
    else:
        summary_message = (
            "Create a summary of this healthcare/insurance conversation. Include:\n"
            "- User questions about reimbursements, medical files, family members\n"
            "- Assistant responses with specific data (amounts, dates, statuses)\n"
            "- Any family member references (wife, son, daughter, etc.)\n"
            "- Keep it concise but preserve key details for follow-up questions"
        )
    
    # Add prompt to our history for summarization
    messages_with_prompt = messages + [HumanMessage(content=summary_message)]
    
    # Get the summary from the LLM
    response = llm.invoke(messages_with_prompt)
    
    # Update the summary in state
    new_state["summary"] = response.content
    
    # DEBUG: Log the summary creation
    print(f"[DEBUG SUMMARY] Created summary: '{response.content[:200]}...'")
    print(f"[DEBUG SUMMARY] Messages count: {len(messages)}")
    print(f"[DEBUG SUMMARY] Agent key: {agent_key}")
    
    # Use trim_messages to keep only the most recent messages (equivalent to ~6 messages)
    # This is more efficient than manually keeping the last N messages
    if len(new_state[agent_key]["messages"]) > 6:
        new_state[agent_key]["messages"] = trim_messages(
            new_state[agent_key]["messages"],
            max_tokens=1000,  # Approximate token count for 6 messages
            strategy="last",  # Keep the most recent messages
            token_counter=llm,  # Use the default model for token counting
            allow_partial=False  # Don't allow partial messages
        )
    
    return new_state

def update_state_with_summary(state: Dict[str, Any], agent_key: str) -> Dict[str, Any]:
    """
    Update the state with a summary of the conversation.
    
    Args:
        state: Current agent state
        agent_key: Key for the agent in the state dictionary
        
    Returns:
        Updated state with summary and trimmed messages
    """
    # Summarize the conversation
    return summarize_conversation(state, agent_key)

def get_messages_with_summary(state: Dict[str, Any], agent_key: str) -> List:
    """
    Get the messages with a summary prepended as a system message, if available.
    
    Args:
        state: Current agent state
        agent_key: Key for the agent in the state dictionary
        
    Returns:
        List of messages including summary as system message if available
    """
    # Get the current summary, if any
    summary = state.get("summary", "")
    
    # Initialize the agent key in the state if it doesn't exist
    if agent_key not in state or "messages" not in state[agent_key]:
        return []
    
    if summary:
        # Add summary to a system message
        system_message = SystemMessage(content=f"Summary of conversation earlier: {summary}")
        
        # Return messages with summary prepended
        return [system_message] + state[agent_key]["messages"]
    
    # No summary, just return the messages
    return state[agent_key]["messages"] 