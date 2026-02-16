from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

# TODO: Import agents from subagents folder as they are built
# from subagents.conversation_agent import create_conversation_agent

load_dotenv()

app = FastAPI()

# TODO: Initialize agents from subagents folder as they are built
# conversation_agent = create_conversation_agent()

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
    # TODO: Implement using subagents as they are built
    # For now, return a placeholder response
    return {
        "question": f"Placeholder question about {request.topic}",
        "response_options": ["Option 1", "Option 2", "Option 3"]
    }
    
    # # 1. Generate Question using conversation agent
    # prompt = f"Start a conversation about {request.topic} for a teen at difficulty level {request.difficulty_level}."
    # question_response = conversation_agent.run(prompt)
    # question_text = question_response.content
    #
    # # 2. Generate Response Options
    # response_prompt = f"Based on the question: '{question_text}', provide 3 potential responses for the user."
    # options_response = response_agent.run(response_prompt)
    #
    # return {
    #     "question": question_text,
    #     "response_options": options
    # }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
