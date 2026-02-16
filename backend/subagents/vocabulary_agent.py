"""
Vocabulary Agent - Sub-Agent for ConvoBridge
This agent generates vocabulary words based on questions displayed by the conversation agent.
Vocabulary helps users learn new words relevant to the conversation topic.
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

def create_vocabulary_agent():
    """
    Creates the vocabulary agent sub-agent.
    This agent generates vocabulary words based on the question displayed by the conversation agent.
    """
    agent = Agent(
        name="Vocabulary Agent",
        model=OpenAIChat(id="gpt-4o-mini"),
        description="A sub-agent that generates vocabulary words based on conversation questions, helping users learn relevant words.",
        instructions=[
            "You are a vocabulary generator for autistic youth conversation practice.",
            "When given a question, identify a key vocabulary word that would be helpful for the user to learn.",
            "The vocabulary word should be relevant to the question and topic being discussed.",
            "Choose words that are appropriate for the conversation context and educational value.",
            "",
            "Output format: Return ONLY a JSON object with the following structure:",
            "{",
            '  "word": "the vocabulary word (string)",',
            '  "type": "part of speech (noun, verb, adjective, etc.)",',
            '  "definition": "a clear, simple definition of the word",',
            '  "example": "a sentence using the word in context"',
            "}",
            "",
            "Do NOT include:",
            "  - Explanatory text",
            "  - Any text outside the JSON object",
            "  - Markdown formatting or code blocks",
            "  - Any additional commentary",
            "",
            "Example output:",
            '{"word": "preference", "type": "noun", "definition": "a greater liking for one alternative over another", "example": "My preference is to play video games in the evening."}',
            "",
            "Return ONLY the raw JSON object, nothing else.",
        ],
        markdown=False,  # Disable markdown since we're returning raw JSON
    )
    return agent

# Create the vocabulary agent instance
vocabulary_agent = create_vocabulary_agent()

if __name__ == "__main__":
    # Simple test interaction
    print("Vocabulary Agent - Ready!")
    print("This agent generates vocabulary words based on questions.\n")
    
    # Test with a sample question
    test_question = "What type of video games do you enjoy playing?"
    
    prompt = f"Generate a vocabulary word based on this question: '{test_question}'"
    
    response = vocabulary_agent.run(prompt)
    print(f"Question: {test_question}")
    print(f"Vocabulary: {response.content}\n")
