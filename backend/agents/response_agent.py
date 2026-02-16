from agno.agent import Agent
from agno.models.openai import OpenAIChat

def create_response_agent():
    return Agent(
        name="Response Agent",
        model=OpenAIChat(id="gpt-4o"),
        description="You generate 3 appropriate response options for the user to choose from.",
        instructions=[
            "Generate 3 distinct responses to the previous question.",
            "Option 1: Simple/Direct answer.",
            "Option 2: Detailed/Enthusiastic answer.",
            "Option 3: A follow-up question or conversational turn.",
            "Keep the language natural and suitable for a teen.",
            "Format the output as a JSON list of strings."
        ],
        markdown=True
    )
