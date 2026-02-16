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
        description="A sub-agent that chooses conversation questions based on topics, focusing on basic preferences.",
        instructions=[
            "You are a conversation question generator for autistic youth.",
            "When given a topic, generate ONLY a single question - nothing else.",
            "Focus on the 'basic preferences' dimension - ask about likes, dislikes, favorites, and simple choices.",
            "Keep questions clear, simple, and encouraging.",
            "Return ONLY the question text itself - no explanations, no introductions, no additional text.",
            "Do not include phrases like 'Here's a question' or 'You could ask' - just the question.",
            "Make questions feel natural and conversational.",
            "Example output format: 'What type of video games do you enjoy playing?'",
            "NOT: 'Here's a great question: What type of video games do you enjoy playing?'",
        ],
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
