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
            "  - The follow-up should use the 'Acknowledgement + question' format.",
            "  - Start with a brief, encouraging acknowledgement of what the user said.",
            "  - Then ask a follow-up question that relates to the specific things mentioned in the user's response.",
            "  - The question should be about the specific thing the user mentioned (e.g., if they said 'super mario', ask about super mario, not just games in general).",
            "  - Adapt the question to the requested dimension chosen by the orchestrator.",
            "  - Example format: 'That's great! Do you play alone or with someone?'",
            "  - Example format: 'Nice choice! What do you like most about it?'",
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
