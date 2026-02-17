from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import re
import json
import sys
import random
import asyncio
import tempfile
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import threading

# Import subprocess for audio conversion (replacing pydub due to Python 3.13 compatibility issues)
import subprocess

# Check if ffmpeg is available
FFMPEG_AVAILABLE = False
try:
    # Try to run ffmpeg -version to check if it's available
    result = subprocess.run(
        ['ffmpeg', '-version'],
        capture_output=True,
        timeout=2
    )
    FFMPEG_AVAILABLE = result.returncode == 0
except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
    FFMPEG_AVAILABLE = False

if not FFMPEG_AVAILABLE:
    print("\n" + "="*60)
    print("WARNING: ffmpeg is not available.")
    print("Audio conversion will fail. Please install ffmpeg:")
    print("  Windows: Download from https://ffmpeg.org/download.html and add to PATH")
    print("  macOS: brew install ffmpeg")
    print("  Linux: sudo apt-get install ffmpeg")
    print("="*60 + "\n")

def convert_audio_to_wav(input_path: str, output_path: str) -> bool:
    """
    Convert audio file to WAV format using ffmpeg directly.
    Returns True if successful, False otherwise.
    """
    if not FFMPEG_AVAILABLE:
        print("Error: ffmpeg is not available for audio conversion")
        return False
        
    try:
        # Run ffmpeg command
        # -i input_path: Input file
        # -ac 1: Convert to mono (optional but good for speech)
        # -ar 16000: Set sample rate to 16kHz (good for speech recognition)
        # -y: Overwrite output file
        cmd = ['ffmpeg', '-i', input_path, '-ac', '1', '-ar', '16000', '-y', output_path]
        
        # On Windows, we might need shell=True or full path if not in PATH, 
        # but usually adding to PATH is the right way.
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"ffmpeg conversion failed: {result.stderr}")
            return False
            
        return True
    except Exception as e:
        print(f"Error during ffmpeg conversion: {e}")
        return False

# Pydub imports removed due to Python 3.13 incompatibility (missing audioop)
PYDUB_AVAILABLE = False
AudioSegment = None

from orchestrator_agent import create_orchestrator_agent
from subagents.conversation_agent import create_conversation_agent
from subagents.response_generate_agent import create_response_agent
from subagents.vocabulary_agent import create_vocabulary_agent
from subagents.speech_analysis_agent import create_speech_analysis_agent, analyze_speech_with_audio
from database import (
    create_user, get_user_by_id, get_user_by_name,
    create_session, is_first_question_for_topic,
    end_session, get_active_session,
    is_returning_user, get_last_topic_for_user,
    get_or_create_session_topic, create_conversation_turn,
    update_conversation_turn_with_response,
    update_conversation_turn_with_speech_analysis,
    save_response_options, save_vocabulary_word,
    get_response_options_for_turn, get_current_session_topic,
    get_current_turn, get_last_conversation_turn
)
from tools.text_to_speech import text_to_speech_base64

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
                    print(f"[OK] Found .env file at: {env_path}")
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
    print(f"[OK] OPENAI_API_KEY loaded successfully (length: {len(api_key)})")
    print(f"  Key starts with: {api_key[:7]}...")

app = FastAPI()

# Add CORS middleware to allow frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dimensions for conversation follow-up questions
DIMENSIONS = [
    "Depth/Specificity",
    "Social Context",
    "Emotional",
    "Temporal / Frequency",
    "Comparative",
    "Reflective / Why",
    "Descriptive / Detail",
    "Challenge / Growth"
]

# Note: User session tracking is now handled by Supabase database
# See database.py for database operations

