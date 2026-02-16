"""
Orchestrator Agent - Entry Point for ConvoBridge
This agent serves as the main orchestrator for coordinating conversations
with autistic youth in a safe and structured environment.
"""

from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.tools.reasoning import ReasoningTools
from subagents.conversation_agent import create_conversation_agent
from subagents.response_generate_agent import create_response_agent
from subagents.vocabulary_agent import create_vocabulary_agent
from subagents.speech_analysis_agent import create_speech_analysis_agent
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file - check multiple locations
backend_dir = Path(__file__).parent
root_dir = backend_dir.parent

# Try loading from multiple locations (in order of preference)
env_locations = [
    backend_dir / '.env',  # backend/.env (preferred)
    root_dir / '.env',     # root/.env (fallback)
    backend_dir / 'subagents' / '.env',  # backend/subagents/.env (fallback)
]

for env_path in env_locations:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        break
else:
    # If no .env file found, try default load_dotenv() behavior
    load_dotenv()  # This will look in current directory and parent directories

def create_orchestrator_agent():
    """
    Creates the main orchestrator team for ConvoBridge.
    This is the entry point that users will interact with.
    The team coordinates sub-agents to handle conversation practice sessions.
    """
    # Create the sub-agent members
    conversation_agent = create_conversation_agent()
    response_agent = create_response_agent()
    vocabulary_agent = create_vocabulary_agent()
    speech_analysis_agent = create_speech_analysis_agent()
    
    # Create the orchestrator team with reasoning tools
    team = Team(
        name="ConvoBridge Orchestrator",
        model=OpenAIChat(id="gpt-4o-mini"),
        description="A helpful team for coordinating conversation practice sessions with teens.",
        members=[conversation_agent, response_agent, vocabulary_agent, speech_analysis_agent],
        tools=[
            ReasoningTools(
                enable_think=True,
                enable_analyze=True,
                add_instructions=True,
                add_few_shot=True,
            )
        ],
        instructions=[
            "You are a friendly and supportive team leader with strong reasoning capabilities.",
            "Use reasoning tools (think and analyze) when you need to:",
            "  - Break down complex coordination tasks into steps",
            "  - Decide which sub-agent to delegate to and when",
            "  - Reflect on the quality of responses from sub-agents",
            "  - Adjust your approach based on the conversation context",
            "  - Consider multiple perspectives before making decisions",
            "",
            "Help coordinate conversation practice sessions.",
            "When a topic is chosen, delegate to the Conversation Agent to generate an appropriate question.",
            "The Conversation Agent focuses on 'basic preferences' - likes, dislikes, favorites, and simple choices.",
            "IMPORTANT: When the Conversation Agent returns a question, extract and return ONLY the question text itself.",
            "Remove any explanatory text, introductions, or additional commentary.",
            "Return just the question - for example: 'What type of video games do you enjoy playing?'",
            "Do not add any text before or after the question.",
            "",
            "The Response Agent is available to generate response options for questions.",
            "It generates 2 response options based on the question's dimension and difficulty level.",
            "The Response Agent focuses on Level 1 difficulty: simple and direct responses.",
            "",
            "The Vocabulary Agent is available to generate vocabulary words based on questions.",
            "It identifies key vocabulary words that are relevant to the question and topic being discussed.",
            "The Vocabulary Agent helps users learn new words relevant to their conversations.",
            "",
            "The Speech Analysis Agent is available to analyze speech responses from teens.",
            "It transcribes speech, analyzes the transcript for clarity and coherence,",
            "provides a speech clarity score (0-100), and gives encouraging feedback to help teens improve.",
            "The Speech Analysis Agent focuses on positive reinforcement and building confidence.",
            "",
            "When coordinating, think through your decisions step by step:",
            "  1. Understand the task and context",
            "  2. Identify which sub-agent(s) are needed",
            "  3. Consider the best approach for delegation",
            "  4. Analyze the results and ensure quality",
            "  5. Adjust if needed based on the response quality",
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
