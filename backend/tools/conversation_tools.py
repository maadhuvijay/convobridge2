"""
Conversation Tools - Tools for ConvoBridge Conversation Agent
These tools help the conversation agent generate contextual follow-up questions
based on user responses and orchestrator-selected dimensions.
"""

from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the backend directory
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / '.env'
load_dotenv(dotenv_path=env_path)


def get_context(
    user_response: str,
    current_dimension: str,
    topic: str,
    previous_question: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get the conversation context including user's response, current dimension, and topic.
    This context is used to generate appropriate follow-up questions.
    
    Args:
        user_response: The teen's response to the previous question
        current_dimension: The dimension chosen by the orchestrator based on engagement
                          (e.g., "basic preferences", "depth/specificity", "social context", 
                          "emotional", "temporal/frequency", "comparative", "reflective/why",
                          "descriptive/detail", "challenge/growth")
        topic: The current conversation topic (e.g., "gaming", "weekend", "hobbies")
        previous_question: The previous question that was asked (optional)
    
    Returns:
        A dictionary containing the conversation context with the following keys:
        - user_response: The teen's response
        - current_dimension: The selected dimension
        - topic: The conversation topic
        - previous_question: The previous question (if provided)
        - context_summary: A formatted summary of the context
    """
    context = {
        "user_response": user_response,
        "current_dimension": current_dimension,
        "topic": topic,
        "previous_question": previous_question,
        "context_summary": (
            f"Topic: {topic}\n"
            f"User Response: {user_response}\n"
            f"Dimension: {current_dimension}\n"
            f"{f'Previous Question: {previous_question}' if previous_question else ''}"
        )
    }
    
    return context


def generate_followup_question(
    user_response: str,
    current_dimension: str,
    topic: str,
    previous_question: Optional[str] = None
) -> str:
    """
    Generate a contextual follow-up question based on the user's response and selected dimension.
    The question follows the "Acknowledgement + Question" pattern to create natural conversation flow.
    
    Args:
        user_response: The teen's response to the previous question
        current_dimension: The dimension chosen by the orchestrator
                          (e.g., "basic preferences", "depth/specificity", "social context", 
                          "emotional", "temporal/frequency", "comparative", "reflective/why",
                          "descriptive/detail", "challenge/growth")
        topic: The current conversation topic
        previous_question: The previous question that was asked (optional)
    
    Returns:
        A follow-up question string that:
        1. Starts with a brief, encouraging acknowledgement of what the user said
        2. Then asks a follow-up question that relates to the specific things mentioned
        3. Adapts to the requested dimension
        4. Uses natural, conversational language suitable for teens
        
    Example:
        If user_response is "I like playing Super Mario", dimension is "social context", and topic is "gaming":
        Returns: "That's awesome! Do you usually play Super Mario alone or with friends?"
    """
    # Build context for question generation
    context_parts = []
    
    if previous_question:
        context_parts.append(f"Previous question: {previous_question}")
    
    context_parts.append(f"User's response: {user_response}")
    context_parts.append(f"Topic: {topic}")
    context_parts.append(f"Target dimension: {current_dimension}")
    
    context_text = "\n".join(context_parts)
    
    # Return formatted context that the agent can use to generate the question
    # The actual question generation will be done by the conversation agent
    # This tool provides the structured context needed
    return f"""Generate a follow-up question using this context:

{context_text}

Requirements:
- Use "Acknowledgement + Question" format
- Start with a brief, encouraging acknowledgement of what the user said
- Ask a follow-up question that relates to the specific things mentioned in the user's response
- Adapt the question to the "{current_dimension}" dimension
- Make it natural and conversational for a teen
- Keep it clear and simple (Level 1 difficulty)

Example format: "That's great! Do you play alone or with someone?"
Example format: "Nice choice! What do you like most about it?"
"""


# For backwards compatibility and direct usage
def create_conversation_context(
    user_response: str,
    dimension: str,
    topic: str,
    previous_question: Optional[str] = None
) -> Dict[str, Any]:
    """
    Alias for get_context for convenience.
    Creates conversation context for follow-up question generation.
    """
    return get_context(
        user_response=user_response,
        current_dimension=dimension,
        topic=topic,
        previous_question=previous_question
    )


if __name__ == "__main__":
    # Simple test
    print("Conversation Tools - Ready!\n")
    
    # Test get_context
    context = get_context(
        user_response="I like playing Super Mario",
        current_dimension="social context",
        topic="gaming",
        previous_question="What type of video games do you enjoy playing?"
    )
    print("Context:")
    print(context["context_summary"])
    print()
    
    # Test generate_followup_question
    followup_prompt = generate_followup_question(
        user_response="I like playing Super Mario",
        current_dimension="social context",
        topic="gaming",
        previous_question="What type of video games do you enjoy playing?"
    )
    print("Follow-up Question Prompt:")
    print(followup_prompt)
