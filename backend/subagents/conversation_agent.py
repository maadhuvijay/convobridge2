"""
Conversation Agent - Sub-Agent for ConvoBridge
This agent chooses questions to display when a topic is selected.
Questions focus on the "basic preferences" dimension.
"""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
import os
from dotenv import load_dotenv

load_dotenv()

def create_conversation_agent():
    """
    Creates the conversation agent sub-agent.
    This agent chooses questions based on the selected topic,
    focusing on basic preferences.
    """
    agent = Agent(
        name="Conversation Agent",
        model=OpenAIChat(id="gpt-4o"),
        description="A sub-agent that chooses conversation questions based on topics, focusing on basic preferences.",
        instructions=[
            "You are a conversation question generator for autistic youth.",
            "When given a topic, choose an appropriate question to ask.",
            "Focus on the 'basic preferences' dimension - ask about likes, dislikes, favorites, and simple choices.",
            "Keep questions clear, simple, and encouraging.",
            "Ask one question at a time.",
            "Make questions feel natural and conversational.",
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
