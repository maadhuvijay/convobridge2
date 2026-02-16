from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from orchestrator_agent import create_orchestrator_agent

load_dotenv()

app = FastAPI()

# Add CORS middleware to allow frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the orchestrator team
orchestrator = create_orchestrator_agent()

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
    """
    Start a conversation by generating a question based on the selected topic.
    Uses the orchestrator team which delegates to the conversation agent.
    """
    try:
        # Create a prompt for the orchestrator team
        # The team will delegate to the conversation agent to generate a question
        prompt = f"Generate a conversation question about {request.topic} for a teen. Focus on basic preferences - likes, dislikes, favorites, and simple choices. The difficulty level is {request.difficulty_level}."
        
        # Run the orchestrator team
        response = orchestrator.run(prompt)
        question_text = response.content.strip()
        
        # For now, return placeholder response options
        # TODO: Add response agent later to generate these
        options = [
            "I like that topic.",
            "I'm not sure about that.",
            "Can you tell me more?"
        ]
        
        return {
            "question": question_text,
            "response_options": options
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating question: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
