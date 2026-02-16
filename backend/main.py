from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import re
import json
from pathlib import Path
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from orchestrator_agent import create_orchestrator_agent
from subagents.response_generate_agent import create_response_agent
from subagents.vocabulary_agent import create_vocabulary_agent

# Load .env file - check multiple locations
backend_dir = Path(__file__).parent
root_dir = backend_dir.parent

# Try loading from multiple locations (in order of preference)
env_locations = [
    backend_dir / '.env',  # backend/.env (preferred)
    root_dir / '.env',     # root/.env (fallback)
    backend_dir / 'subagents' / '.env',  # backend/subagents/.env (fallback)
]

env_loaded = False
loaded_from = None
for env_path in env_locations:
    if env_path.exists():
        # Check file content for debugging
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    print(f"✓ Found .env file at: {env_path}")
                    print(f"  File size: {len(content)} characters")
                    # Check if OPENAI_API_KEY is in the file
                    if 'OPENAI_API_KEY' in content:
                        print(f"  Contains OPENAI_API_KEY: Yes")
                    else:
                        print(f"  Contains OPENAI_API_KEY: No")
                        print(f"  File content preview: {content[:50]}...")
        except Exception as e:
            print(f"  Error reading file: {e}")
        
        load_dotenv(dotenv_path=env_path, override=True)
        env_loaded = True
        loaded_from = env_path
        break

# If no .env file found, try default load_dotenv() behavior
if not env_loaded:
    load_dotenv()  # This will look in current directory and parent directories

# Verify API key is loaded
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("\n" + "="*60)
    print("WARNING: OPENAI_API_KEY not found in environment variables.")
    print("="*60)
    if loaded_from:
        print(f"\nThe .env file was loaded from: {loaded_from}")
        print("But OPENAI_API_KEY was not found in the environment.")
        print("\nPlease check that your .env file contains exactly:")
        print("OPENAI_API_KEY=sk-your-actual-api-key-here")
        print("\nMake sure:")
        print("  - No quotes around the key")
        print("  - No spaces around the = sign")
        print("  - The key starts with 'sk-'")
    else:
        print(f"\nPlease create a .env file in one of these locations:")
        for loc in env_locations:
            print(f"  - {loc}")
        print("\nWith the following content:")
        print("OPENAI_API_KEY=sk-your-actual-api-key-here")
    print("="*60 + "\n")
else:
    print(f"✓ OPENAI_API_KEY loaded successfully (length: {len(api_key)})")
    print(f"  Key starts with: {api_key[:7]}...")

app = FastAPI()

# Add CORS middleware to allow frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the orchestrator team and sub-agents
orchestrator = create_orchestrator_agent()
response_agent = create_response_agent()
vocabulary_agent = create_vocabulary_agent()

class TopicRequest(BaseModel):
    topic: str
    user_id: str
    difficulty_level: int = 1

class VocabularyWord(BaseModel):
    word: str
    type: str
    definition: str
    example: str

class QuestionResponse(BaseModel):
    question: str
    response_options: List[str]
    vocabulary: VocabularyWord

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
        
        # Extract just the question - remove any explanatory text
        # Look for patterns like "Here's a question:" or quotes, and extract the actual question
        
        # Remove common prefixes and explanatory text
        question_text = re.sub(r'^.*?(?:here\'?s|here is|you could ask|try asking|question:?)\s*', '', question_text, flags=re.IGNORECASE)
        question_text = re.sub(r'^.*?(?:great|good|perfect)\s+(?:question|way)\s+.*?:?\s*', '', question_text, flags=re.IGNORECASE)
        
        # Extract text within quotes if present
        quoted_match = re.search(r'["\']([^"\']+)["\']', question_text)
        if quoted_match:
            question_text = quoted_match.group(1)
        
        # Extract text after bold markers if present
        bold_match = re.search(r'\*\*([^*]+)\*\*', question_text)
        if bold_match:
            question_text = bold_match.group(1)
        
        # Clean up: remove any remaining explanatory sentences
        # Split by periods and take the first sentence that looks like a question
        sentences = question_text.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if '?' in sentence and len(sentence) > 10:
                question_text = sentence
                break
        
        # Final cleanup
        question_text = question_text.strip()
        # Remove leading/trailing quotes if any
        question_text = question_text.strip('"\'')
        
        # Generate response options using the response agent
        dimension = "basic preferences"  # Current dimension focus
        difficulty_level = f"Level {request.difficulty_level}"
        
        response_prompt = (
            f"Generate 2 response options for this question: '{question_text}'. "
            f"The dimension is '{dimension}' and difficulty is {difficulty_level}. "
            f"Make responses simple and direct."
        )
        
        response_result = response_agent.run(response_prompt)
        response_content = response_result.content.strip()
        
        # Parse the JSON response from the agent
        try:
            # Try to extract JSON array from the response
            # Remove markdown code blocks if present
            response_content = re.sub(r'```json\s*', '', response_content)
            response_content = re.sub(r'```\s*', '', response_content)
            response_content = response_content.strip()
            
            # Try to find JSON array in the response
            json_match = re.search(r'\[.*?\]', response_content, re.DOTALL)
            if json_match:
                response_content = json_match.group(0)
            
            # Parse the JSON
            options = json.loads(response_content)
            
            # Ensure we have exactly 2 options
            if not isinstance(options, list) or len(options) != 2:
                raise ValueError("Response agent did not return exactly 2 options")
            
            # Add the third "Choose your own response" option
            options.append("Choose your own response")
            
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback to default options if parsing fails
            print(f"Warning: Failed to parse response agent output: {e}")
            print(f"Response content: {response_content}")
            options = [
                "I like that topic.",
                "I'm not sure about that.",
                "Choose your own response"
            ]
        
        # Generate vocabulary using the vocabulary agent
        vocab_prompt = f"Generate a vocabulary word based on this question: '{question_text}'"
        vocab_result = vocabulary_agent.run(vocab_prompt)
        vocab_content = vocab_result.content.strip()
        
        # Parse the JSON response from the vocabulary agent
        try:
            # Try to extract JSON object from the response
            # Remove markdown code blocks if present
            vocab_content = re.sub(r'```json\s*', '', vocab_content)
            vocab_content = re.sub(r'```\s*', '', vocab_content)
            vocab_content = vocab_content.strip()
            
            # Try to find JSON object in the response
            json_match = re.search(r'\{.*?\}', vocab_content, re.DOTALL)
            if json_match:
                vocab_content = json_match.group(0)
            
            # Parse the JSON
            vocab_data = json.loads(vocab_content)
            
            # Ensure we have all required fields
            if not all(key in vocab_data for key in ['word', 'type', 'definition', 'example']):
                raise ValueError("Vocabulary agent did not return all required fields")
            
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback to default vocabulary if parsing fails
            print(f"Warning: Failed to parse vocabulary agent output: {e}")
            print(f"Vocabulary content: {vocab_content}")
            vocab_data = {
                "word": "Topic",
                "type": "noun",
                "definition": "A matter dealt with in a text, discourse, or conversation.",
                "example": "That is an interesting topic."
            }
        
        return {
            "question": question_text,
            "response_options": options,
            "vocabulary": vocab_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating question: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
