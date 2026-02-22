from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import threading
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
    get_current_turn, get_last_conversation_turn,
    get_conversation_history_for_user_topic,
    get_dimension_history_for_user_topic,
    get_recent_speech_metrics_for_user_topic,
    analyze_speech_trends
)
from supabase import create_client
import os
from tools.text_to_speech import text_to_speech_base64

# Initialize Supabase client for direct database access
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY') or os.getenv('SUPABASE_KEY')
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"[OK] Supabase client initialized in main.py")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Supabase client in main.py: {e}")
        supabase = None

# ============================================================================
# Pre-generation Cache for Next Questions
# ============================================================================
# Simple in-memory cache for pre-generated questions
# Cache key format: f"{user_id}_{topic}_{previous_turn_id}"
question_cache: Dict[str, Dict[str, Any]] = {}
cache_expiry: Dict[str, datetime] = {}
cache_lock = threading.Lock()  # Thread-safe access

# Track which first questions are currently being pre-generated
# Key format: f"first_q_{user_id}_{topic}"
first_question_in_progress: Dict[str, asyncio.Task] = {}
first_question_lock = threading.Lock()

# ============================================================================
# Database Query Cache
# ============================================================================
# Cache for database query results to avoid repeated queries
# Cache key format: f"db_{query_type}_{user_id}_{topic}"
db_query_cache: Dict[str, Dict[str, Any]] = {}
db_cache_expiry: Dict[str, datetime] = {}
db_cache_lock = threading.Lock()  # Thread-safe access
DB_CACHE_TTL = timedelta(seconds=30)  # 30 second TTL for database queries

def get_db_cache_key(query_type: str, user_id: str, topic: str) -> str:
    """Generate cache key for database query"""
    normalized_topic = (topic or "").lower().strip()
    return f"db_{query_type}_{user_id}_{normalized_topic}"

def get_cached_db_query(cache_key: str) -> Optional[Any]:
    """Retrieve cached database query result if it exists and hasn't expired"""
    with db_cache_lock:
        if cache_key in db_query_cache:
            if db_cache_expiry.get(cache_key, datetime.now()) > datetime.now():
                print(f"[DB-CACHE HIT] Retrieved cached query for key: {cache_key}")
                return db_query_cache[cache_key]
            else:
                # Expired, clean up
                del db_query_cache[cache_key]
                del db_cache_expiry[cache_key]
                print(f"[DB-CACHE] Expired entry removed for key: {cache_key}")
        return None

def cache_db_query(cache_key: str, result: Any):
    """Cache a database query result with TTL"""
    with db_cache_lock:
        db_query_cache[cache_key] = result
        db_cache_expiry[cache_key] = datetime.now() + DB_CACHE_TTL
        print(f"[DB-CACHE] Cached query result for key: {cache_key} (expires in {DB_CACHE_TTL.total_seconds()}s)")

def clear_db_cache_for_user(user_id: str, topic: str = None):
    """Clear database query cache for a user (optionally filtered by topic)"""
    with db_cache_lock:
        normalized_topic = topic.lower().strip() if topic else None
        keys_to_remove = []
        for key in db_query_cache.keys():
            if normalized_topic:
                if key.startswith(f"db_") and f"_{user_id}_{normalized_topic}" in key:
                    keys_to_remove.append(key)
            else:
                if key.startswith(f"db_") and f"_{user_id}_" in key:
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del db_query_cache[key]
            if key in db_cache_expiry:
                del db_cache_expiry[key]
        
        if keys_to_remove:
            print(f"[DB-CACHE] Cleared {len(keys_to_remove)} entries for user {user_id}" + (f", topic {topic}" if topic else ""))

def summarize_conversation_history(conversation_history: List[Dict[str, Any]], max_turns: int = 3) -> str:
    """
    Rule-based summarization of conversation history.
    Extracts key information from user responses and summarizes questions.
    
    Args:
        conversation_history: List of conversation turn dictionaries
        max_turns: Maximum number of recent turns to summarize (default: 3)
    
    Returns:
        Concise summary string of conversation history
    """
    if not conversation_history:
        return ""
    
    # Get last N turns (most recent first)
    recent_turns = conversation_history[-max_turns:] if len(conversation_history) > max_turns else conversation_history
    
    # Extract key information from user responses
    user_points = []
    question_themes = []
    
    for turn in reversed(recent_turns):  # Process in chronological order
        question = (turn.get('question') or '').strip()
        user_response = (turn.get('user_response') or '').strip() or (turn.get('transcript') or '').strip()
        
        if user_response:
            # Extract key points from user response (first 100 chars, remove filler)
            response_summary = user_response[:100].strip()
            # Remove common filler phrases
            response_summary = re.sub(r'^(um|uh|like|you know|i mean|well|so)\s*,?\s*', '', response_summary, flags=re.IGNORECASE)
            if response_summary:
                user_points.append(response_summary)
        
        if question:
            # Extract question theme (first 80 chars, remove common prefixes)
            question_theme = question[:80].strip()
            question_theme = re.sub(r'^(here\'?s|here is|you could ask|try asking|question:?)\s*', '', question_theme, flags=re.IGNORECASE)
            if question_theme:
                question_themes.append(question_theme)
    
    # Build concise summary
    summary_parts = []
    
    if user_points:
        # Combine user points into a single summary
        if len(user_points) == 1:
            summary_parts.append(f"User said: {user_points[0]}")
        elif len(user_points) == 2:
            summary_parts.append(f"User mentioned: {user_points[0]}; {user_points[1]}")
        else:
            # For 3+ points, summarize (show first 2, count rest)
            summary_parts.append(f"User discussed: {user_points[0]}, {user_points[1]}, and {len(user_points)-2} more topics")
    
    # Always return a summary, even if minimal
    if summary_parts:
        return "History: " + ". ".join(summary_parts)
    elif question_themes:
        # If no user responses but questions exist
        return f"History: {len(question_themes)} previous questions asked"
    else:
        # Fallback
        return "History: previous conversation"

