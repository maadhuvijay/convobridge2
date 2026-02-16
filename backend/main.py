from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
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
    create_session, is_first_question_for_topic
)

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

# Initialize the orchestrator team and sub-agents
orchestrator = create_orchestrator_agent()
conversation_agent = create_conversation_agent()
response_agent = create_response_agent()
vocabulary_agent = create_vocabulary_agent()
speech_analysis_agent = create_speech_analysis_agent()

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
    dimension: str
    response_options: List[str]
    vocabulary: VocabularyWord

class QuestionOnlyResponse(BaseModel):
    question: str
    dimension: str = "Basic Preferences"

class ContinueConversationRequest(BaseModel):
    topic: str
    user_id: str
    previous_question: str
    user_response: Optional[str] = None
    difficulty_level: int = 1

class ConversationDetailsRequest(BaseModel):
    question: str
    topic: str
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
            "message": "Login successful"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during login: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")

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
        
        return {
            "question": question_text,
            "dimension": dimension
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
            f"The follow-up should:\n"
            f"- Use 'Acknowledgement + Question' format\n"
            f"- Be about the specific things mentioned in the user's response\n"
            f"- Adapt to the {dimension} dimension\n"
            f"- Be natural and conversational for a teen"
        )
        
        # Run conversation agent (it will use the tools)
        response = conversation_agent.run(prompt)
        question_text = response.content.strip()
        
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
        
        print(f"Generated follow-up question: {question_text}")
            
        return {"question": question_text, "dimension": dimension}
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
        
        return {
            "response_options": options,
            "vocabulary": vocab_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating conversation details: {str(e)}")

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
    expected_response: Optional[str] = Form(None)
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
