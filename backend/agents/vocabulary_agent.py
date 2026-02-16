from agno.agent import Agent
from agno.models.openai import OpenAIChat

def create_vocabulary_agent():
    return Agent(
        name="Vocabulary Agent",
        model=OpenAIChat(id="gpt-4o"),
        description="You identify one interesting or useful vocabulary word from the user's chosen response.",
        instructions=[
            "Given the user's response, select ONE key vocabulary word.",
            "Provide the definition suitable for a teen.",
            "Provide one example sentence using the word.",
            "Format the output as JSON: {'word': '', 'definition': '', 'example': '', 'type': 'noun/verb/etc'}"
        ],
        markdown=True
    )
