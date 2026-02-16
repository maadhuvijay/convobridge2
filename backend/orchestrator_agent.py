"""
Orchestrator Agent - Entry Point for ConvoBridge
This agent serves as the main orchestrator for coordinating conversations
with autistic youth in a safe and structured environment.
"""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
import os
from dotenv import load_dotenv

load_dotenv()

def create_orchestrator_agent():
    """
    Creates the main orchestrator agent for ConvoBridge.
    This is the entry point that users will interact with.
    """
    agent = Agent(
        name="ConvoBridge Orchestrator",
        model=OpenAIChat(id="gpt-4o"),
        description="A helpful assistant for coordinating conversation practice sessions with teens.",
        instructions=[
            "You are a friendly and supportive assistant.",
            "Help coordinate conversation practice sessions.",
            "Be encouraging and clear in your communication.",
        ],
        markdown=True,
    )
    return agent

# Create the orchestrator instance
orchestrator = create_orchestrator_agent()

if __name__ == "__main__":
    # Simple test interaction
    print("ConvoBridge Orchestrator - Ready!")
    print("Type 'exit' to quit.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("Goodbye!")
            break
        
        response = orchestrator.run(user_input)
        print(f"\nOrchestrator: {response.content}\n")
