"""
Orchestrator Agent - Entry Point for ConvoBridge
This agent serves as the main orchestrator for coordinating conversations
with autistic youth in a safe and structured environment.
"""

from agno.team import Team
from agno.models.openai import OpenAIChat
from subagents.conversation_agent import create_conversation_agent
import os
from dotenv import load_dotenv

load_dotenv()

def create_orchestrator_agent():
    """
    Creates the main orchestrator team for ConvoBridge.
    This is the entry point that users will interact with.
    The team coordinates sub-agents to handle conversation practice sessions.
    """
    # Create the conversation agent member
    conversation_agent = create_conversation_agent()
    
    # Create the orchestrator team
    team = Team(
        name="ConvoBridge Orchestrator",
        model=OpenAIChat(id="gpt-4o"),
        description="A helpful team for coordinating conversation practice sessions with teens.",
        members=[conversation_agent],
        instructions=[
            "You are a friendly and supportive team leader.",
            "Help coordinate conversation practice sessions.",
            "Be encouraging and clear in your communication.",
            "When a topic is chosen, delegate to the Conversation Agent to generate an appropriate question.",
            "The Conversation Agent focuses on 'basic preferences' - likes, dislikes, favorites, and simple choices.",
            "Synthesize the responses from team members to provide a clear, helpful response to the user.",
        ],
        markdown=True,
    )
    return team

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
