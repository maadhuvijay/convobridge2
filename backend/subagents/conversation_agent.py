"""
Conversation Agent - Sub-Agent for ConvoBridge
This agent chooses questions to display when a topic is selected.
Questions focus on the "basic preferences" dimension.
"""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
import os
from pathlib import Path
from dotenv import load_dotenv

# Import conversation tools
from tools.conversation_tools import get_context, generate_followup_question
from tools.text_to_speech import text_to_speech_base64

# Load .env file from the backend directory
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / '.env'
load_dotenv(dotenv_path=env_path)

def create_conversation_agent():
    """
    Creates the conversation agent sub-agent.
    This agent chooses questions based on the selected topic,
    focusing on basic preferences.
    """
    agent = Agent(
        name="Conversation Agent",
        model=OpenAIChat(id="gpt-4o-mini"),
        description="A sub-agent that chooses conversation questions based on topics and dimensions.",
        instructions=[
            "You are a conversation question generator for autistic youth.",
            "",
            "You have access to two tools:",
            "  1. get_context - Gets the conversation context (user response, dimension, topic)",
            "  2. generate_followup_question - Generates a follow-up question based on context",
            "",
            "For INITIAL questions (when no user response is provided):",
            "  - Generate ONLY a single question - nothing else.",
            "  - Adapt the question to the requested dimension.",
            "  - Return ONLY the question text itself - no explanations, no introductions.",
            "",
            "For FOLLOW-UP questions (when user response is provided):",
            "  - First, use get_context to gather the conversation context.",
            "  - Then, use generate_followup_question to create a contextual follow-up.",
            "  - The follow-up should use the 'Acknowledgement + personal preference + question' format.",
            "  - CRITICAL: Analyze the emotional tone of the user's response FIRST, then match your acknowledgement:",
            "    * POSITIVE tone (happy, excited, enthusiastic): Use positive acknowledgements like 'That's great!', 'Awesome!', 'Cool!', 'That sounds fun!'",
            "    * NEGATIVE tone (frustrated, sad, disappointed, difficult): Use empathetic acknowledgements like 'I understand that can be frustrating', 'That sounds tough', 'I can see how that would be challenging', 'That must be difficult'",
            "    * NEUTRAL tone (matter-of-fact, informative): Use neutral acknowledgements like 'I see', 'Got it', 'Interesting', 'That makes sense'",
            "  - DO NOT use cheerful acknowledgements (like 'It's cool!' or 'That's awesome!') when the user expresses frustration, difficulty, or negative feelings.",
            "  - Instead, use empathetic, understanding acknowledgements that validate their feelings.",
            "  - After the acknowledgement, add a SHORT personal preference or relatable comment that MATCHES the tone:",
            "    * For positive: 'I like that too', 'That sounds fun', 'That's cool'",
            "    * For negative: 'I can relate', 'That's tough', 'I understand', 'I get that'",
            "    * For neutral: 'That makes sense', 'I understand', 'I see'",
            "  - Keep the personal preference brief (3-6 words) and natural.",
            "  - CRITICAL: Vary your acknowledgements - use different phrases each time to keep conversations natural.",
            "  - Avoid repeating the same acknowledgement phrase in consecutive questions.",
            "  - CRITICAL: NEVER repeat the same question that was asked before. Check the previous_question in context.",
            "  - If the previous question was similar, ask about a DIFFERENT aspect or angle of the topic.",
            "  - The question should be about the specific thing the user mentioned (e.g., if they said 'super mario', ask about super mario, not just games in general).",
            "  - Adapt the question to the requested dimension chosen by the orchestrator.",
            "  - IMPORTANT: Format as: 'Acknowledgement + personal preference' on first line, blank line, then question on next line.",
            "  - Example format (positive): 'That's great! I like that too.\n\nDo you play alone or with someone?'",
            "  - Example format (negative): 'I understand that can be frustrating. I can relate.\n\nWhat makes it challenging for you?'",
            "  - Example format (neutral): 'I see. That makes sense.\n\nHow often do you do that?'",
            "  - The first line (acknowledgement + preference) should end with punctuation (! or .), followed by two newlines, then the question.",
            "",
            "Dimensions to adapt questions to:",
            "  - Basic Preferences: Likes, dislikes, favorites, simple choices",
            "  - Depth/Specificity: Dig deeper into a specific aspect",
            "  - Social Context: Involve friends, family, or social situations",
            "  - Emotional: Feelings, excitement, frustration, reactions",
            "  - Temporal/Frequency: When, how often, past experiences, future plans",
            "  - Comparative: Compare two things, what is better/worse",
            "  - Reflective/Why: Reasons, motivations, 'why' questions",
            "  - Descriptive/Detail: Sensory details, appearance, setting",
            "  - Challenge/Growth: Learning curves, difficulties, improvements",
            "",
            "Keep questions clear, simple, and encouraging (Level 1 difficulty unless specified).",
            "Make questions feel natural and conversational.",
        ],
        tools=[get_context, generate_followup_question],
        markdown=True,
    )
    return agent

# Create the conversation agent instance
conversation_agent = create_conversation_agent()

if __name__ == "__main__":
    # Simple test interaction
    print("Conversation Agent - Ready!")
    print("This agent chooses questions based on topics.\n")
    
    # Test with a sample topic
    test_topic = "gaming"
    prompt = f"Choose a question about {test_topic} that focuses on basic preferences."
    
    response = conversation_agent.run(prompt)
    print(f"Topic: {test_topic}")
    print(f"Question: {response.content}\n")
