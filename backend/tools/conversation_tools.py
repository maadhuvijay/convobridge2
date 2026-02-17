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
            f"{f'Previous Question: {previous_question}' if previous_question else 'No previous question'}\n"
            f"IMPORTANT: Do NOT repeat the previous question. Ask about a different aspect or angle."
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
- Use "Acknowledgement + Personal Preference + Question" format
- Start with a brief, encouraging acknowledgement of what the user said
- CRITICAL: Vary your acknowledgements - use different phrases to keep conversations natural
- Acknowledgement variety examples: 'That's great!', 'Cool!', 'Nice!', 'Awesome!', 'That sounds fun!', 'Interesting!', 'I see!', 'Got it!', 'That's awesome!', 'Sweet!', 'Neat!', 'That's really cool!', 'How cool!', 'That's neat!', 'Sounds awesome!'
- Avoid repeating the same acknowledgement phrase used in previous questions
- After the acknowledgement, add a SHORT personal preference or relatable comment on the same line (e.g., 'I like that too', 'That's interesting', 'I can relate', 'Sounds fun', 'That's cool', 'I get that')
- Keep the personal preference brief (3-6 words) and natural
- CRITICAL: NEVER repeat the same question that was asked before (check previous_question in context)
- If the previous question was similar, ask about a DIFFERENT aspect, angle, or detail of what the user mentioned
- Ask a follow-up question that relates to the specific things mentioned in the user's response
- Adapt the question to the "{current_dimension}" dimension
- Make it natural and conversational for a teen
- Keep it clear and simple (Level 1 difficulty)
- Format: 'Acknowledgement + personal preference' on first line, blank line, then question on next line

Example format: "That's great! I like that too.\n\nDo you play alone or with someone?"
Example format: "Cool! That sounds fun.\n\nWhat do you like most about it?"
Example format: "That's awesome! I can relate.\n\nHow long have you been doing that?"
Example format: "That sounds fun! I get that.\n\nWhat makes it enjoyable for you?"
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