async def get_user_topic_data_parallel(user_id: str, topic: str) -> tuple:
    """
    Fetch conversation history, dimension history, and speech metrics in parallel.
    Uses caching to avoid repeated queries.
    
    Returns:
        (conversation_history, dimension_history, speech_metrics)
    """
    # Check cache first
    history_key = get_db_cache_key("history", user_id, topic)
    dimension_key = get_db_cache_key("dimensions", user_id, topic)
    speech_key = get_db_cache_key("speech", user_id, topic)
    
    cached_history = get_cached_db_query(history_key)
    cached_dimensions = get_cached_db_query(dimension_key)
    cached_speech = get_cached_db_query(speech_key)
    
    # Initialize results with cached values or None
    conversation_history = cached_history
    dimension_history = cached_dimensions
    speech_metrics = cached_speech
    
    # Build list of tasks for queries that need to be executed
    tasks = []
    task_info = []  # List of (query_type, cache_key) tuples
    
    # History query
    if cached_history is None:
        tasks.append(asyncio.to_thread(get_conversation_history_for_user_topic, user_id, topic, 5))
        task_info.append(("history", history_key))
    
    # Dimension query
    if cached_dimensions is None:
        tasks.append(asyncio.to_thread(get_dimension_history_for_user_topic, user_id, topic, 10))
        task_info.append(("dimensions", dimension_key))
    
    # Speech metrics query
    if cached_speech is None:
        tasks.append(asyncio.to_thread(get_recent_speech_metrics_for_user_topic, user_id, topic, 5))
        task_info.append(("speech", speech_key))
    
    # Execute queries in parallel (only for uncached queries)
    if tasks:
        print(f"[DB-QUERY] Executing {len(tasks)} database queries in parallel for user {user_id}, topic {topic}...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and cache them
        for i, (query_type, cache_key) in enumerate(task_info):
            result = results[i]
            
            if isinstance(result, Exception):
                print(f"[DB-QUERY] Error in {query_type} query: {result}")
                # Use empty result on error
                result = [] if query_type != "dimensions" else []
            else:
                # Cache the result
                cache_db_query(cache_key, result)
            
            # Assign result to appropriate variable
            if query_type == "history":
                conversation_history = result
            elif query_type == "dimensions":
                dimension_history = result
            elif query_type == "speech":
                speech_metrics = result
    else:
        # All queries were cached
        print(f"[DB-QUERY] All queries retrieved from cache for user {user_id}, topic {topic}")
    
    return conversation_history, dimension_history, speech_metrics

def get_cache_key(user_id: str, topic: str, previous_turn_id: str) -> str:
    """Generate cache key for pre-generated question"""
    # Normalize topic to lowercase for consistent cache keys
    normalized_topic = (topic or "").lower().strip()
    return f"{user_id}_{normalized_topic}_{previous_turn_id}"

def get_first_question_cache_key(user_id: str, topic: str) -> str:
    """Generate cache key for pre-generated first question (topic-level, not turn-based)"""
    normalized_topic = (topic or "").lower().strip()
    return f"first_q_{user_id}_{normalized_topic}"

def cache_first_question(cache_key: str, question_data: Dict[str, Any]):
    """Cache a pre-generated first question with 30-minute expiry"""
    with cache_lock:
        question_cache[cache_key] = question_data
        cache_expiry[cache_key] = datetime.now() + timedelta(minutes=30)
        print(f"[FIRST-Q CACHE] Cached first question for key: {cache_key} (expires in 30 minutes)")

def get_cached_first_question(cache_key: str) -> Optional[Dict[str, Any]]:
    """Retrieve cached first question if it exists and hasn't expired"""
    with cache_lock:
        if cache_key in question_cache:
            # Check expiry
            if cache_expiry.get(cache_key, datetime.now()) > datetime.now():
                cached = question_cache[cache_key]
                # Don't remove from cache (can be reused multiple times)
                print(f"[FIRST-Q CACHE HIT] Retrieved pre-generated first question for key: {cache_key}")
                return cached
            else:
                # Expired, clean up
                del question_cache[cache_key]
                del cache_expiry[cache_key]
                print(f"[FIRST-Q CACHE] Expired entry removed for key: {cache_key}")
        return None

def cache_question(cache_key: str, question_data: Dict[str, Any]):
    """Cache a pre-generated question with 5-minute expiry"""
    with cache_lock:
        question_cache[cache_key] = question_data
        cache_expiry[cache_key] = datetime.now() + timedelta(minutes=5)
        print(f"[CACHE] Cached question for key: {cache_key} (expires in 5 minutes)")

def get_cached_question(cache_key: str) -> Optional[Dict[str, Any]]:
    """Retrieve cached question if it exists and hasn't expired"""
    with cache_lock:
        if cache_key in question_cache:
            # Check expiry
            if cache_expiry.get(cache_key, datetime.now()) > datetime.now():
                cached = question_cache[cache_key]
                # Remove from cache after retrieval (single-use)
                del question_cache[cache_key]
                del cache_expiry[cache_key]
                print(f"[CACHE HIT] Retrieved pre-generated question for key: {cache_key}")
                return cached
            else:
                # Expired, clean up
                del question_cache[cache_key]
                del cache_expiry[cache_key]
                print(f"[CACHE] Expired entry removed for key: {cache_key}")
        return None

def clear_cache_for_user(user_id: str, topic: str = None):
    """Clear cache entries for a user (optionally filtered by topic)"""
    with cache_lock:
        keys_to_remove = []
        normalized_topic = topic.lower().strip() if topic else None
        for key in question_cache.keys():
            if normalized_topic:
                if key.startswith(f"{user_id}_{normalized_topic}_"):
                    keys_to_remove.append(key)
            else:
                if key.startswith(f"{user_id}_"):
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del question_cache[key]
            if key in cache_expiry:
                del cache_expiry[key]
        
        if keys_to_remove:
            print(f"[CACHE] Cleared {len(keys_to_remove)} entries for user {user_id}" + (f", topic {topic}" if topic else ""))

def cleanup_expired_cache():
    """Remove expired cache entries (can be called periodically)"""
    with cache_lock:
        now = datetime.now()
        expired_keys = [key for key, expiry in cache_expiry.items() if expiry <= now]
        for key in expired_keys:
            if key in question_cache:
                del question_cache[key]
            del cache_expiry[key]
        if expired_keys:
            print(f"[CACHE] Cleaned up {len(expired_keys)} expired entries")

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
    reasoning: Optional[str] = None  # Orchestrator's reasoning for dimension selection

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
    user_response: Optional[str] = None  # User's previous response for context-aware options

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

class PreGenerationStatusRequest(BaseModel):
    user_id: str
    topic: str
    previous_turn_id: str

class PreGenerationStatusResponse(BaseModel):
    ready: bool
    message: str

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
        # Validate and normalize username
        if not request.username:
            raise HTTPException(status_code=400, detail="Username is required")
        username = (request.username or "").strip()
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
        
        # Check if returning user (check for previous conversation activity)
        returning = is_returning_user(user_id)
        last_topic = None
        
        if returning:
            # Get last topic for returning user
            last_topic_data = get_last_topic_for_user(user_id)
            if last_topic_data and 'topic_name' in last_topic_data:
                last_topic = last_topic_data['topic_name']
                print(f"Returning user '{username}' (ID: {user_id}) - last topic: {last_topic}")
        else:
            print(f"First-time user '{username}' (ID: {user_id})")
        
        # Create a new session for this login
        session = create_session(user_id)
        session_id = str(session['id']) if session else None
        
        print(f"User logged in: {username} (ID: {user_id}) at {login_timestamp}")
        if session_id:
            print(f"Created session: {session_id}")
        
        # Clear any stale pre-generation tasks from previous sessions
        with first_question_lock:
            # Remove any stale/done tasks
            stale_keys = [k for k, task in first_question_in_progress.items() if task.done()]
            for key in stale_keys:
                del first_question_in_progress[key]
            if stale_keys:
                print(f"[LOGIN] Cleaned up {len(stale_keys)} stale pre-generation tasks")
        
        # Trigger pre-generation of first questions for all topics in the background
        # This allows instant topic selection without waiting for question generation
        try:
            asyncio.create_task(pre_generate_all_first_questions(user_id, difficulty_level=1))
            print(f"[LOGIN] Triggered background pre-generation of first questions for all topics")
        except Exception as e:
            print(f"[LOGIN] Warning: Failed to trigger pre-generation: {e}")
            # Don't fail login if pre-generation fails
        
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
        # Validate and normalize user_id
        if not request.user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        user_id = (request.user_id or "").strip()
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
        
        # Case-insensitive comparison for topic name
        if not last_topic_data:
            raise HTTPException(
                status_code=404,
                detail=f"No previous conversation found for user '{user_id}'"
            )
        
        stored_topic_name = last_topic_data.get('topic_name', '').strip()
        requested_topic_name = topic_name.strip()
        
        if stored_topic_name.lower() != requested_topic_name.lower():
            raise HTTPException(
                status_code=404,
                detail=f"No previous conversation found for topic '{topic_name}'. Last topic was '{stored_topic_name}'"
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

@app.post("/api/check_pre_generation_status", response_model=PreGenerationStatusResponse)
async def check_pre_generation_status(request: PreGenerationStatusRequest):
    """
    Check if a pre-generated question is ready in the cache.
    Used by frontend to determine when to enable the "Continue Chat" button.
    """
    try:
        cache_key = get_cache_key(request.user_id, request.topic, request.previous_turn_id)
        
        # Check cache (this doesn't remove the entry, just checks if it exists)
        with cache_lock:
            if cache_key in question_cache:
                # Check if expired
                if cache_expiry.get(cache_key, datetime.now()) > datetime.now():
                    print(f"[STATUS] Pre-generation ready for key: {cache_key}")
                    return {
                        "ready": True,
                        "message": "Question is ready"
                    }
                else:
                    # Expired, clean up
                    del question_cache[cache_key]
                    if cache_key in cache_expiry:
                        del cache_expiry[cache_key]
                    print(f"[STATUS] Pre-generation expired for key: {cache_key}")
        
        print(f"[STATUS] Pre-generation not ready for key: {cache_key}")
        return {
            "ready": False,
            "message": "Question is still being generated"
        }
    except Exception as e:
        print(f"[STATUS] Error checking pre-generation status: {e}")
        import traceback
        traceback.print_exc()
        return {
            "ready": False,
            "message": f"Error checking status: {str(e)}"
        }

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
    Uses "Basic Preferences" dimension for the first question on any topic.
    For returning users, retrieves conversation history and generates a contextual question.
    """
    try:
        user_id = request.user_id
        topic = request.topic
        
        # Validate required fields
        if not topic or not topic.strip():
            raise HTTPException(status_code=400, detail="Topic is required and cannot be empty")
        if not user_id or not user_id.strip():
            raise HTTPException(status_code=400, detail="User ID is required and cannot be empty")
        
        topic = topic.strip()  # Normalize topic
        
        # Clear caches for this user/topic when starting a new conversation
        # (in case user changed topic or wants fresh start)
        clear_cache_for_user(user_id, topic)
        clear_db_cache_for_user(user_id, topic)
        
        # Check if this is the first question for this topic using database
        # Fallback to True if database is not available
        try:
            is_first_question = is_first_question_for_topic(user_id, topic)
        except Exception as e:
            print(f"Warning: Error checking first question in database: {e}. Defaulting to first question.")
            is_first_question = True
        
        # If this is a first question, check if we have a pre-generated cached version
        if is_first_question:
            cache_key = get_first_question_cache_key(user_id, topic)
            cached_first_question = get_cached_first_question(cache_key)
            
            # If not cached, check if pre-generation is in progress and wait for it
            if not cached_first_question:
                with first_question_lock:
                    if cache_key in first_question_in_progress:
                        task = first_question_in_progress[cache_key]
                        if not task.done():
                            print(f"[CACHE WAIT] Pre-generation in progress for topic: {topic}, waiting...")
                            try:
                                # Wait up to 10 seconds for pre-generation to complete
                                cached_first_question = await asyncio.wait_for(task, timeout=10.0)
                                if cached_first_question:
                                    print(f"[CACHE WAIT] Pre-generation completed, using cached question")
                            except asyncio.TimeoutError:
                                print(f"[CACHE WAIT] Timeout waiting for pre-generation, falling back to normal generation")
                                cached_first_question = None
                            except Exception as e:
                                print(f"[CACHE WAIT] Error waiting for pre-generation: {e}, falling back to normal generation")
                                cached_first_question = None
            
            if cached_first_question:
                print(f"[CACHE HIT] Using pre-generated first question for topic: {topic}")
                # We have a cached first question - use it!
                question_text = cached_first_question['question']
                dimension = cached_first_question['dimension']
                reasoning = cached_first_question.get('reasoning')
                orchestrator_difficulty = cached_first_question.get('difficulty_level', request.difficulty_level)
                audio_base64 = cached_first_question.get('audio_base64')
                
                # Still need to create the database turn
                turn_id = None
                try:
                    if supabase:
                        session_topic = get_or_create_session_topic(request.session_id, topic)
                        if session_topic:
                            session_topic_id = str(session_topic['id'])
                            current_turn = get_current_turn(session_topic_id)
                            turn_number = 1
                            if current_turn:
                                turn_number = current_turn.get('turn_number', 0) + 1
                            
                            conversation_turn = create_conversation_turn(
                                session_topic_id=session_topic_id,
                                turn_number=turn_number,
                                dimension=dimension,
                                difficulty_level=orchestrator_difficulty,
                                question=question_text
                            )
                            
                            if conversation_turn:
                                turn_id = str(conversation_turn['id'])
                                print(f"Created conversation turn {turn_number} (ID: {turn_id}) for topic {topic} (from cache)")
                except Exception as e:
                    print(f"Warning: Error saving conversation state to database: {e}")
                    # Continue even if database save fails
                
                return {
                    "question": question_text,
                    "dimension": dimension,
                    "audio_base64": audio_base64,
                    "turn_id": turn_id,
                    "reasoning": reasoning
                }
        
        # OPTIMIZATION: Skip history retrieval for first questions (even for returning users)
        # First questions should be simple and welcoming, no need for complex context
        conversation_history = []
        dimension_history = []
        speech_metrics = []
        speech_trends = None
        history_context = ""
        
        # Only fetch history if this is NOT a first question
        if not is_first_question:
            try:
                conversation_history, dimension_history, speech_metrics = await get_user_topic_data_parallel(user_id, topic)
                speech_trends = analyze_speech_trends(speech_metrics)
                print(f"Retrieved {len(conversation_history)} conversation turns, {len(dimension_history)} dimensions, and {len(speech_metrics)} speech metrics for user {user_id}, topic {topic}")
                if speech_trends:
                    print(f"Speech trends: clarity={speech_trends['clarity_trend']}, pace={speech_trends['pace_trend']}, confidence={speech_trends['confidence_level']}")
                # Build history context only for non-first questions
                history_context = summarize_conversation_history(conversation_history, max_turns=5) if conversation_history else ""
            except Exception as e:
                print(f"Warning: Error retrieving conversation/dimension/speech history: {e}. Continuing without history.")
                import traceback
                traceback.print_exc()
                conversation_history = []
                dimension_history = []
                speech_metrics = []
                speech_trends = None
                history_context = ""
        
        # Create orchestrator prompt with topic and context
        if is_first_question:
            print(f"[ORCHESTRATOR] First question for user {user_id} on topic {topic} (skipping history for speed)")
            
            # Build minimal JSON context for first questions (no history needed)
            context_json = {
                "t": str(topic)[:20],  # topic shortened
                "d": int(request.difficulty_level),  # diff
                "f": True  # is_first
            }
            
            # Short task instructions (OPTIMIZED - minimal prompt for first questions)
            orchestrator_prompt = f"""Gen first Q for teen.

Ctx: {json.dumps(context_json, separators=(',', ':'))}

Task: Select "Basic Preferences" → Gen Q (teen-appropriate, positive, simple)

Return JSON: {{"question":"...","dimension":"Basic Preferences","reasoning":"...","difficulty_level":1}}"""
        else:
            # Build speech performance context if available
            speech_context = ""
            if speech_trends:
                recent_clarity_scores = [m.get('clarity_score', 0.0) for m in speech_metrics[:3] if m.get('clarity_score') is not None]
                avg_clarity = speech_trends['average_clarity']
                recent_clarity = speech_trends['recent_clarity']
                avg_pace = speech_trends['average_pace']
                speech_context = f"Speech: clarity_trend={speech_trends['clarity_trend']}, clarity_avg={avg_clarity:.2f}, clarity_recent={recent_clarity:.2f}, pace_trend={speech_trends['pace_trend']}, pace_avg={avg_pace:.0f}wpm, conf={speech_trends['confidence_level']}, recent_scores={recent_clarity_scores}"
            elif speech_metrics:
                recent_clarity = speech_metrics[0].get('clarity_score') if speech_metrics else None
                if recent_clarity is not None:
                    speech_context = f"Speech: clarity_recent={recent_clarity:.2f} (limited data)"
            
            # Check if same dimension used 2+ times in a row
            dimension_warning = ""
            if dimension_history and len(dimension_history) >= 2:
                last_two = dimension_history[:2]
                if last_two[0] == last_two[1]:
                    dimension_warning = f"⚠️ CRITICAL: Last 2 turns used '{last_two[0]}'. You MUST switch to a DIFFERENT dimension now!"
                    print(f"[ORCHESTRATOR] WARNING: Same dimension '{last_two[0]}' used 2 times in a row - forcing switch")
            
            dimension_context = ""
            if dimension_history:
                dimension_context = f"Recently used dimensions: {', '.join(dimension_history[:5])}\n"
                if dimension_warning:
                    dimension_context += dimension_warning + "\n"
                else:
                    dimension_context += "Avoid repeating these dimensions unless it's a natural continuation.\n"
            
            print(f"[ORCHESTRATOR] Continuing conversation for user {user_id} on topic {topic}")
            
            # Build JSON context (Option 4: structured data)
            context_json = {
                "user_id": str(user_id) if user_id else "",
                "topic": str(topic) if topic else "",
                "diff": int(request.difficulty_level),
                "is_first": False,
                "history": str(history_context) if history_context else None,
                "dims_used": [str(d) for d in (dimension_history[:3] if dimension_history else [])],
                "speech": str(speech_context) if speech_context else None
            }
            
            # Short task instructions with dimension switching enforcement
            dims_list = dimension_history[:3] if dimension_history else []
            dims_str = ', '.join(dims_list) if dims_list else 'none'
            switch_instruction = dimension_warning if dimension_warning else f"Select dimension (avoid: {dims_str})"
            
            orchestrator_prompt = f"""Gen Q for teen. Follow system instructions for topic-based reasoning and continue conversation.

Ctx: {json.dumps(context_json, separators=(',', ':'))}

Task: Analyze topic+history → {switch_instruction} → Adjust difficulty → Gen Q (build on history, don't repeat, teen-appropriate)

Return JSON: {{"question": "...", "dimension": "...", "reasoning": "...", "difficulty_level": 1}}"""
        
        # Use orchestrator instead of direct agent call
        print(f"[ORCHESTRATOR] Calling orchestrator for topic: {topic}, user: {user_id}")
        loop = asyncio.get_event_loop()
        reasoning = None  # Initialize reasoning
        orchestrator_response = None
        max_retries = 3
        retry_delay = 2  # Start with 2 seconds
        
        for attempt in range(max_retries):
            try:
                orchestrator_response = await loop.run_in_executor(
                    None,
                    orchestrator.run,
                    orchestrator_prompt
                )
                
                if not orchestrator_response or not orchestrator_response.content:
                    raise ValueError("Orchestrator returned empty response")
                
                print(f"[ORCHESTRATOR] Received response (length: {len(orchestrator_response.content)} chars)")
                print(f"[ORCHESTRATOR] Raw response preview: {orchestrator_response.content[:200]}...")
                break  # Success, exit retry loop
            except Exception as e:
                error_str = str(e)
                # Check if it's a rate limit error
                if "rate limit" in error_str.lower() or "tpm" in error_str.lower() or "rpm" in error_str.lower():
                    if attempt < max_retries - 1:
                        # Extract wait time from error if available
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        print(f"[ORCHESTRATOR] Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise HTTPException(
                            status_code=429,
                            detail=f"Rate limit exceeded. Please try again in a few moments."
                        )
                else:
                    # Not a rate limit error, re-raise
                    raise
        
        try:
            
            # Parse JSON response from orchestrator
            orchestrator_content = (orchestrator_response.content or '').strip()
            
            # Remove markdown code blocks if present
            orchestrator_content = re.sub(r'```json\s*', '', orchestrator_content)
            orchestrator_content = re.sub(r'```\s*', '', orchestrator_content)
            orchestrator_content = orchestrator_content.strip()
            
            # Extract JSON object
            start_idx = orchestrator_content.find('{')
            if start_idx == -1:
                raise ValueError("No JSON object found in orchestrator response")
            
            brace_count = 0
            end_idx = start_idx
            for i in range(start_idx, len(orchestrator_content)):
                if orchestrator_content[i] == '{':
                    brace_count += 1
                elif orchestrator_content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            if brace_count != 0:
                raise ValueError("Unclosed JSON object in orchestrator response")
            
            orchestrator_content = orchestrator_content[start_idx:end_idx]
            
            # Parse JSON
            orchestrator_data = json.loads(orchestrator_content)
            
            # Validate required fields
            if 'question' not in orchestrator_data or not orchestrator_data.get('question'):
                raise ValueError("Orchestrator response missing 'question' field")
            if 'dimension' not in orchestrator_data or not orchestrator_data.get('dimension'):
                raise ValueError("Orchestrator response missing 'dimension' field")
            
            # Extract data (with None safety)
            question_text = (orchestrator_data.get('question') or '').strip()
            dimension = (orchestrator_data.get('dimension') or '').strip()
            reasoning = orchestrator_data.get('reasoning', '') or None
            if reasoning:
                reasoning = str(reasoning).strip() or None
            orchestrator_difficulty = orchestrator_data.get('difficulty_level', request.difficulty_level)
            
            # Validate that we have required fields
            if not question_text:
                raise ValueError("Orchestrator response 'question' field is empty or None")
            if not dimension:
                raise ValueError("Orchestrator response 'dimension' field is empty or None")
            
            # Validate dimension (log warning if not in list, but allow flexibility)
            if dimension not in DIMENSIONS and dimension != "Basic Preferences":
                print(f"[ORCHESTRATOR] WARNING: Dimension '{dimension}' not in standard list. Allowing flexibility.")
            else:
                print(f"[ORCHESTRATOR] Dimension '{dimension}' validated against standard list.")
            
            # Log detailed orchestrator decisions
            print(f"[ORCHESTRATOR] ===== DECISION LOG =====")
            print(f"[ORCHESTRATOR] Topic: {topic}")
            print(f"[ORCHESTRATOR] Is First Question: {is_first_question}")
            print(f"[ORCHESTRATOR] Chosen Dimension: {dimension}")
            print(f"[ORCHESTRATOR] Chosen Difficulty Level: {orchestrator_difficulty}")
            print(f"[ORCHESTRATOR] Requested Difficulty Level: {request.difficulty_level}")
            if reasoning:
                print(f"[ORCHESTRATOR] Reasoning: {reasoning}")
            else:
                print(f"[ORCHESTRATOR] WARNING: Reasoning field missing (optional but preferred)")
            print(f"[ORCHESTRATOR] Generated Question: {question_text}")
            print(f"[ORCHESTRATOR] ===== END DECISION LOG =====")
            
            # Use orchestrator's difficulty level if different from requested
            final_difficulty = orchestrator_difficulty if orchestrator_difficulty != request.difficulty_level else request.difficulty_level
            if orchestrator_difficulty != request.difficulty_level:
                print(f"[ORCHESTRATOR] Using orchestrator's difficulty level {orchestrator_difficulty} instead of requested {request.difficulty_level}")
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse orchestrator JSON response: {str(e)}"
            print(f"[ORCHESTRATOR] ERROR: {error_msg}")
            print(f"[ORCHESTRATOR] Raw response: {orchestrator_response.content if orchestrator_response else 'No response'}")
            error_detail = f"{error_msg} | Response preview: {orchestrator_response.content[:200] if orchestrator_response else 'No response'}"
            print(f"[ORCHESTRATOR] Full error detail: {error_detail}")
            raise HTTPException(
                status_code=500,
                detail=error_detail
            )
        except ValueError as e:
            error_msg = f"Orchestrator validation error: {str(e)}"
            print(f"[ORCHESTRATOR] ERROR: {error_msg}")
            print(f"[ORCHESTRATOR] Raw response: {orchestrator_response.content if orchestrator_response else 'No response'}")
            error_detail = f"{error_msg} | Response preview: {orchestrator_response.content[:200] if orchestrator_response else 'No response'}"
            print(f"[ORCHESTRATOR] Full error detail: {error_detail}")
            raise HTTPException(
                status_code=500,
                detail=error_detail
            )
        except Exception as e:
            error_msg = f"Orchestrator execution error: {str(e)}"
            print(f"[ORCHESTRATOR] ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            error_detail = f"{error_msg} | Response preview: {orchestrator_response.content[:200] if orchestrator_response and hasattr(orchestrator_response, 'content') else 'No response'}"
            print(f"[ORCHESTRATOR] Full error detail: {error_detail}")
            raise HTTPException(
                status_code=500,
                detail=error_detail
            )
        
        # Clean up question text (minimal - orchestrator should return clean text)
        question_text = (question_text or '').strip()
        
        # Use orchestrator's difficulty level for database and response
        difficulty_level_to_use = final_difficulty
        
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
                    difficulty_level=difficulty_level_to_use,
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
            "turn_id": turn_id,
            "reasoning": reasoning
        }
    except Exception as e:
        print(f"Error starting conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating question: {str(e)}")

async def pre_generate_first_question_for_topic(
    user_id: str,
    topic: str,
    difficulty_level: int = 1
):
    """
    Pre-generate the first question for a specific topic.
    This is used to pre-generate questions for all topics on login.
    """
    cache_key = get_first_question_cache_key(user_id, topic)
    
    try:
        print(f"[PRE-GEN FIRST-Q] Starting pre-generation for topic: {topic}, user: {user_id}")
        
        # Check if already cached
        cached = get_cached_first_question(cache_key)
        if cached:
            print(f"[PRE-GEN FIRST-Q] Already cached for topic: {topic}")
            return cached
        
        # Check if already in progress (with self-check and stale task cleanup)
        current_task = asyncio.current_task()
        with first_question_lock:
            if cache_key in first_question_in_progress:
                existing_task = first_question_in_progress[cache_key]
                # Check if it's the current task (avoid waiting for ourselves)
                if existing_task is current_task:
                    # This is the same task, don't wait - just continue
                    print(f"[PRE-GEN FIRST-Q] Same task detected for topic: {topic}, continuing...")
                elif existing_task.done():
                    # Task is done but not cleaned up, remove it
                    print(f"[PRE-GEN FIRST-Q] Found stale completed task for topic: {topic}, cleaning up...")
                    del first_question_in_progress[cache_key]
                else:
                    # Task is in progress - skip waiting and just proceed (avoid deadlocks)
                    # The existing task will complete in background, we'll generate fresh
                    print(f"[PRE-GEN FIRST-Q] Task already in progress for topic: {topic}, skipping wait and generating fresh...")
                    # Remove the old task entry to avoid conflicts
                    del first_question_in_progress[cache_key]
            
            # Mark this task as in progress
            if current_task:
                first_question_in_progress[cache_key] = current_task
        
        # Build orchestrator prompt for first question
        context_json = {
            "user_id": str(user_id) if user_id else "",
            "topic": str(topic) if topic else "",
            "diff": int(difficulty_level),
            "is_first": True
        }
        
        orchestrator_prompt = f"""Gen first Q for teen. Follow system instructions for topic-based reasoning.

Ctx: {json.dumps(context_json, separators=(',', ':'))}

Task: Analyze topic → Select dimension (ALWAYS "Basic Preferences" for first Q) → Gen Q (teen-appropriate, positive, educational)

Return JSON: {{"question": "...", "dimension": "...", "reasoning": "...", "difficulty_level": 1}}"""
        
        # Call orchestrator with rate limit retry logic
        loop = asyncio.get_event_loop()
        orchestrator_response = None
        max_retries = 3
        retry_delay = 2  # Start with 2 seconds
        
        for attempt in range(max_retries):
            try:
                orchestrator_response = await loop.run_in_executor(
                    None,
                    orchestrator.run,
                    orchestrator_prompt
                )
                break  # Success, exit retry loop
            except Exception as e:
                error_str = str(e)
                # Check if it's a rate limit error
                if "rate limit" in error_str.lower() or "tpm" in error_str.lower() or "rpm" in error_str.lower():
                    if attempt < max_retries - 1:
                        # Extract wait time from error if available
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        print(f"[PRE-GEN FIRST-Q] Rate limit hit for topic: {topic}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print(f"[PRE-GEN FIRST-Q] Rate limit error after {max_retries} attempts for topic: {topic}")
                        return None
                else:
                    # Not a rate limit error, re-raise
                    print(f"[PRE-GEN FIRST-Q] Error calling orchestrator for topic: {topic}: {e}")
                    return None
        
        if not orchestrator_response or not orchestrator_response.content:
            print(f"[PRE-GEN FIRST-Q] Orchestrator returned empty response for topic: {topic}")
            return None
        
        # Parse JSON response
        orchestrator_content = (orchestrator_response.content or '').strip()
        orchestrator_content = re.sub(r'```json\s*', '', orchestrator_content)
        orchestrator_content = re.sub(r'```\s*', '', orchestrator_content)
        orchestrator_content = orchestrator_content.strip()
        
        # Extract JSON object
        start_idx = orchestrator_content.find('{')
        if start_idx == -1:
            print(f"[PRE-GEN FIRST-Q] No JSON found in orchestrator response for topic: {topic}")
            return None
        
        brace_count = 0
        end_idx = start_idx
        for i in range(start_idx, len(orchestrator_content)):
            if orchestrator_content[i] == '{':
                brace_count += 1
            elif orchestrator_content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        
        if brace_count != 0:
            print(f"[PRE-GEN FIRST-Q] Unclosed JSON in orchestrator response for topic: {topic}")
            return None
        
        orchestrator_content = orchestrator_content[start_idx:end_idx]
        orchestrator_data = json.loads(orchestrator_content)
        
        # Extract data
        question_text = (orchestrator_data.get('question') or '').strip()
        dimension = (orchestrator_data.get('dimension') or '').strip()
        reasoning = orchestrator_data.get('reasoning', '') or None
        if reasoning:
            reasoning = str(reasoning).strip() or None
        orchestrator_difficulty = orchestrator_data.get('difficulty_level', difficulty_level)
        
        if not question_text or not dimension:
            print(f"[PRE-GEN FIRST-Q] Missing required fields for topic: {topic}")
            return None
        
        # Generate TTS audio
        audio_base64 = None
        try:
            clean_text_for_speech = question_text.replace('\n\n', '. ').replace('\n', ' ')
            audio_base64 = await loop.run_in_executor(
                None,
                text_to_speech_base64,
                clean_text_for_speech
            )
            if audio_base64:
                print(f"[PRE-GEN FIRST-Q] Generated audio for topic: {topic} ({len(audio_base64)} characters base64)")
        except Exception as e:
            print(f"[PRE-GEN FIRST-Q] Warning: Failed to generate audio for topic {topic}: {e}")
        
        # Prepare cached data (without turn_id - will be created when used)
        cached_data = {
            "question": question_text,
            "dimension": dimension,
            "reasoning": reasoning,
            "difficulty_level": orchestrator_difficulty,
            "audio_base64": audio_base64
        }
        
        # Cache it
        cache_first_question(cache_key, cached_data)
        print(f"[PRE-GEN FIRST-Q] Successfully pre-generated and cached first question for topic: {topic}")
        
        # Remove from in-progress tracking
        with first_question_lock:
            if cache_key in first_question_in_progress:
                del first_question_in_progress[cache_key]
        
        return cached_data
        
    except Exception as e:
        print(f"[PRE-GEN FIRST-Q] Error pre-generating first question for topic {topic}: {e}")
        import traceback
        traceback.print_exc()
        
        # Remove from in-progress tracking on error
        with first_question_lock:
            if cache_key in first_question_in_progress:
                del first_question_in_progress[cache_key]
        
        return None

async def pre_generate_all_first_questions(user_id: str, difficulty_level: int = 1):
    """
    Pre-generate first questions for ALL topics in the background.
    Called after user login to prepare questions for instant topic selection.
    Uses staggered execution to avoid rate limits.
    """
    topics = ['gaming', 'food', 'hobbies', 'youtube', 'weekend']
    
    print(f"[PRE-GEN ALL] Starting pre-generation for all topics for user: {user_id}")
    
    # Process topics sequentially with delays to avoid rate limits
    # This is slower but prevents hitting OpenAI rate limits
    successful = 0
    failed = 0
    
    for i, topic in enumerate(topics):
        try:
            # Add delay between topics to avoid rate limits (except for first one)
            if i > 0:
                await asyncio.sleep(2)  # 2 second delay between topics
            
            result = await pre_generate_first_question_for_topic(user_id, topic, difficulty_level)
            if result:
                successful += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[PRE-GEN ALL] Error pre-generating topic {topic}: {e}")
            failed += 1
    
    print(f"[PRE-GEN ALL] Completed: {successful} successful, {failed} failed for user: {user_id}")

async def pre_generate_next_question(
    user_id: str,
    topic: str,
    user_response: str,
    previous_question: str,
    previous_turn_id: str,
    session_id: str,
    difficulty_level: int = 1
):
    """
    Pre-generate the next question in the background.
    This function runs asynchronously and caches the result for instant retrieval.
    """
    try:
        print(f"[PRE-GEN] Starting pre-generation for user {user_id}, topic {topic}")
        
        # Get conversation history, dimension history, and speech metrics in parallel (with caching)
        conversation_history = []
        dimension_history = []
        speech_metrics = []
        speech_trends = None
        try:
            conversation_history, dimension_history, speech_metrics = await get_user_topic_data_parallel(user_id, topic)
            speech_trends = analyze_speech_trends(speech_metrics)
            print(f"[PRE-GEN] Retrieved {len(conversation_history)} conversation turns, {len(dimension_history)} dimensions, and {len(speech_metrics)} speech metrics")
        except Exception as e:
            print(f"[PRE-GEN] Warning: Error retrieving history: {e}")
            import traceback
            traceback.print_exc()
            conversation_history = []
            dimension_history = []
            speech_metrics = []
            speech_trends = None
        
        # Analyze engagement level based on user response
        response_length = len(user_response.split())
        engagement_level = "low"
        if response_length > 20:
            engagement_level = "high"
        elif response_length > 10:
            engagement_level = "medium"
        
        # Build context for orchestrator (using rule-based summarization)
        history_context = summarize_conversation_history(conversation_history, max_turns=3)
        
        # Check if same dimension used 2+ times in a row
        dimension_warning = ""
        if dimension_history and len(dimension_history) >= 2:
            last_two = dimension_history[:2]
            if last_two[0] == last_two[1]:
                dimension_warning = f"⚠️ CRITICAL: Last 2 turns used '{last_two[0]}'. You MUST switch to a DIFFERENT dimension now!"
                print(f"[PRE-GEN] WARNING: Same dimension '{last_two[0]}' used 2 times in a row - forcing switch")
        
        dimension_context = ""
        if dimension_history:
            dimension_context = f"Recently used dimensions: {', '.join(dimension_history[:5])}\n"
            if dimension_warning:
                dimension_context += dimension_warning + "\n"
            else:
                dimension_context += "Avoid repeating these dimensions unless it's a natural continuation.\n"
        
        # Build speech performance context (compressed format with numeric values)
        speech_context = ""
        if speech_trends:
            recent_clarity_scores = [m.get('clarity_score', 0.0) for m in speech_metrics[:3] if m.get('clarity_score') is not None]
            avg_clarity = speech_trends['average_clarity']
            recent_clarity = speech_trends['recent_clarity']
            avg_pace = speech_trends['average_pace']
            speech_context = f"Speech: clarity_trend={speech_trends['clarity_trend']}, clarity_avg={avg_clarity:.2f}, clarity_recent={recent_clarity:.2f}, pace_trend={speech_trends['pace_trend']}, pace_avg={avg_pace:.0f}wpm, conf={speech_trends['confidence_level']}, recent_scores={recent_clarity_scores}"
        elif speech_metrics:
            recent_clarity = speech_metrics[0].get('clarity_score') if speech_metrics else None
            if recent_clarity is not None:
                speech_context = f"Speech: clarity_recent={recent_clarity:.2f} (limited data)"
        
        # Build JSON context (Option 4: structured data)
        try:
            prev_q = str(previous_question or "")[:100] if previous_question else ""
            user_resp = str(user_response or "")[:150] if user_response else ""
            context_json = {
                "topic": str(topic) if topic else "",
                "prev_q": prev_q,
                "user_resp": user_resp,
                "diff": int(difficulty_level),
                "eng": str(engagement_level) if engagement_level else "",
                "history": str(history_context) if history_context else "early conversation",
                "dims_used": [str(d) for d in (dimension_history[:3] if dimension_history else [])],
                "speech": str(speech_context) if speech_context else None
            }
            context_json_str = json.dumps(context_json, separators=(',', ':'))
        except Exception as e:
            print(f"[PRE-GEN] Error building context JSON: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to simpler format
            context_json_str = f'{{"topic":"{topic}","prev_q":"{str(previous_question or "")[:100]}","user_resp":"{str(user_response or "")[:150]}","diff":{difficulty_level},"eng":"{engagement_level}"}}'
        
        # Short task instructions with dimension switching enforcement
        dims_list = dimension_history[:3] if dimension_history else []
        dims_str = ', '.join([str(d) for d in dims_list]) if dims_list else 'none'
        switch_instruction = dimension_warning if dimension_warning else f"Select dimension (avoid: {dims_str})"
        
        orchestrator_prompt = f"""Gen follow-up Q. Follow system instructions for continue conversation reasoning.

Ctx: {context_json_str}

Task: Analyze response → {switch_instruction} → Adjust difficulty → Gen Q (ack+personal+question, match tone, vary ack, don't repeat prev_q)

Return JSON: {{"question": "...", "dimension": "...", "reasoning": "...", "difficulty_level": 1}}"""

        # Call orchestrator with rate limit retry logic
        loop = asyncio.get_event_loop()
        reasoning = None
        orchestrator_response = None
        max_retries = 3
        retry_delay = 2  # Start with 2 seconds
        
        for attempt in range(max_retries):
            try:
                orchestrator_response = await loop.run_in_executor(
                    None,
                    orchestrator.run,
                    orchestrator_prompt
                )
                
                if not orchestrator_response or not orchestrator_response.content:
                    raise ValueError("Orchestrator returned empty response")
                
                print(f"[PRE-GEN] Orchestrator response received (length: {len(orchestrator_response.content)} chars)")
                break  # Success, exit retry loop
            except Exception as e:
                error_str = str(e)
                # Check if it's a rate limit error
                if "rate limit" in error_str.lower() or "tpm" in error_str.lower() or "rpm" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        print(f"[PRE-GEN] Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print(f"[PRE-GEN] Rate limit error after {max_retries} attempts, skipping pre-generation")
                        return None
                else:
                    # Not a rate limit error, re-raise
                    print(f"[PRE-GEN] Error calling orchestrator: {e}")
                    return None
        
        try:
            
            # Parse JSON response from orchestrator
            orchestrator_content = (orchestrator_response.content or '').strip()
            
            # Remove markdown code blocks if present
            orchestrator_content = re.sub(r'```json\s*', '', orchestrator_content)
            orchestrator_content = re.sub(r'```\s*', '', orchestrator_content)
            orchestrator_content = orchestrator_content.strip()
            
            # Extract JSON object
            start_idx = orchestrator_content.find('{')
            if start_idx == -1:
                raise ValueError("No JSON object found in orchestrator response")
            
            brace_count = 0
            end_idx = start_idx
            for i in range(start_idx, len(orchestrator_content)):
                if orchestrator_content[i] == '{':
                    brace_count += 1
                elif orchestrator_content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            if brace_count != 0:
                raise ValueError("Unclosed JSON object in orchestrator response")
            
            orchestrator_content = orchestrator_content[start_idx:end_idx]
            
            # Parse JSON
            orchestrator_data = json.loads(orchestrator_content)
            
            # Validate required fields
            if 'question' not in orchestrator_data or not orchestrator_data.get('question'):
                raise ValueError("Orchestrator response missing 'question' field")
            if 'dimension' not in orchestrator_data or not orchestrator_data.get('dimension'):
                raise ValueError("Orchestrator response missing 'dimension' field")
            
            # Extract data (with None safety)
            question_text = (orchestrator_data.get('question') or '').strip()
            dimension = (orchestrator_data.get('dimension') or '').strip()
            reasoning = orchestrator_data.get('reasoning', '') or None
            if reasoning:
                reasoning = str(reasoning).strip() or None
            orchestrator_difficulty = orchestrator_data.get('difficulty_level', difficulty_level)
            
            # Validate that we have required fields
            if not question_text:
                raise ValueError("Orchestrator response 'question' field is empty or None")
            if not dimension:
                raise ValueError("Orchestrator response 'dimension' field is empty or None")
            
            # Clean up question text
            question_text = (question_text or '').strip()
            question_text = re.sub(r'^(?:here\'?s|here is|you could ask|try asking|question:?)\s*', '', question_text, flags=re.IGNORECASE)
            
            if (question_text.startswith('"') and question_text.endswith('"')) or \
               (question_text.startswith("'") and question_text.endswith("'")):
                question_text = question_text[1:-1].strip()
            
            if question_text.startswith('**') and question_text.endswith('**'):
                question_text = question_text[2:-2].strip()
            
            question_text = (question_text or '').strip()
            
            # Format follow-up questions
            formatted_question = question_text
            if re.search(r'\.\s+([A-Z][a-z])', question_text):
                formatted_question = re.sub(r'\.\s+([A-Z][a-z])', r'.\n\n\1', question_text)
            elif re.search(r'([!?])\s+([A-Z][a-z])', question_text):
                formatted_question = re.sub(r'([!?])\s+([A-Z][a-z])', r'\1\n\n\2', question_text)
            elif re.search(r',\s+([A-Z][a-z])', question_text):
                formatted_question = re.sub(r',\s+([A-Z][a-z])', r',\n\n\1', question_text)
            
            # Generate audio for the question
            audio_base64 = None
            try:
                clean_text_for_speech = formatted_question.replace('\n\n', '. ').replace('\n', ' ')
                audio_base64 = await loop.run_in_executor(
                    None,
                    text_to_speech_base64,
                    clean_text_for_speech
                )
                if audio_base64:
                    print(f"[PRE-GEN] Generated audio for question ({len(audio_base64)} characters base64)")
            except Exception as e:
                print(f"[PRE-GEN] Warning: Failed to generate audio: {e}")
            
            # Use orchestrator's difficulty level
            final_difficulty = orchestrator_difficulty if orchestrator_difficulty != difficulty_level else difficulty_level
            
            # Create cache entry
            cache_key = get_cache_key(user_id, topic, previous_turn_id)
            question_data = {
                "question": formatted_question,
                "dimension": dimension,
                "reasoning": reasoning,
                "difficulty_level": final_difficulty,
                "audio_base64": audio_base64,
                "turn_id": None  # Will be set when retrieved
            }
            
            # Cache the question
            cache_question(cache_key, question_data)
            print(f"[PRE-GEN] ===== PRE-GENERATION SUCCESS =====")
            print(f"[PRE-GEN] Cache Key: {cache_key}")
            print(f"[PRE-GEN] Question: {formatted_question[:100]}...")
            print(f"[PRE-GEN] Dimension: {dimension}")
            print(f"[PRE-GEN] Difficulty: {final_difficulty}")
            print(f"[PRE-GEN] Audio Generated: {audio_base64 is not None}")
            print(f"[PRE-GEN] Current cache size: {len(question_cache)} entries")
            print(f"[PRE-GEN] ==================================")
            
        except Exception as e:
            print(f"[PRE-GEN] Error pre-generating question: {e}")
            import traceback
            traceback.print_exc()
            # Don't raise - this is background task, failures shouldn't affect main flow
    
    except Exception as e:
        print(f"[PRE-GEN] Fatal error in pre-generation: {e}")
        import traceback
        traceback.print_exc()

@app.post("/api/continue_conversation", response_model=QuestionOnlyResponse)
async def continue_conversation(request: ContinueConversationRequest):
    """
    Generate a follow-up question based on previous context using conversation tools.
    The orchestrator chooses the dimension, and the conversation agent uses tools to generate contextual follow-ups.
    First checks cache for pre-generated question, otherwise generates on-demand.
    """
    try:
        if not request.user_response:
            raise HTTPException(status_code=400, detail="user_response is required for follow-up questions")
        
        # Log incoming user response for context drift / relevancy testing
        print(f"[SESSION TURN] ===== USER RESPONSE RECEIVED =====")
        print(f"[SESSION TURN] User ID:           {request.user_id}")
        print(f"[SESSION TURN] Session ID:        {request.session_id}")
        print(f"[SESSION TURN] Topic:             {request.topic}")
        print(f"[SESSION TURN] Previous Turn ID:  {request.previous_turn_id}")
        print(f"[SESSION TURN] Previous Question: {(request.previous_question or 'N/A')[:200]}")
        print(f"[SESSION TURN] User Response:     {request.user_response}")
        print(f"[SESSION TURN] Word Count:        {len(request.user_response.split())}")
        print(f"[SESSION TURN] ============================================")

        # Check cache for pre-generated question first
        print(f"[CONTINUE] Checking cache for user_id={request.user_id}, topic={request.topic}, previous_turn_id={request.previous_turn_id}")
        if request.previous_turn_id:
            cache_key = get_cache_key(request.user_id, request.topic, request.previous_turn_id)
            print(f"[CONTINUE] Cache key: {cache_key}")
            print(f"[CONTINUE] Current cache entries: {list(question_cache.keys())}")
            cached_question = get_cached_question(cache_key)
            
            if cached_question:
                print(f"[CACHE HIT] Returning pre-generated question for user {request.user_id}, topic {request.topic}")
                
                # Update previous turn with user's response (same as non-cache path)
                if request.previous_turn_id and request.user_response:
                    try:
                        updated_turn = update_conversation_turn_with_response(
                            turn_id=request.previous_turn_id,
                            user_response=request.user_response,
                            response_type="custom_speech"
                        )
                        if updated_turn:
                            print(f"[CACHE HIT] Updated previous turn {request.previous_turn_id} with user response")
                        else:
                            print(f"[CACHE HIT] Warning: Failed to update previous turn {request.previous_turn_id}")
                    except Exception as e:
                        print(f"[CACHE HIT] Warning: Error updating previous turn: {e}")

                # Need to create turn in database and get turn_id
                turn_id = None
                try:
                    session_topic = get_or_create_session_topic(request.session_id, request.topic)
                    if session_topic:
                        session_topic_id = str(session_topic['id'])
                        current_turn = get_current_turn(session_topic_id)
                        turn_number = 1
                        if current_turn:
                            turn_number = current_turn.get('turn_number', 0) + 1
                        
                        conversation_turn = create_conversation_turn(
                            session_topic_id=session_topic_id,
                            turn_number=turn_number,
                            dimension=cached_question['dimension'],
                            difficulty_level=cached_question['difficulty_level'],
                            question=cached_question['question']
                        )
                        
                        if conversation_turn:
                            turn_id = str(conversation_turn['id'])
                            # Update cached question with turn_id
                            cached_question['turn_id'] = turn_id
                            print(f"[CACHE HIT] Created turn {turn_number} (ID: {turn_id}) for cached question")
                except Exception as e:
                    print(f"[CACHE HIT] Warning: Error creating turn for cached question: {e}")
                    # Continue with cached question even if turn creation fails
                
                return {
                    "question": cached_question['question'],
                    "dimension": cached_question['dimension'],
                    "audio_base64": cached_question.get('audio_base64'),
                    "turn_id": turn_id,
                    "reasoning": cached_question.get('reasoning')
                }
            else:
                print(f"[CACHE MISS] No pre-generated question found for key: {cache_key}, generating on-demand")
        
        # OPTIMIZATION 1: Parallelize Previous Turn Update + Data Fetching
        # Start both operations in parallel
        update_task = None
        if request.previous_turn_id:
            async def update_previous_turn():
                try:
                    response_type = "custom_speech"
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
            
            update_task = asyncio.create_task(update_previous_turn())
        
        # Get conversation history, dimension history, and speech metrics in parallel (with caching)
        conversation_history = []
        dimension_history = []
        speech_metrics = []
        speech_trends = None
        try:
            # Get user_id from request or session
            user_id = request.user_id
            if not user_id and request.session_id:
                # Try to get user_id from session
                session_response = supabase.table('sessions').select('user_id').eq('id', request.session_id).limit(1).execute()
                if session_response.data:
                    user_id = session_response.data[0].get('user_id')
            
            if user_id:
                conversation_history, dimension_history, speech_metrics = await get_user_topic_data_parallel(user_id, request.topic)
                speech_trends = analyze_speech_trends(speech_metrics)
                print(f"Retrieved {len(conversation_history)} conversation turns, {len(dimension_history)} dimensions, and {len(speech_metrics)} speech metrics for user {user_id}, topic {request.topic}")
                if speech_trends:
                    print(f"Speech trends: clarity={speech_trends['clarity_trend']}, pace={speech_trends['pace_trend']}, confidence={speech_trends['confidence_level']}")
        except Exception as e:
            print(f"Warning: Error retrieving conversation/dimension/speech history: {e}")
            import traceback
            traceback.print_exc()
            conversation_history = []
            dimension_history = []
            speech_metrics = []
            speech_trends = None
        
        # Analyze engagement level based on user response
        response_length = len(request.user_response.split())
        engagement_level = "low"
        if response_length > 20:
            engagement_level = "high"
        elif response_length > 10:
            engagement_level = "medium"
        
        # OPTIMIZATION 2: Reduce Orchestrator Prompt Size
        # Build context for orchestrator (using rule-based summarization) - REDUCED
        history_context = summarize_conversation_history(conversation_history, max_turns=2)  # Reduced from 3 to 2
        
        # Build speech performance context (ULTRA-COMPRESSED format)
        speech_context = ""
        if speech_trends:
            # Only include essential metrics: trend and recent clarity
            speech_context = f"sp:tr={speech_trends['clarity_trend'][:1]},cl={speech_trends['recent_clarity']:.2f}"  # e.g., "sp:tr=i,cl=0.88"
        elif speech_metrics:
            recent_clarity = speech_metrics[0].get('clarity_score') if speech_metrics else None
            if recent_clarity is not None:
                speech_context = f"sp:cl={recent_clarity:.2f}"  # e.g., "sp:cl=0.85"
        
        # Use orchestrator to analyze user response, check engagement, review dimension history, and select next dimension
        print(f"[ORCHESTRATOR] Calling orchestrator for continue conversation - topic: {request.topic}")
        
        # Build JSON context (REDUCED sizes)
        try:
            # Reduced truncation: prev_q from 100 to 60, user_resp from 150 to 80
            prev_q = str(request.previous_question or "")[:60] if request.previous_question else ""
            user_resp = str(request.user_response or "")[:80] if request.user_response else ""
            
            # Reduce history context length
            history_str = str(history_context) if history_context else "early"
            if len(history_str) > 100:
                history_str = history_str[:100] + "..."
            
            context_json = {
                "t": str(request.topic)[:20],  # topic shortened
                "pq": prev_q,  # prev_q (already truncated)
                "ur": user_resp,  # user_resp (already truncated)
                "d": int(request.difficulty_level),  # diff shortened
                "e": str(engagement_level)[:1],  # eng shortened to first char (l/m/h)
                "h": history_str,  # history (truncated)
                "du": [str(d)[:15] for d in (dimension_history[:2] if dimension_history else [])],  # dims_used: only 2, truncated
                "s": speech_context if speech_context else None  # speech (ultra-compressed)
            }
            context_json_str = json.dumps(context_json, separators=(',', ':'))
        except Exception as e:
            print(f"[ORCHESTRATOR] Error building context JSON: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to simpler format
            context_json_str = f'{{"t":"{request.topic[:20]}","pq":"{str(request.previous_question or "")[:60]}","ur":"{str(request.user_response or "")[:80]}","d":{request.difficulty_level},"e":"{engagement_level[0]}"}}'
        
        # Check if same dimension used 2+ times in a row
        dimension_warning = ""
        if dimension_history and len(dimension_history) >= 2:
            last_two = dimension_history[:2]
            if last_two[0] == last_two[1]:
                dimension_warning = f"⚠️ CRITICAL: Last 2 turns used '{last_two[0]}'. MUST switch to DIFFERENT dimension!"
                print(f"[ORCHESTRATOR] WARNING: Same dimension '{last_two[0]}' used 2 times in a row - forcing switch")
        
        # Short task instructions with dimension switching enforcement
        dims_str = ','.join([str(d)[:10] for d in dimension_history[:2]]) if dimension_history else 'none'
        switch_instruction = dimension_warning if dimension_warning else f"Select dimension (avoid: {dims_str})"
        
        orchestrator_prompt = f"""Gen follow-up Q. Follow system instructions.

Ctx: {context_json_str}

Task: Analyze → {switch_instruction} → Gen Q (ack+personal+question, match tone, don't repeat)

Return JSON: {{"question":"...","dimension":"...","reasoning":"...","difficulty_level":1}}"""

        # Call orchestrator
        loop = asyncio.get_event_loop()
        reasoning = None  # Initialize reasoning
        try:
            orchestrator_response = None
            max_retries = 3
            retry_delay = 2  # Start with 2 seconds
            
            for attempt in range(max_retries):
                try:
                    orchestrator_response = await loop.run_in_executor(
                        None,
                        orchestrator.run,
                        orchestrator_prompt
                    )
                    
                    if not orchestrator_response or not orchestrator_response.content:
                        raise ValueError("Orchestrator returned empty response")
                    
                    print(f"[ORCHESTRATOR] Received response (length: {len(orchestrator_response.content)} chars)")
                    print(f"[ORCHESTRATOR] Raw response preview: {orchestrator_response.content[:200]}...")
                    break  # Success, exit retry loop
                except Exception as e:
                    error_str = str(e)
                    # Check if it's a rate limit error
                    if "rate limit" in error_str.lower() or "tpm" in error_str.lower() or "rpm" in error_str.lower():
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                            print(f"[ORCHESTRATOR] Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise HTTPException(
                                status_code=429,
                                detail=f"Rate limit exceeded. Please try again in a few moments."
                            )
                    else:
                        # Not a rate limit error, re-raise
                        raise
            
            # Parse JSON response from orchestrator
            orchestrator_content = (orchestrator_response.content or '').strip()
            
            # Remove markdown code blocks if present
            orchestrator_content = re.sub(r'```json\s*', '', orchestrator_content)
            orchestrator_content = re.sub(r'```\s*', '', orchestrator_content)
            orchestrator_content = orchestrator_content.strip()
            
            # Extract JSON object
            start_idx = orchestrator_content.find('{')
            if start_idx == -1:
                raise ValueError("No JSON object found in orchestrator response")
            
            brace_count = 0
            end_idx = start_idx
            for i in range(start_idx, len(orchestrator_content)):
                if orchestrator_content[i] == '{':
                    brace_count += 1
                elif orchestrator_content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            if brace_count != 0:
                raise ValueError("Unclosed JSON object in orchestrator response")
            
            orchestrator_content = orchestrator_content[start_idx:end_idx]
            
            # Parse JSON
            orchestrator_data = json.loads(orchestrator_content)
            
            # Validate required fields
            if 'question' not in orchestrator_data or not orchestrator_data.get('question'):
                raise ValueError("Orchestrator response missing 'question' field")
            if 'dimension' not in orchestrator_data or not orchestrator_data.get('dimension'):
                raise ValueError("Orchestrator response missing 'dimension' field")
            
            # Extract data (with None safety)
            question_text = (orchestrator_data.get('question') or '').strip()
            dimension = (orchestrator_data.get('dimension') or '').strip()
            reasoning = orchestrator_data.get('reasoning', '') or None
            if reasoning:
                reasoning = str(reasoning).strip() or None
            orchestrator_difficulty = orchestrator_data.get('difficulty_level', request.difficulty_level)
            
            # Validate that we have required fields
            if not question_text:
                raise ValueError("Orchestrator response 'question' field is empty or None")
            if not dimension:
                raise ValueError("Orchestrator response 'dimension' field is empty or None")
            
            # Validate dimension (log warning if not in list, but allow flexibility)
            if dimension not in DIMENSIONS and dimension != "Basic Preferences":
                print(f"[ORCHESTRATOR] WARNING: Dimension '{dimension}' not in standard list. Allowing flexibility.")
            else:
                print(f"[ORCHESTRATOR] Dimension '{dimension}' validated against standard list.")
            
            # Log detailed orchestrator decisions
            print(f"[ORCHESTRATOR] ===== CONTINUE CONVERSATION DECISION LOG =====")
            print(f"[ORCHESTRATOR] Topic: {request.topic}")
            print(f"[ORCHESTRATOR] User Response: {request.user_response}")
            print(f"[ORCHESTRATOR] Engagement Level: {engagement_level} ({response_length} words)")
            print(f"[ORCHESTRATOR] Dimension History: {dimension_history[:5] if dimension_history else 'None'}")
            if speech_trends:
                print(f"[ORCHESTRATOR] Speech Performance:")
                print(f"[ORCHESTRATOR]   - Clarity Trend: {speech_trends['clarity_trend']}")
                print(f"[ORCHESTRATOR]   - Average Clarity: {speech_trends['average_clarity']}")
                print(f"[ORCHESTRATOR]   - Confidence Level: {speech_trends['confidence_level']}")
                print(f"[ORCHESTRATOR]   - Recent Clarity: {speech_trends['recent_clarity']}")
            else:
                print(f"[ORCHESTRATOR] Speech Performance: No data available")
            print(f"[ORCHESTRATOR] Chosen Dimension: {dimension}")
            print(f"[ORCHESTRATOR] Chosen Difficulty Level: {orchestrator_difficulty}")
            print(f"[ORCHESTRATOR] Requested Difficulty Level: {request.difficulty_level}")
            if reasoning:
                print(f"[ORCHESTRATOR] Reasoning: {reasoning}")
            else:
                print(f"[ORCHESTRATOR] WARNING: Reasoning field missing (optional but preferred)")
            print(f"[ORCHESTRATOR] Generated Question: {question_text[:200]}...")
            print(f"[ORCHESTRATOR] ===== END DECISION LOG =====")
            
            # Use orchestrator's difficulty level if different from requested
            final_difficulty = orchestrator_difficulty if orchestrator_difficulty != request.difficulty_level else request.difficulty_level
            if orchestrator_difficulty != request.difficulty_level:
                print(f"[ORCHESTRATOR] Using orchestrator's difficulty level {orchestrator_difficulty} instead of requested {request.difficulty_level}")
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse orchestrator JSON response: {str(e)}"
            print(f"[ORCHESTRATOR] ERROR: {error_msg}")
            print(f"[ORCHESTRATOR] Raw response: {orchestrator_response.content if orchestrator_response else 'No response'}")
            error_detail = f"{error_msg} | Response preview: {orchestrator_response.content[:200] if orchestrator_response else 'No response'}"
            print(f"[ORCHESTRATOR] Full error detail: {error_detail}")
            raise HTTPException(
                status_code=500,
                detail=error_detail
            )
        except ValueError as e:
            error_msg = f"Orchestrator validation error: {str(e)}"
            print(f"[ORCHESTRATOR] ERROR: {error_msg}")
            print(f"[ORCHESTRATOR] Raw response: {orchestrator_response.content if orchestrator_response else 'No response'}")
            error_detail = f"{error_msg} | Response preview: {orchestrator_response.content[:200] if orchestrator_response else 'No response'}"
            raise HTTPException(
                status_code=500,
                detail=error_detail
            )
        except Exception as e:
            error_msg = f"Orchestrator execution error: {str(e)}"
            print(f"[ORCHESTRATOR] ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )
        
        # Clean up question text (minimal, preserve natural flow)
        question_text = (question_text or '').strip()
        
        # Only remove very specific instruction prefixes
        question_text = re.sub(r'^(?:here\'?s|here is|you could ask|try asking|question:?)\s*', '', question_text, flags=re.IGNORECASE)
        
        # Extract text within quotes ONLY if the ENTIRE response is wrapped in quotes
        if (question_text.startswith('"') and question_text.endswith('"')) or \
           (question_text.startswith("'") and question_text.endswith("'")):
            question_text = question_text[1:-1].strip()
        
        # Extract text after bold markers ONLY if the entire response is bold
        if question_text.startswith('**') and question_text.endswith('**'):
            question_text = question_text[2:-2].strip()
        
        # Final cleanup
        question_text = (question_text or '').strip()
        
        # Format follow-up questions: Split acknowledgement+preference and question into separate lines
        # New pattern: "Acknowledgement + personal preference" on first line, question on next line
        formatted_question = question_text
        
        # Try to detect acknowledgement + personal preference + question pattern
        # Pattern 1: Period followed by space and capital letter (e.g., "That's great! I like that too. Do you...")
        if re.search(r'\.\s+([A-Z][a-z])', question_text):
            formatted_question = re.sub(r'\.\s+([A-Z][a-z])', r'.\n\n\1', question_text)
        # Pattern 2: Exclamation mark followed by space and capital letter (e.g., "That's great! Do you...")
        elif re.search(r'([!?])\s+([A-Z][a-z])', question_text):
            formatted_question = re.sub(r'([!?])\s+([A-Z][a-z])', r'\1\n\n\2', question_text)
        # Pattern 3: Comma followed by space and capital letter (less common but possible)
        elif re.search(r',\s+([A-Z][a-z])', question_text):
            formatted_question = re.sub(r',\s+([A-Z][a-z])', r',\n\n\1', question_text)
        
        print(f"[DEBUG] After formatting, formatted_question length: {len(formatted_question)} characters")
        print(f"[DEBUG] After formatting, formatted_question: {repr(formatted_question[:200])}...")
        print(f"Generated follow-up question: {formatted_question[:200]}...")
        
        # Generate TTS audio together with question (wait for completion)
        # Prepare text for TTS (remove newlines for clean speech)
        clean_text_for_speech = formatted_question.replace('\n\n', '. ').replace('\n', ' ')
        
        # Generate TTS audio and save to database in parallel
        loop = asyncio.get_event_loop()
        audio_base64 = None
        
        async def generate_audio():
            """Generate TTS audio for the follow-up question"""
            try:
                audio = await loop.run_in_executor(
                    None,
                    text_to_speech_base64,
                    clean_text_for_speech
                )
                if audio:
                    print(f"Generated audio for follow-up question ({len(audio)} characters base64)")
                return audio
            except Exception as e:
                print(f"Warning: Failed to generate audio for follow-up question: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        async def save_to_database():
            """Save conversation turn to database"""
            try:
                # Get or create session_topic
                session_topic = get_or_create_session_topic(request.session_id, request.topic)
                if not session_topic:
                    print(f"Warning: Failed to get/create session_topic for session {request.session_id}, topic {request.topic}")
                    return None
                
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
                    difficulty_level=final_difficulty,
                    question=formatted_question
                )
                
                if conversation_turn:
                    turn_id = str(conversation_turn['id'])
                    print(f"Created follow-up conversation turn {turn_number} (ID: {turn_id}) for topic {request.topic}")
                    return turn_id
                else:
                    print(f"Warning: Failed to create conversation_turn for session_topic {session_topic_id}")
                    return None
            except Exception as e:
                print(f"Warning: Error saving conversation state to database: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        # Execute TTS generation and database save in parallel
        audio_task = asyncio.create_task(generate_audio())
        db_task = asyncio.create_task(save_to_database())
        
        # Wait for both TTS generation and database save to complete in parallel
        audio_base64, turn_id = await asyncio.gather(audio_task, db_task)
        
        # Wait for previous turn update to complete (if it was started)
        if update_task:
            try:
                await update_task
            except Exception as e:
                print(f"Warning: Previous turn update task failed: {e}")
        
        return {
            "question": formatted_question,
            "dimension": dimension,
            "audio_base64": audio_base64,  # TTS audio for the follow-up question
            "turn_id": turn_id,
            "reasoning": reasoning
        }
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
            topic = request.topic or "general conversation"
            
            # Build prompt with topic and user context if available
            if request.user_response:
                response_prompt = (
                    f"Q: '{request.question}' | Topic: {topic} | Dim: {dimension} | Level: {difficulty_level} | "
                    f"User said: '{request.user_response}'. "
                    f"⚠️ Generate options SPECIFICALLY about {topic} AND what user mentioned. NO generic options."
                )
            else:
                response_prompt = (
                    f"Q: '{request.question}' | Topic: {topic} | Dim: {dimension} | Level: {difficulty_level}. "
                    f"⚠️ Generate options SPECIFICALLY about {topic} ONLY. Gaming→games, Food→food, Hobbies→hobbies. NO generic options."
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

@app.get("/api/debug/cache-status")
async def get_cache_status():
    """Debug endpoint to check cache status"""
    with cache_lock:
        return {
            "cache_size": len(question_cache),
            "cache_keys": list(question_cache.keys()),
            "expiry_times": {k: str(v) for k, v in cache_expiry.items()}
        }

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

            # Log the transcribed user response for context drift / relevancy testing
            print(f"[SESSION TURN] ===== SPEECH RESPONSE TRANSCRIBED =====")
            print(f"[SESSION TURN] Turn ID:       {turn_id or 'N/A'}")
            print(f"[SESSION TURN] Transcript:    {analysis_data['transcript']}")
            print(f"[SESSION TURN] Clarity Score: {analysis_data['clarity_score']}")
            print(f"[SESSION TURN] Pace (WPM):    {analysis_data['pace_wpm']}")
            print(f"[SESSION TURN] Filler Words:  {analysis_data['filler_words']}")
            print(f"[SESSION TURN] Feedback:      {analysis_data['feedback']}")
            print(f"[SESSION TURN] ================================================")

            # Trigger background pre-generation of next question if we have all required info
            print(f"[PRE-GEN] Checking if pre-generation should be triggered...")
            print(f"[PRE-GEN] turn_id: {turn_id}, transcript: {analysis_data.get('transcript', '')[:50] if analysis_data.get('transcript') else 'None'}...")
            if turn_id and analysis_data.get('transcript'):
                try:
                    # Get conversation turn details to extract user_id, topic, previous_question
                    # We need to query the database to get these details
                    if supabase:
                        turn_response = supabase.table('conversation_turns')\
                            .select('id, question, session_topic_id, dimension')\
                            .eq('id', turn_id)\
                            .limit(1)\
                            .execute()
                        
                        if turn_response.data and len(turn_response.data) > 0:
                            turn_data = turn_response.data[0]
                            previous_question = turn_data.get('question', '')
                            session_topic_id = turn_data.get('session_topic_id')
                            
                            if session_topic_id and previous_question:
                                # Get session_topic to get topic and session_id
                                topic_response = supabase.table('session_topics')\
                                    .select('topic_name, session_id')\
                                    .eq('id', session_topic_id)\
                                    .limit(1)\
                                    .execute()
                                
                                if topic_response.data and len(topic_response.data) > 0:
                                    topic_data = topic_response.data[0]
                                    topic = topic_data.get('topic_name', '')
                                    session_id = topic_data.get('session_id', '')
                                    
                                    # Get user_id from session
                                    if session_id:
                                        session_response = supabase.table('sessions')\
                                            .select('user_id')\
                                            .eq('id', session_id)\
                                            .limit(1)\
                                            .execute()
                                        
                                        if session_response.data and len(session_response.data) > 0:
                                            user_id = session_response.data[0].get('user_id', '')
                                            
                                            if user_id and topic:
                                                # Trigger background pre-generation
                                                cache_key = get_cache_key(user_id, topic, turn_id)
                                                print(f"[PRE-GEN] ===== TRIGGERING PRE-GENERATION =====")
                                                print(f"[PRE-GEN] User ID: {user_id}")
                                                print(f"[PRE-GEN] Topic: {topic}")
                                                print(f"[PRE-GEN] Previous Question: {previous_question[:100]}...")
                                                print(f"[PRE-GEN] Previous Turn ID: {turn_id}")
                                                print(f"[PRE-GEN] User Response: {analysis_data['transcript'][:100]}...")
                                                print(f"[PRE-GEN] Cache Key: {cache_key}")
                                                print(f"[PRE-GEN] ======================================")
                                                
                                                # Create background task
                                                task = asyncio.create_task(pre_generate_next_question(
                                                    user_id=user_id,
                                                    topic=topic,
                                                    user_response=analysis_data['transcript'],
                                                    previous_question=previous_question,
                                                    previous_turn_id=turn_id,
                                                    session_id=session_id,
                                                    difficulty_level=1  # Default, can be retrieved from turn if needed
                                                ))
                                                print(f"[PRE-GEN] Background task created (task: {task}, done: {task.done()})")
                                                print(f"[PRE-GEN] Background task started (non-blocking)")
                                            else:
                                                print(f"[PRE-GEN] Missing user_id or topic, skipping pre-generation")
                                        else:
                                            print(f"[PRE-GEN] Could not find session for session_id: {session_id}")
                                    else:
                                        print(f"[PRE-GEN] Missing session_id, skipping pre-generation")
                                else:
                                    print(f"[PRE-GEN] Could not find session_topic for session_topic_id: {session_topic_id}")
                            else:
                                print(f"[PRE-GEN] Missing session_topic_id or previous_question, skipping pre-generation")
                        else:
                            print(f"[PRE-GEN] Could not find conversation_turn for turn_id: {turn_id}")
                    else:
                        print(f"[PRE-GEN] Supabase not available, skipping pre-generation")
                except Exception as e:
                    print(f"[PRE-GEN] Error triggering pre-generation: {e}")
                    import traceback
                    traceback.print_exc()
                    # Don't fail the request if pre-generation fails
            
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
