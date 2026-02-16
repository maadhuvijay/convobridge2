from agno.agent import Agent
from agno.models.openai import OpenAIChat

def create_conversation_agent():
    return Agent(
        name="Conversation Agent",
        model=OpenAIChat(id="gpt-4o"),
        description="You are a friendly conversation partner for autistic teens. You ask engaging questions based on the chosen topic.",
        instructions=[
            "Always be encouraging and clear.",
            "Ask one question at a time.",
            "Keep sentences simple but natural.",
            "Adapt difficulty based on the user's level (default: Level 1/Easy)."
        ],
        markdown=True
    )
