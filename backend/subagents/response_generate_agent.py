"""
Response Agent - Sub-Agent for ConvoBridge
This agent generates appropriate response options for questions asked by the conversation agent.
Responses are generated based on the dimension of the question and difficulty level.
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

def create_response_agent():
    """
    Creates the response agent sub-agent.
    This agent generates 2 response options plus a "Choose your own response" option
    based on the question, dimension, and difficulty level.
    """
    agent = Agent(
        name="Response Agent",
        model=OpenAIChat(id="gpt-4o-mini"),
        description="A sub-agent that generates appropriate response options for conversation questions, adapting to the question's dimension and difficulty level.",
        instructions=[
            "You are a response option generator for autistic youth conversation practice.",
            "When given a question, generate exactly 2 response options that are appropriate for that question.",
            "The responses should be simple and direct (Level 1 difficulty).",
            "Responses should be non-deterministic - vary them each time based on the specific question asked.",
            "Adapt responses to match the dimension of the question:",
            "  - For 'basic preferences' dimension: focus on likes, dislikes, favorites, and simple choices",
            "  - Make responses feel natural and conversational",
            "  - Keep responses concise and clear",
            "",
            "Output format: Return ONLY a JSON array with exactly 2 response strings.",
            "Example output: [\"I really enjoy playing action games.\", \"I prefer puzzle games more.\"]",
            "",
            "Do NOT include:",
            "  - The third 'Choose your own response' option (that will be added separately)",
            "  - Explanatory text",
            "  - Any text outside the JSON array",
            "  - Markdown formatting or code blocks",
            "  - Any additional commentary",
            "",
            "The responses should be diverse and appropriate to the specific question asked.",
            "Return ONLY the raw JSON array, nothing else.",
        ],
        markdown=False,  # Disable markdown since we're returning raw JSON
    )
    return agent

# Create the response agent instance
response_agent = create_response_agent()

if __name__ == "__main__":
    # Simple test interaction
    print("Response Agent - Ready!")
    print("This agent generates response options for questions.\n")
    
    # Test with a sample question
    test_question = "What type of video games do you enjoy playing?"
    test_dimension = "basic preferences"
    test_difficulty = "Level 1"
    
    prompt = f"Generate 2 response options for this question: '{test_question}'. The dimension is '{test_dimension}' and difficulty is {test_difficulty}. Make responses simple and direct."
    
    response = response_agent.run(prompt)
    print(f"Question: {test_question}")
    print(f"Dimension: {test_dimension}")
    print(f"Difficulty: {test_difficulty}")
    print(f"Response Options: {response.content}\n")