# Lightweight session cache for active sessions (3 minute TTL)
# This is an optional optimization - database is always the source of truth
class SessionCache:
    def __init__(self, ttl_minutes: int = 3):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        self.lock = threading.Lock()
    
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached session state if not expired"""
        with self.lock:
            if cache_key in self.cache:
                entry = self.cache[cache_key]
                if datetime.now() - entry['timestamp'] < self.ttl:
                    return entry['data']
                else:
                    # Expired, remove it
                    del self.cache[cache_key]
            return None
    
    def set(self, cache_key: str, data: Dict[str, Any]):
        """Cache session state with timestamp"""
        with self.lock:
            self.cache[cache_key] = {
                'data': data,
                'timestamp': datetime.now()
            }
    
    def clear(self, cache_key: str):
        """Remove entry from cache"""
        with self.lock:
            if cache_key in self.cache:
                del self.cache[cache_key]
    
    def cleanup_expired(self):
        """Remove all expired entries (can be called periodically)"""
        with self.lock:
            now = datetime.now()
            expired_keys = [
                key for key, entry in self.cache.items()
                if now - entry['timestamp'] >= self.ttl
            ]
            for key in expired_keys:
                del self.cache[key]
            return len(expired_keys)

# Global session cache instance
session_cache = SessionCache(ttl_minutes=3)

# Initialize the orchestrator team and sub-agents
orchestrator = create_orchestrator_agent()
conversation_agent = create_conversation_agent()
response_agent = create_response_agent()
vocabulary_agent = create_vocabulary_agent()
speech_analysis_agent = create_speech_analysis_agent()

class TopicRequest(BaseModel):
    topic: str
    user_id: str
    session_id: str  # Required: session_id from login
    difficulty_level: int = 1

class VocabularyWord(BaseModel):
    word: str
    type: str
    definition: str
    example: str

class QuestionResponse(BaseModel):
    question: str
    dimension: str
    response_options: List[str]
    vocabulary: VocabularyWord

class QuestionOnlyResponse(BaseModel):
    question: str
    dimension: str = "Basic Preferences"
    audio_base64: Optional[str] = None  # Base64-encoded audio for text-to-speech
    turn_id: Optional[str] = None  # Conversation turn ID for linking response options and vocabulary

class ContinueConversationRequest(BaseModel):
    topic: str
    user_id: str
    session_id: str  # Required: session_id from login
    previous_question: str
    previous_turn_id: Optional[str] = None  # ID of previous conversation turn
    user_response: Optional[str] = None
    difficulty_level: int = 1

class ConversationDetailsRequest(BaseModel):
    question: str
    topic: str
    turn_id: str  # Required: conversation_turn_id to link response options and vocabulary
    difficulty_level: int = 1
    dimension: str = "Basic Preferences"

class ConversationDetailsResponse(BaseModel):
    response_options: List[str]
    vocabulary: VocabularyWord

class LoginRequest(BaseModel):
    username: str

class LoginResponse(BaseModel):
    user_id: str
    username: str
    login_timestamp: str
    session_id: Optional[str] = None
    message: str
    is_returning_user: bool = False
    last_topic: Optional[str] = None  # Last topic name if returning user

class GetUserRequest(BaseModel):
    user_id: Optional[str] = None
    username: Optional[str] = None

class GetUserResponse(BaseModel):
    user_id: str
    username: str
    created_at: str
    updated_at: str

class SpeechAnalysisRequest(BaseModel):
    expected_response: Optional[str] = None  # The expected response text for WER calculation

class SpeechAnalysisResponse(BaseModel):
    transcript: str
    wer_estimate: Optional[float] = None
    clarity_score: float
    pace_wpm: int
    filler_words: List[str]
    feedback: str
    strengths: List[str]
    suggestions: List[str]

class TextToSpeechRequest(BaseModel):
    text: str
    voice: Optional[str] = "nova"
    model: Optional[str] = "tts-1-hd"
    format: Optional[str] = "mp3"

class TextToSpeechResponse(BaseModel):
    audio_base64: str
    format: str

class LogoutRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None  # Optional: if not provided, will find active session

class LogoutResponse(BaseModel):
    success: bool
    message: str
    session_id: Optional[str] = None
    ended_at: Optional[str] = None

class GetPreviousTopicStateRequest(BaseModel):
    user_id: str
    topic_name: str

class GetPreviousTopicStateResponse(BaseModel):
    topic_name: str
    difficulty_level: int
    dimension: str
    last_response_options: List[str]
    last_question: Optional[str] = None

@app.get("/")
def read_root():
    return {"status": "ConvoBridge Backend Active"}

@app.post("/api/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Log user login with username and timestamp.
    Creates or retrieves user from database and creates a new session.
    Falls back to in-memory storage if Supabase is not configured.
    """
    try:
        username = request.username.strip()
        if not username:
            raise HTTPException(status_code=400, detail="Username cannot be empty")
        
        # Create or get user from database
        user = create_user(username)
        
        # Fallback to simple user_id generation if database is not available
        if not user:
            print("Warning: Database not available, using fallback user ID generation")
            # Generate a simple user_id for fallback
            import uuid
            user_id = str(uuid.uuid4())
            login_timestamp = datetime.now().isoformat()
            
            return {
                "user_id": user_id,
                "username": username,
                "login_timestamp": login_timestamp,
                "session_id": None,
                "message": "Login successful (database not configured - using fallback)"
            }
        
        user_id = str(user['id'])
        login_timestamp = datetime.now().isoformat()
        
        # Check if returning user
        returning = is_returning_user(username)
        last_topic = None
        
        if returning:
            # Get last topic for returning user
            last_topic_data = get_last_topic_for_user(user_id)
            if last_topic_data and 'topic_name' in last_topic_data:
                last_topic = last_topic_data['topic_name']
                print(f"Returning user '{username}' - last topic: {last_topic}")
        
        # Create a new session for this login
        session = create_session(user_id)
        session_id = str(session['id']) if session else None
        
        print(f"User logged in: {username} (ID: {user_id}) at {login_timestamp}")
        if session_id:
            print(f"Created session: {session_id}")
        
        return {
            "user_id": user_id,
            "username": user['name'],
            "login_timestamp": login_timestamp,
            "session_id": session_id,
            "message": "Login successful",
            "is_returning_user": returning,
            "last_topic": last_topic
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during login: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")

@app.post("/api/logout", response_model=LogoutResponse)
async def logout(request: LogoutRequest):
    """
    Log user logout with timestamp.
    Ends the active session by updating ended_at timestamp and setting status to 'completed'.
    All session data (conversation turns, response options, vocabulary, etc.) is already saved
    in the database during the session, so this just marks the session as completed.
    """
    try:
        user_id = request.user_id.strip()
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID cannot be empty")
        
        session_id = request.session_id
        
        # If session_id not provided, find the active session for this user
        if not session_id:
            active_session = get_active_session(user_id)
            if not active_session:
                return {
                    "success": False,
                    "message": "No active session found for this user",
                    "session_id": None,
                    "ended_at": None
                }
            session_id = str(active_session['id'])
        
        # End the session
        ended_session = end_session(session_id)
        
        if not ended_session:
            return {
                "success": False,
                "message": "Failed to end session",
                "session_id": session_id,
                "ended_at": None
            }
        
        ended_at = ended_session.get('ended_at')
        print(f"User logged out: {user_id} (Session: {session_id}) at {ended_at}")
        
        return {
            "success": True,
            "message": "Logout successful. Session data saved.",
            "session_id": session_id,
            "ended_at": ended_at
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during logout: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error during logout: {str(e)}")

@app.post("/api/get_previous_topic_state", response_model=GetPreviousTopicStateResponse)
async def get_previous_topic_state(request: GetPreviousTopicStateRequest):
    """
    Get the previous topic state for continuing a previous conversation.
    Returns difficulty_level, dimension, and last response_options for the topic.
    """
    try:
        user_id = request.user_id
        topic_name = request.topic_name
        
        # Get last topic data for user
        last_topic_data = get_last_topic_for_user(user_id)
        
        if not last_topic_data or last_topic_data.get('topic_name') != topic_name:
            raise HTTPException(
                status_code=404,
                detail=f"No previous conversation found for topic '{topic_name}'"
            )
        
        # Extract information from last turn
        difficulty_level = last_topic_data.get('difficulty_level', 1)
        dimension = last_topic_data.get('dimension', 'Basic Preferences')
        last_question = last_topic_data.get('question', '')
        turn_id = str(last_topic_data['id'])
        
        # Get response options for the last turn
        response_options_data = get_response_options_for_turn(turn_id)
        last_response_options = [opt['option_text'] for opt in response_options_data] if response_options_data else []
        
        # If no response options found, return empty list (frontend will generate new ones)
        if not last_response_options:
            print(f"Warning: No response options found for turn {turn_id}, returning empty list")
        
        return {
            "topic_name": topic_name,
            "difficulty_level": difficulty_level,
            "dimension": dimension,
            "last_response_options": last_response_options,
            "last_question": last_question
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting previous topic state: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error retrieving previous topic state: {str(e)}")

@app.post("/api/get_user", response_model=GetUserResponse)
async def get_user(request: GetUserRequest):
    """
    Retrieve user information from database by user_id or username.
    """
    try:
        user = None
        
        if request.user_id:
            user = get_user_by_id(request.user_id)
        elif request.username:
            user = get_user_by_name(request.username)
        else:
            raise HTTPException(status_code=400, detail="Either user_id or username must be provided")
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "user_id": str(user['id']),
            "username": user['name'],
            "created_at": user['created_at'],
            "updated_at": user['updated_at']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user: {str(e)}")

@app.post("/api/start_conversation", response_model=QuestionOnlyResponse)
async def start_conversation(request: TopicRequest):
    """
    Fast endpoint: Generate and return question immediately using conversation agent.
    This allows the frontend to show the question while responses and vocabulary load in the background.
    Always uses "Basic Preferences" dimension for the first question on any topic.
    """
    try:
        user_id = request.user_id
        topic = request.topic
        
        # Check if this is the first question for this topic using database
        # Fallback to True if database is not available
        try:
            is_first_question = is_first_question_for_topic(user_id, topic)
        except Exception as e:
            print(f"Warning: Error checking first question in database: {e}. Defaulting to first question.")
            is_first_question = True
        
        # Always use Basic Preferences for the first question on any topic
        if is_first_question:
            dimension = "Basic Preferences"
            print(f"First question for user {user_id} on topic {topic} - using Basic Preferences")
        else:
            # This shouldn't happen if frontend is working correctly, but handle it
            dimension = "Basic Preferences"
            print(f"Warning: start_conversation called for non-first question. Using Basic Preferences.")
        
        # Create a prompt for the conversation agent
        prompt = f"Generate a conversation question about {request.topic} for a teen. Dimension: {dimension}. The difficulty level is {request.difficulty_level}."
        
        # Run the conversation agent directly
        response = conversation_agent.run(prompt)
        question_text = response.content.strip()
        
        # Extract just the question - remove any explanatory text
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
        
        # Save conversation state to database
        turn_id = None
        try:
            # Get or create session_topic
            session_topic = get_or_create_session_topic(request.session_id, topic)
            if not session_topic:
                print(f"Warning: Failed to get/create session_topic for session {request.session_id}, topic {topic}")
            else:
                session_topic_id = str(session_topic['id'])
                # Get current turn count to determine turn_number
                current_turn = get_current_turn(session_topic_id)
                turn_number = 1
                if current_turn:
                    turn_number = current_turn.get('turn_number', 0) + 1
                
                # Create conversation_turn
                conversation_turn = create_conversation_turn(
                    session_topic_id=session_topic_id,
                    turn_number=turn_number,
                    dimension=dimension,
                    difficulty_level=request.difficulty_level,
                    question=question_text
                )
                
                if conversation_turn:
                    turn_id = str(conversation_turn['id'])
                    print(f"Created conversation turn {turn_number} (ID: {turn_id}) for topic {topic}")
                else:
                    print(f"Warning: Failed to create conversation_turn for session_topic {session_topic_id}")
        except Exception as e:
            print(f"Warning: Error saving conversation state to database: {e}")
            import traceback
            traceback.print_exc()
            # Continue even if database save fails
        
        # Generate audio for the question using text-to-speech
        audio_base64 = None
        try:
            # Remove newlines for TTS (keep the text clean for speech)
            clean_text_for_speech = question_text.replace('\n\n', '. ').replace('\n', ' ')
            loop = asyncio.get_event_loop()
            audio_base64 = await loop.run_in_executor(
                None,
                text_to_speech_base64,
                clean_text_for_speech
            )
            if audio_base64:
                print(f"Generated audio for question ({len(audio_base64)} characters base64)")
        except Exception as e:
            print(f"Warning: Failed to generate audio for question: {e}")
            # Don't fail the request if audio generation fails
        
        return {
            "question": question_text,
            "dimension": dimension,
            "audio_base64": audio_base64,
            "turn_id": turn_id
        }
    except Exception as e:
        print(f"Error starting conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating question: {str(e)}")

@app.post("/api/continue_conversation", response_model=QuestionOnlyResponse)
async def continue_conversation(request: ContinueConversationRequest):
    """
    Generate a follow-up question based on previous context using conversation tools.
    The orchestrator chooses the dimension, and the conversation agent uses tools to generate contextual follow-ups.
    """
    try:
        if not request.user_response:
            raise HTTPException(status_code=400, detail="user_response is required for follow-up questions")
        
        # Update previous turn with user response (if previous_turn_id provided)
        if request.previous_turn_id:
            try:
                # Determine response type (for now, assume custom_speech or custom_text)
                # Frontend should indicate if it was a selected option
                response_type = "custom_speech"  # Default, can be updated based on frontend input
                updated_turn = update_conversation_turn_with_response(
                    turn_id=request.previous_turn_id,
                    user_response=request.user_response,
                    response_type=response_type
                )
                if updated_turn:
                    print(f"Updated previous turn {request.previous_turn_id} with user response")
                else:
                    print(f"Warning: Failed to update previous turn {request.previous_turn_id}")
            except Exception as e:
                print(f"Warning: Error updating previous turn: {e}")
                # Continue even if update fails
        
        # Orchestrator chooses dimension based on user response and engagement
        # For now, randomly select a dimension (can be enhanced with orchestrator logic later)
        dimension = random.choice(DIMENSIONS)
        print(f"Continuing conversation. Selected dimension: {dimension}")
        print(f"User response: {request.user_response}")
        
        # Use conversation agent with tools to generate follow-up question
        # The agent will use get_context and generate_followup_question tools
        prompt = (
            f"Generate a FOLLOW-UP question using your tools.\n\n"
            f"First, use get_context with:\n"
            f"- user_response: '{request.user_response}'\n"
            f"- current_dimension: '{dimension}'\n"
            f"- topic: '{request.topic}'\n"
            f"- previous_question: '{request.previous_question}'\n\n"
            f"Then, use generate_followup_question with the same parameters to create a contextual follow-up.\n\n"
            f"CRITICAL REQUIREMENTS:\n"
            f"- Use 'Acknowledgement + Personal Preference + Question' format\n"
            f"- Format: 'Acknowledgement + short personal preference' on first line, blank line, then question on next line\n"
            f"- VARY your acknowledgement - use a different phrase than you might have used before\n"
            f"- Add a brief personal preference after the acknowledgement (e.g., 'I like that too', 'That's interesting', 'I can relate')\n"
            f"- NEVER repeat the previous question: '{request.previous_question}'\n"
            f"- Ask about a DIFFERENT aspect or angle of what the user mentioned\n"
            f"- Be about the specific things mentioned in the user's response\n"
            f"- Adapt to the {dimension} dimension\n"
            f"- Be natural and conversational for a teen"
        )
        
        # Run conversation agent (it will use the tools)
        response = conversation_agent.run(prompt)
        
        # ===== DIAGNOSTIC LOGGING =====
        print("\n" + "="*80)
        print("[DEBUG] RAW AGENT RESPONSE DIAGNOSTICS")
        print("="*80)
        print(f"[DEBUG] Response type: {type(response)}")
        print(f"[DEBUG] Response class: {response.__class__.__name__}")
        
        # Check for content attribute
        if hasattr(response, 'content'):
            raw_content = response.content
            print(f"[DEBUG] Raw response content length: {len(raw_content)} characters")
            print(f"[DEBUG] Raw response content (first 500 chars): {repr(raw_content[:500])}")
            print(f"[DEBUG] Raw response content (last 200 chars): {repr(raw_content[-200:])}")
            print(f"[DEBUG] Raw response ends with punctuation: {raw_content.strip()[-1] if raw_content.strip() else 'N/A'} in {['.', '!', '?']}")
        else:
            print(f"[DEBUG] Response has no 'content' attribute")
            print(f"[DEBUG] Available attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
        
        # Check for finish reason or truncation indicators
        if hasattr(response, 'finish_reason'):
            print(f"[DEBUG] Finish reason: {response.finish_reason}")
        if hasattr(response, 'usage'):
            print(f"[DEBUG] Token usage: {response.usage}")
        if hasattr(response, 'truncated'):
            print(f"[DEBUG] Truncated flag: {response.truncated}")
        if hasattr(response, 'model'):
            print(f"[DEBUG] Model used: {response.model}")
        
        # Check response object structure
        print(f"[DEBUG] Response object attributes: {[attr for attr in dir(response) if not attr.startswith('_') and not callable(getattr(response, attr, None))]}")
        
        # Try to get text content in different ways
        if hasattr(response, 'get_content_as_string'):
            try:
                content_str = response.get_content_as_string()
                print(f"[DEBUG] get_content_as_string() length: {len(content_str)} characters")
            except Exception as e:
                print(f"[DEBUG] get_content_as_string() error: {e}")
        
        if hasattr(response, 'text'):
            print(f"[DEBUG] response.text length: {len(response.text)} characters")
        
        if hasattr(response, 'message'):
            print(f"[DEBUG] response.message type: {type(response.message)}")
        
        print("="*80 + "\n")
        # ===== END DIAGNOSTIC LOGGING =====
        
        question_text = response.content.strip()
        
        print(f"[DEBUG] After .strip(), question_text length: {len(question_text)} characters")
        print(f"[DEBUG] After .strip(), question_text (first 300 chars): {repr(question_text[:300])}")
        
        # Cleanup logic - but preserve the acknowledgement + question format
        # Remove common prefixes that might interfere
        question_text = re.sub(r'^.*?(?:here\'?s|here is|you could ask|try asking|question:?)\s*', '', question_text, flags=re.IGNORECASE)
        
        # Extract text within quotes if present (but keep the full text if it's already in the right format)
        quoted_match = re.search(r'["\']([^"\']+)["\']', question_text)
        if quoted_match and len(quoted_match.group(1)) > 20:  # Only if it's a substantial quote
            question_text = quoted_match.group(1)
            
        # Extract text after bold markers if present
        bold_match = re.search(r'\*\*([^*]+)\*\*', question_text)
        if bold_match:
            question_text = bold_match.group(1)
            
        # Final cleanup - preserve the format
        question_text = question_text.strip()
        question_text = question_text.strip('"\'')
        
        print(f"[DEBUG] After final cleanup, question_text length: {len(question_text)} characters")
        print(f"[DEBUG] After final cleanup, question_text: {repr(question_text)}")
        
        # Format follow-up questions: Split acknowledgement+preference and question into separate lines
        # New pattern: "Acknowledgement + personal preference" on first line, question on next line
        # Look for patterns like "That's great! I like that too. Do you..." or "Cool! That sounds fun. What do you..."
        # The personal preference ends with a period, then the question starts with a capital letter
        formatted_question = question_text
        
        # Try to detect acknowledgement + personal preference + question pattern
        # Pattern 1: Period followed by space and capital letter (e.g., "That's great! I like that too. Do you...")
        # This handles the case where personal preference ends with period and question starts
        # Check for period pattern first since it's more specific to the new format
        if re.search(r'\.\s+([A-Z][a-z])', question_text):
            # Split on period followed by space and capital letter
            # This will split after the personal preference, before the question
            formatted_question = re.sub(r'\.\s+([A-Z][a-z])', r'.\n\n\1', question_text)
        # Pattern 2: Exclamation mark followed by space and capital letter (e.g., "That's great! Do you...")
        # This handles cases where there's no personal preference or it's very short
        elif re.search(r'([!?])\s+([A-Z][a-z])', question_text):
            # Split on exclamation/question mark followed by space and capital letter
            formatted_question = re.sub(r'([!?])\s+([A-Z][a-z])', r'\1\n\n\2', question_text)
        # Pattern 3: Comma followed by space and capital letter (less common but possible)
        elif re.search(r',\s+([A-Z][a-z])', question_text):
            formatted_question = re.sub(r',\s+([A-Z][a-z])', r',\n\n\1', question_text)
        
        print(f"[DEBUG] After formatting, formatted_question length: {len(formatted_question)} characters")
        print(f"[DEBUG] After formatting, formatted_question: {repr(formatted_question)}")
        print(f"Generated follow-up question: {formatted_question}")
        
        # Save new conversation turn to database
        turn_id = None
        try:
            # Get or create session_topic
            session_topic = get_or_create_session_topic(request.session_id, request.topic)
            if not session_topic:
                print(f"Warning: Failed to get/create session_topic for session {request.session_id}, topic {request.topic}")
            else:
                session_topic_id = str(session_topic['id'])
                # Get current turn count to determine turn_number
                current_turn = get_current_turn(session_topic_id)
                turn_number = 1
                if current_turn:
                    turn_number = current_turn.get('turn_number', 0) + 1
                
                # Create new conversation_turn for follow-up question
                conversation_turn = create_conversation_turn(
                    session_topic_id=session_topic_id,
                    turn_number=turn_number,
                    dimension=dimension,
                    difficulty_level=request.difficulty_level,
                    question=formatted_question
                )
                
                if conversation_turn:
                    turn_id = str(conversation_turn['id'])
                    print(f"Created follow-up conversation turn {turn_number} (ID: {turn_id}) for topic {request.topic}")
                else:
                    print(f"Warning: Failed to create conversation_turn for session_topic {session_topic_id}")
        except Exception as e:
            print(f"Warning: Error saving conversation state to database: {e}")
            import traceback
            traceback.print_exc()
            # Continue even if database save fails
        
        # Generate audio for the question using text-to-speech
        audio_base64 = None
        try:
            # Remove newlines for TTS (keep the text clean for speech)
            clean_text_for_speech = formatted_question.replace('\n\n', '. ').replace('\n', ' ')
            loop = asyncio.get_event_loop()
            audio_base64 = await loop.run_in_executor(
                None,
                text_to_speech_base64,
                clean_text_for_speech
            )
            if audio_base64:
                print(f"Generated audio for follow-up question ({len(audio_base64)} characters base64)")
        except Exception as e:
            print(f"Warning: Failed to generate audio for follow-up question: {e}")
            # Don't fail the request if audio generation fails
            
        return {"question": formatted_question, "dimension": dimension, "audio_base64": audio_base64, "turn_id": turn_id}
    except Exception as e:
        print(f"Error continuing conversation: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/get_conversation_details", response_model=ConversationDetailsResponse)
async def get_conversation_details(request: ConversationDetailsRequest):
    """
    Background endpoint: Generate response options and vocabulary in parallel.
    Called after the question is displayed to load remaining content.
    """
    try:
        # Helper functions for parallel execution
        async def generate_response_options():
            """Generate response options using the response agent"""
            dimension = request.dimension
            difficulty_level = f"Level {request.difficulty_level}"
            
            response_prompt = (
                f"Generate 2 response options for this question: '{request.question}'. "
                f"The dimension is '{dimension}' and difficulty is {difficulty_level}. "
                f"Make responses simple and direct."
            )
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response_result = await loop.run_in_executor(None, response_agent.run, response_prompt)
            response_content = response_result.content.strip()
            
            # Parse the JSON response
            try:
                response_content = re.sub(r'```json\s*', '', response_content)
                response_content = re.sub(r'```\s*', '', response_content)
                response_content = response_content.strip()
                
                json_match = re.search(r'\[.*?\]', response_content, re.DOTALL)
                if json_match:
                    response_content = json_match.group(0)
                
                options = json.loads(response_content)
                
                if not isinstance(options, list) or len(options) != 2:
                    raise ValueError("Response agent did not return exactly 2 options")
                
                options.append("Choose your own response")
                return options
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Warning: Failed to parse response agent output: {e}")
                return [
                    "I like that topic.",
                    "I'm not sure about that.",
                    "Choose your own response"
                ]
        
        async def generate_vocabulary():
            """Generate vocabulary using the vocabulary agent"""
            vocab_prompt = f"Generate a vocabulary word based on this question: '{request.question}'. Make sure the word is relevant to this specific question and topic."
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            vocab_result = await loop.run_in_executor(None, vocabulary_agent.run, vocab_prompt)
            vocab_content = vocab_result.content.strip()
            
            # Parse the JSON response
            try:
                vocab_content = re.sub(r'```json\s*', '', vocab_content)
                vocab_content = re.sub(r'```\s*', '', vocab_content)
                vocab_content = vocab_content.strip()
                
                start_idx = vocab_content.find('{')
                if start_idx != -1:
                    brace_count = 0
                    end_idx = start_idx
                    for i in range(start_idx, len(vocab_content)):
                        if vocab_content[i] == '{':
                            brace_count += 1
                        elif vocab_content[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_idx = i + 1
                                break
                    
                    if brace_count == 0:
                        vocab_content = vocab_content[start_idx:end_idx]
                
                vocab_data = json.loads(vocab_content)
                
                if not all(key in vocab_data for key in ['word', 'type', 'definition', 'example']):
                    raise ValueError("Vocabulary agent did not return all required fields")
                
                return vocab_data
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Warning: Failed to parse vocabulary agent output: {e}")
                fallback_word = request.topic.capitalize() if request.topic else "Topic"
                return {
                    "word": fallback_word,
                    "type": "noun",
                    "definition": f"A subject or theme related to {fallback_word.lower()}.",
                    "example": f"Let's talk about {fallback_word.lower()}."
                }
        
        # Run both agents in parallel
        options, vocab_data = await asyncio.gather(
            generate_response_options(),
            generate_vocabulary()
        )
        
        # Save response options and vocabulary to database
        try:
            if request.turn_id:
                # Save response options
                saved_options = save_response_options(request.turn_id, options)
                if saved_options:
                    print(f"Saved {len(saved_options)} response options for turn {request.turn_id}")
                else:
                    print(f"Warning: Failed to save response options for turn {request.turn_id}")
                
                # Save vocabulary word
                saved_vocab = save_vocabulary_word(
                    conversation_turn_id=request.turn_id,
                    word=vocab_data['word'],
                    word_type=vocab_data['type'],
                    definition=vocab_data['definition'],
                    example=vocab_data['example']
                )
                if saved_vocab:
                    print(f"Saved vocabulary word '{vocab_data['word']}' for turn {request.turn_id}")
                else:
                    print(f"Warning: Failed to save vocabulary word for turn {request.turn_id}")
            else:
                print(f"Warning: No turn_id provided, skipping database save")
        except Exception as e:
            print(f"Warning: Error saving conversation details to database: {e}")
            import traceback
            traceback.print_exc()
            # Continue even if database save fails
        
        return {
            "response_options": options,
            "vocabulary": vocab_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating conversation details: {str(e)}")

@app.post("/api/text_to_speech", response_model=TextToSpeechResponse)
async def generate_text_to_speech(request: TextToSpeechRequest):
    """
    Generate speech from text using OpenAI's TTS.
    This endpoint can be called on-demand to regenerate audio for a question.
    """
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Clean text for TTS (remove extra newlines)
        clean_text = request.text.replace('\n\n', '. ').replace('\n', ' ').strip()
        
        # Generate audio
        loop = asyncio.get_event_loop()
        try:
            audio_base64 = await loop.run_in_executor(
                None,
                text_to_speech_base64,
                clean_text,
                request.voice,
                request.model,
                request.format
            )
            
            if not audio_base64:
                raise HTTPException(status_code=500, detail="Failed to generate audio: TTS function returned None. Check backend logs for details.")
        except Exception as executor_error:
            print(f"Error in executor for text-to-speech: {executor_error}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Error generating speech in executor: {str(executor_error)}")
        
        return {
            "audio_base64": audio_base64,
            "format": request.format
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating text-to-speech: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")

@app.post("/api/analyze_speech", response_model=SpeechAnalysisResponse)
async def analyze_speech(request: SpeechAnalysisRequest):
    """
    Analyze speech transcript from the teen.
    This endpoint accepts a transcript (text) and analyzes it.
    For audio file analysis, use /api/process-audio instead.
    """
    try:
        if not request.expected_response:
            raise HTTPException(status_code=400, detail="expected_response is required")
        
        # This endpoint is for text-based analysis only
        # For audio analysis, use /api/process-audio
        raise HTTPException(status_code=400, detail="This endpoint requires audio. Use /api/process-audio for audio file uploads.")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing speech: {str(e)}")

@app.post("/api/process-audio", response_model=SpeechAnalysisResponse)
async def process_audio(
    audio: UploadFile = File(...),
    expected_response: Optional[str] = Form(None),
    turn_id: Optional[str] = Form(None)  # Conversation turn ID to save speech analysis
):
    """
    Process uploaded audio file.
    Transcribes the audio, analyzes it, and provides feedback.
    Saves audio to temporary directory, processes it, and deletes it immediately after.
    """
    temp_file_path = None
    converted_file_path = None
    try:
        print(f"Received audio file: {audio.filename}, content_type: {audio.content_type}")
        
        # Create temporary file
        # Determine file extension from content type or filename
        file_extension = '.webm'  # default
        if audio.content_type:
            if 'webm' in audio.content_type.lower():
                file_extension = '.webm'
            elif 'mp3' in audio.content_type.lower():
                file_extension = '.mp3'
            elif 'wav' in audio.content_type.lower():
                file_extension = '.wav'
            elif 'm4a' in audio.content_type.lower():
                file_extension = '.m4a'
        elif audio.filename:
            file_extension = Path(audio.filename).suffix or '.webm'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension, dir=tempfile.gettempdir()) as temp_file:
            temp_file_path = temp_file.name
            # Write uploaded audio to temp file
            content = await audio.read()
            print(f"Audio file size: {len(content)} bytes")
            temp_file.write(content)
            temp_file.flush()
        
        # Validate file size (must be at least 1KB for a 1+ second recording)
        file_size = os.path.getsize(temp_file_path)
        print(f"Saved temp file size: {file_size} bytes")
        
        if file_size < 1000:  # Less than 1KB is likely too short
            raise HTTPException(status_code=400, detail="Audio file too short. Please record for at least 1 second.")
        
        # Convert audio format if needed (OpenAI only supports wav and mp3)
        audio_format = file_extension.lstrip('.').lower()
        print(f"Detected audio format: {audio_format}")
        
        # Convert webm or other unsupported formats to wav
        if audio_format not in ['wav', 'mp3']:
            if not FFMPEG_AVAILABLE:
                raise HTTPException(
                    status_code=500,
                    detail="Audio conversion requires ffmpeg, which is not available on the server. Please install ffmpeg and add it to your PATH."
                )
            
            print(f"Converting {audio_format} to wav format using ffmpeg...")
            
            # Create new temp file with .wav extension
            converted_file_path = temp_file_path.rsplit('.', 1)[0] + '.wav'
            print(f"Exporting to: {converted_file_path}")
            
            # Use our direct ffmpeg function
            success = convert_audio_to_wav(temp_file_path, converted_file_path)
            
            if success:
                print(f"Successfully exported to wav format")
                # Delete original file and update temp_file_path
                if converted_file_path != temp_file_path:
                    try:
                        os.unlink(temp_file_path)
                        print(f"Deleted original file: {temp_file_path}")
                    except Exception as e:
                        print(f"Warning: Could not delete original file: {e}")
                    temp_file_path = converted_file_path
                
                audio_format = 'wav'
                print(f"Conversion complete. Using file: {temp_file_path} with format: {audio_format}")
            else:
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to convert audio file using ffmpeg. Check server logs for details."
                )
        else:
            print(f"Audio format {audio_format} is supported, no conversion needed.")
        
        # Process audio using speech_analysis_agent
        loop = asyncio.get_event_loop()
        
        # Use analyze_speech_with_audio function
        # temp_file_path now points to the correct file (converted if needed, original otherwise)
        analysis_result = await loop.run_in_executor(
            None,
            analyze_speech_with_audio,
            speech_analysis_agent,
            None,  # audio_data
            temp_file_path,  # audio_filepath (use temp_file_path which may be converted)
            audio_format,
            expected_response
        )
        
        # Parse the JSON response
        try:
            analysis_content = analysis_result.strip()
            analysis_content = re.sub(r'```json\s*', '', analysis_content)
            analysis_content = re.sub(r'```\s*', '', analysis_content)
            analysis_content = analysis_content.strip()
            
            # Extract JSON object
            start_idx = analysis_content.find('{')
            if start_idx != -1:
                brace_count = 0
                end_idx = start_idx
                for i in range(start_idx, len(analysis_content)):
                    if analysis_content[i] == '{':
                        brace_count += 1
                    elif analysis_content[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                
                if brace_count == 0:
                    analysis_content = analysis_content[start_idx:end_idx]
            
            analysis_data = json.loads(analysis_content)
            
            # Validate required fields
            required_fields = ['transcript', 'clarity_score', 'feedback', 'strengths', 'suggestions', 'pace_wpm', 'filler_words']
            if not all(key in analysis_data for key in required_fields):
                raise ValueError("Speech analysis agent did not return all required fields")
            
            # Ensure wer_estimate is present (can be null)
            if 'wer_estimate' not in analysis_data:
                analysis_data['wer_estimate'] = None
            
            # Save speech analysis to database if turn_id provided
            if turn_id:
                try:
                    updated_turn = update_conversation_turn_with_speech_analysis(
                        turn_id=turn_id,
                        transcript=analysis_data['transcript'],
                        clarity_score=analysis_data['clarity_score'],
                        wer_estimate=analysis_data.get('wer_estimate'),
                        pace_wpm=analysis_data['pace_wpm'],
                        filler_words=analysis_data['filler_words'],
                        feedback=analysis_data['feedback'],
                        strengths=analysis_data['strengths'],
                        suggestions=analysis_data['suggestions']
                    )
                    if updated_turn:
                        print(f"Saved speech analysis for turn {turn_id}")
                    else:
                        print(f"Warning: Failed to save speech analysis for turn {turn_id}")
                except Exception as e:
                    print(f"Warning: Error saving speech analysis to database: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continue even if database save fails
            else:
                print(f"Warning: No turn_id provided, skipping speech analysis database save")
            
            print(f"Audio processed successfully, file size: {file_size} bytes")
            return analysis_data
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Failed to parse speech analysis output: {e}")
            import traceback
            traceback.print_exc()
            # Fallback response
            return {
                "transcript": "[Transcription failed]",
                "wer_estimate": None,
                "clarity_score": 0.75,
                "pace_wpm": 120,
                "filler_words": [],
                "feedback": "Great effort! Keep practicing to improve your communication skills.",
                "strengths": ["You're making progress with your speech practice."],
                "suggestions": ["Continue practicing to build confidence."]
            }
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = str(e)
        print(f"\n{'='*60}")
        print(f"ERROR processing audio: {error_detail}")
        print(f"{'='*60}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        # Include more context in the error message
        error_msg = f"Error processing audio: {error_detail}"
        if "transcribe" in error_detail.lower() or "transcription" in error_detail.lower():
            error_msg += "\n\nThis might be a transcription issue. Check:\n- OpenAI API key is valid\n- Model 'gpt-4o-audio-preview' is available\n- Audio file format is supported (wav, mp3)"
        raise HTTPException(status_code=500, detail=error_msg)
    finally:
        # Always delete the temporary file
        # Note: temp_file_path may point to converted file if conversion occurred
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                print(f"Deleted temp file: {temp_file_path}")
            except Exception as e:
                print(f"Warning: Failed to delete temp file {temp_file_path}: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
