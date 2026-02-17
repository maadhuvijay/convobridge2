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

CRITICAL REQUIREMENT - EMOTIONAL TONE MATCHING:
- FIRST, analyze the emotional tone of the user's response:
  * POSITIVE tone (happy, excited, enthusiastic): Use positive acknowledgements like 'That's great!', 'Awesome!', 'Cool!', 'That sounds fun!', 'Sweet!', 'That's really cool!'
  * NEGATIVE tone (frustrated, sad, disappointed, difficult): Use empathetic acknowledgements like 'I understand that can be frustrating', 'That sounds tough', 'I can see how that would be challenging', 'That must be difficult', 'I get that can be hard'
  * NEUTRAL tone (matter-of-fact, informative): Use neutral acknowledgements like 'I see', 'Got it', 'Interesting', 'That makes sense', 'I understand'
  * MIXED tone (both positive and negative): Acknowledge both aspects appropriately

- The acknowledgement MUST match the emotional tone of what the user said
- If the user expresses frustration, difficulty, or negative feelings, DO NOT use cheerful acknowledgements like "It's cool!" or "That's awesome!"
- Instead, use empathetic, understanding acknowledgements that validate their feelings
- Then add a SHORT personal preference or relatable comment that matches the tone (e.g., for negative: 'I can relate', 'That's tough', 'I understand'; for positive: 'I like that too', 'That sounds fun', 'That's cool')

Requirements:
- Use "Acknowledgement + Personal Preference + Question" format
- Start with a brief acknowledgement that MATCHES the emotional tone of the user's response
- CRITICAL: Vary your acknowledgements - use different phrases to keep conversations natural
- Avoid repeating the same acknowledgement phrase used in previous questions
- After the acknowledgement, add a SHORT personal preference or relatable comment on the same line (3-6 words) that also matches the tone
- CRITICAL: NEVER repeat the same question that was asked before (check previous_question in context)
- If the previous question was similar, ask about a DIFFERENT aspect, angle, or detail of what the user mentioned
- Ask a follow-up question that relates to the specific things mentioned in the user's response
- Adapt the question to the "{current_dimension}" dimension
- Make it natural and conversational for a teen
- Keep it clear and simple (Level 1 difficulty)
- Format: 'Acknowledgement + personal preference' on first line, blank line, then question on next line

Examples for POSITIVE tone:
"That's great! I like that too.\n\nDo you play alone or with someone?"
"Awesome! That sounds fun.\n\nWhat do you like most about it?"

Examples for NEGATIVE/FRUSTRATED tone:
"I understand that can be frustrating. I can relate.\n\nWhat makes it challenging for you?"
"That sounds tough. I get that.\n\nHow do you handle it when that happens?"

Examples for NEUTRAL tone:
"I see. That makes sense.\n\nHow often do you do that?"
"Got it. I understand.\n\nWhat do you like about it?"
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
