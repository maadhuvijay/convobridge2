from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

from agents.conversation_agent import create_conversation_agent
from agents.response_agent import create_response_agent
from agents.vocabulary_agent import create_vocabulary_agent

load_dotenv()

app = FastAPI()

# Initialize Agents
conversation_agent = create_conversation_agent()
response_agent = create_response_agent()
vocabulary_agent = create_vocabulary_agent()

class TopicRequest(BaseModel):
    topic: str
    user_id: str
    difficulty_level: int = 1

class QuestionResponse(BaseModel):
    question: str
    response_options: List[str]

@app.get("/")
def read_root():
    return {"status": "ConvoBridge Backend Active"}

@app.post("/api/start_conversation", response_model=QuestionResponse)
async def start_conversation(request: TopicRequest):
    # 1. Generate Question
    prompt = f"Start a conversation about {request.topic} for a teen at difficulty level {request.difficulty_level}."
    question_response = conversation_agent.run(prompt)
    question_text = question_response.content

    # 2. Generate Response Options
    response_prompt = f"Based on the question: '{question_text}', provide 3 potential responses for the user."
    options_response = response_agent.run(response_prompt)
    
    # In a real implementation, we'd parse the JSON properly.
    # For now, mocking the response structure to ensure flow works.
    options = ["I love playing RPGs.", "I prefer shooters with friends.", "I don't play much, what about you?"] 

    return {
        "question": question_text,
        "response_options": options
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
