"""
Database module for ConvoBridge - Supabase integration
Handles all database operations for users, sessions, and conversation tracking.
"""

from supabase import create_client, Client
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv

# Load .env file - check multiple locations (same as main.py)
backend_dir = Path(__file__).parent
root_dir = backend_dir.parent

# Try loading from multiple locations (in order of preference)
env_locations = [
    backend_dir / '.env',  # backend/.env (preferred)
    root_dir / '.env',     # root/.env (fallback)
]

env_loaded = False
for env_path in env_locations:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        env_loaded = True
        break

# If no .env file found, try default load_dotenv() behavior
if not env_loaded:
    load_dotenv()  # This will look in current directory and parent directories

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY') or os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("\n" + "="*60)
    print("WARNING: Supabase credentials not found in environment variables.")
    print("Please set SUPABASE_URL and SUPABASE_ANON_KEY in your .env file.")
    print("="*60 + "\n")
    supabase: Optional[Client] = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"[OK] Supabase client initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Supabase client: {e}")
        supabase = None


def get_user_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a user by name from the database.
    
    Args:
        name: The user's name
        
    Returns:
        User dictionary with id, name, created_at, updated_at, or None if not found
    """
    if not supabase:
        return None
    
    try:
        response = supabase.table('users').select('*').eq('name', name).limit(1).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error retrieving user by name: {e}")
        return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a user by ID from the database.
    
    Args:
        user_id: The user's UUID
        
    Returns:
        User dictionary with id, name, created_at, updated_at, or None if not found
    """
    if not supabase:
        return None
    
    try:
        response = supabase.table('users').select('*').eq('id', user_id).limit(1).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error retrieving user by ID: {e}")
        return None


def create_user(name: str) -> Optional[Dict[str, Any]]:
    """
    Create a new user in the database.
    If user already exists, return the existing user.
    
    Args:
        name: The user's name
        
    Returns:
        User dictionary with id, name, created_at, updated_at, or None if creation failed
    """
    if not supabase:
        return None
    
    # Check if user already exists
    existing_user = get_user_by_name(name)
    if existing_user:
        print(f"User '{name}' already exists with ID: {existing_user['id']}")
        return existing_user
    
    try:
        # Create new user
        response = supabase.table('users').insert({
            'name': name
        }).execute()
        
        if response.data and len(response.data) > 0:
            user = response.data[0]
            print(f"Created new user: {user['name']} (ID: {user['id']})")
            return user
        return None
    except Exception as e:
        print(f"Error creating user: {e}")
        # If error is due to duplicate (user was created between check and insert)
        # Try to retrieve the existing user
        existing_user = get_user_by_name(name)
        if existing_user:
            return existing_user
        return None


def create_session(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Create a new session for a user.
    
    Args:
        user_id: The user's UUID
        
    Returns:
        Session dictionary with id, user_id, started_at, status, or None if creation failed
    """
    if not supabase:
        return None
    
    try:
        response = supabase.table('sessions').insert({
            'user_id': user_id,
            'status': 'active'
        }).execute()
        
        if response.data and len(response.data) > 0:
            session = response.data[0]
            print(f"Created new session: {session['id']} for user {user_id}")
            return session
        return None
    except Exception as e:
        print(f"Error creating session: {e}")
        return None


def get_or_create_session_topic(session_id: str, topic_name: str) -> Optional[Dict[str, Any]]:
    """
    Get or create a session_topic record.
    Returns existing record if it exists, otherwise creates a new one.
    
    Args:
        session_id: The session UUID
        topic_name: The topic name (e.g., 'Gaming', 'Weekend plans')
        
    Returns:
        Session topic dictionary or None if operation failed
    """
    if not supabase:
        return None
    
    try:
        # Try to get existing session topic (case-insensitive)
        # Get all topics for this session and filter case-insensitively
        all_topics_response = supabase.table('session_topics')\
            .select('*')\
            .eq('session_id', session_id)\
            .execute()
        
        if all_topics_response.data:
            # Find matching topic (case-insensitive)
            for topic in all_topics_response.data:
                if topic.get('topic_name', '').lower() == topic_name.lower():
                    return topic
        
        # Create new session topic (use the provided topic_name as-is)
        response = supabase.table('session_topics').insert({
            'session_id': session_id,
            'topic_name': topic_name,
            'turn_count': 0
        }).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting/creating session topic: {e}")
        return None


def is_first_question_for_topic(user_id: str, topic_name: str) -> bool:
    """
    Check if this is the first question for a topic for a given user.
    Checks across all sessions for the user.
    
    Args:
        user_id: The user's UUID
        topic_name: The topic name
    
    Returns:
        True if this is the first question for this topic, False otherwise
    """
    if not supabase:
        print("Warning: Supabase not configured, defaulting to first question")
        return True  # Default to True if database not available
    
    try:
        # Get all sessions for this user
        sessions_response = supabase.table('sessions').select('id').eq('user_id', user_id).execute()
        
        if not sessions_response.data:
            return True  # No sessions, so this is first
        
        session_ids = [s['id'] for s in sessions_response.data]
        
        # Check if any session has this topic with turn_count > 0
        # Use case-insensitive matching
        for session_id in session_ids:
            # Get all topics for this session and filter case-insensitively
            topics_response = supabase.table('session_topics')\
                .select('turn_count, topic_name')\
                .eq('session_id', session_id)\
                .execute()
            
            if topics_response.data:
                # Find matching topic (case-insensitive)
                for topic in topics_response.data:
                    if topic.get('topic_name', '').lower() == topic_name.lower():
                        turn_count = topic.get('turn_count', 0)
                        if turn_count > 0:
                            return False  # Found a topic with turns, so not first
        
        return True  # No turns found for this topic
    except Exception as e:
        print(f"Error checking first question: {e}")
        return True  # Default to True on error


def end_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    End a session by updating the ended_at timestamp and setting status to 'completed'.
    This is called when a user logs out.
    
    Args:
        session_id: The session UUID to end
    
    Returns:
        Updated session dictionary with ended_at and status='completed', or None if operation failed
    """
    if not supabase:
        print("Warning: Supabase not configured, cannot end session")
        return None
    
    try:
        # Update the session with ended_at timestamp and status
        response = supabase.table('sessions').update({
            'ended_at': datetime.now().isoformat(),
            'status': 'completed'
        }).eq('id', session_id).execute()
        
        if response.data and len(response.data) > 0:
            session = response.data[0]
            print(f"Session {session_id} ended successfully at {session.get('ended_at')}")
            return session
        return None
    except Exception as e:
        print(f"Error ending session: {e}")
        return None


def get_active_session(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the active session for a user.
    
    Args:
        user_id: The user's UUID
    
    Returns:
        Active session dictionary or None if not found
    """
    if not supabase:
        return None
    
    try:
        response = supabase.table('sessions')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('status', 'active')\
            .order('started_at', desc=True)\
            .limit(1)\
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting active session: {e}")
        return None


def is_returning_user(user_id: str) -> bool:
    """
    Check if a user is a returning user by checking if they have previous sessions with conversation turns.
    A user is considered returning if they have at least one completed or active session with conversation activity.
    
    Args:
        user_id: The user's UUID
    
    Returns:
        True if user has previous conversation activity (returning user), False otherwise (first-time user)
    """
    if not supabase:
        return False
    
    try:
        # Check if user has any sessions with conversation turns
        # Get all sessions for this user
        sessions_response = supabase.table('sessions').select('id').eq('user_id', user_id).execute()
        
        if not sessions_response.data:
            return False  # No sessions = first-time user
        
        session_ids = [s['id'] for s in sessions_response.data]
        
        # Check if any session has conversation turns
        for session_id in session_ids:
            # Get session topics for this session
            topics_response = supabase.table('session_topics').select('id').eq('session_id', session_id).execute()
            
            if not topics_response.data:
                continue
            
            for topic in topics_response.data:
                topic_id = topic['id']
                # Check if this topic has any conversation turns
                turns_response = supabase.table('conversation_turns')\
                    .select('id')\
                    .eq('session_topic_id', topic_id)\
                    .limit(1)\
                    .execute()
                
                if turns_response.data and len(turns_response.data) > 0:
                    return True  # Found conversation activity = returning user
        
        return False  # No conversation turns found = first-time user
    except Exception as e:
        print(f"Error checking if returning user: {e}")
        return False


def get_last_topic_for_user(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the last topic the user worked on by finding the most recent conversation_turn.
    Returns the topic name and related information.
    
    Args:
        user_id: The user's UUID
    
    Returns:
        Dictionary with topic_name, last_turn info, or None if no previous topics
    """
    if not supabase:
        return None
    
    try:
        # Get all sessions for this user
        sessions_response = supabase.table('sessions').select('id').eq('user_id', user_id).execute()
        
        if not sessions_response.data:
            return None
        
        session_ids = [s['id'] for s in sessions_response.data]
        
        # Get the most recent conversation_turn across all sessions
        # Join through session_topics to get topic_name
        most_recent_turn = None
        most_recent_time = None
        
        for session_id in session_ids:
            # Get session topics for this session
            topics_response = supabase.table('session_topics').select('id, topic_name').eq('session_id', session_id).execute()
            
            if not topics_response.data:
                continue
            
            for topic in topics_response.data:
                topic_id = topic['id']
                # Get most recent turn for this topic
                turns_response = supabase.table('conversation_turns')\
                    .select('*')\
                    .eq('session_topic_id', topic_id)\
                    .order('question_asked_at', desc=True)\
                    .limit(1)\
                    .execute()
                
                if turns_response.data and len(turns_response.data) > 0:
                    turn = turns_response.data[0]
                    turn_time = turn.get('question_asked_at')
                    
                    if turn_time and (most_recent_time is None or turn_time > most_recent_time):
                        most_recent_turn = turn
                        most_recent_time = turn_time
                        most_recent_turn['topic_name'] = topic['topic_name']
        
        return most_recent_turn
    except Exception as e:
        print(f"Error getting last topic for user: {e}")
        return None


def get_last_conversation_turn(session_topic_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the last conversation turn for a session topic.
    
    Args:
        session_topic_id: The session topic UUID
    
    Returns:
        Last conversation turn dictionary or None if not found
    """
    if not supabase:
        return None
    
    try:
        response = supabase.table('conversation_turns')\
            .select('*')\
            .eq('session_topic_id', session_topic_id)\
            .order('turn_number', desc=True)\
            .limit(1)\
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting last conversation turn: {e}")
        return None


def get_conversation_history_for_user_topic(user_id: str, topic_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get conversation history for a user-topic combination across all sessions.
    Returns the most recent conversation turns (questions and responses) for that topic.
    
    Args:
        user_id: The user's UUID
        topic_name: The topic name (e.g., 'Gaming', 'Weekend plans', 'food', 'Food')
        limit: Maximum number of recent turns to retrieve (default: 5)
    
    Returns:
        List of conversation turn dictionaries, ordered by most recent first.
        Each turn includes question, user_response, dimension, and turn_number.
    """
    if not supabase:
        return []
    
    try:
        # Get all sessions for this user
        sessions_response = supabase.table('sessions').select('id').eq('user_id', user_id).execute()
        
        if not sessions_response.data:
            print(f"No sessions found for user {user_id}")
            return []  # No sessions, so no history
        
        session_ids = [s['id'] for s in sessions_response.data]
        print(f"Found {len(session_ids)} sessions for user {user_id}")
        
        # Get all session_topics for this topic across all sessions
        # Try both exact match and case-insensitive match
        all_turns = []
        for session_id in session_ids:
            # Get session topics - try exact match first, then case-insensitive
            topics_response = supabase.table('session_topics')\
                .select('id, topic_name')\
                .eq('session_id', session_id)\
                .execute()
            
            if not topics_response.data:
                continue
            
            # Filter topics by case-insensitive match
            matching_topics = [
                t for t in topics_response.data 
                if t.get('topic_name', '').lower() == topic_name.lower()
            ]
            
            print(f"Session {session_id}: Found {len(matching_topics)} matching topics for '{topic_name}'")
            
            for topic in matching_topics:
                topic_id = topic['id']
                # Get conversation turns for this topic
                turns_response = supabase.table('conversation_turns')\
                    .select('id, turn_number, question, user_response, dimension, question_asked_at')\
                    .eq('session_topic_id', topic_id)\
                    .order('turn_number', desc=False)\
                    .execute()
                
                if turns_response.data:
                    print(f"Found {len(turns_response.data)} turns for topic {topic_id}")
                    for turn in turns_response.data:
                        print(f"  Turn {turn.get('turn_number')}: Q='{turn.get('question', '')[:50]}...' A='{turn.get('user_response', '')[:50] if turn.get('user_response') else 'None'}...'")
                    all_turns.extend(turns_response.data)
        
        # Sort all turns by question_asked_at (most recent first) and limit
        all_turns.sort(key=lambda x: x.get('question_asked_at', ''), reverse=True)
        
        # Return the most recent turns (up to limit)
        result = all_turns[:limit]
        print(f"Returning {len(result)} conversation turns for user {user_id}, topic {topic_name}")
        return result
    except Exception as e:
        print(f"Error getting conversation history for user {user_id}, topic {topic_name}: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_current_session_topic(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the current active session topic (most recently active).
    
    Args:
        session_id: The session UUID
    
    Returns:
        Current session topic dictionary or None if not found
    """
    if not supabase:
        return None
    
    try:
        response = supabase.table('session_topics')\
            .select('*')\
            .eq('session_id', session_id)\
            .order('last_activity_at', desc=True)\
            .limit(1)\
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting current session topic: {e}")
        return None


def get_current_turn(session_topic_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the current (most recent) conversation turn for a session topic.
    
    Args:
        session_topic_id: The session topic UUID
    
    Returns:
        Current conversation turn dictionary or None if not found
    """
    return get_last_conversation_turn(session_topic_id)


def create_conversation_turn(
    session_topic_id: str,
    turn_number: int,
    dimension: str,
    difficulty_level: int,
    question: str
) -> Optional[Dict[str, Any]]:
    """
    Create a new conversation turn record.
    
    Args:
        session_topic_id: The session topic UUID
        turn_number: Sequential turn number within the topic
        dimension: Conversation dimension (e.g., 'Basic Preferences', 'Social Context')
        difficulty_level: Difficulty level (1, 2, 3, etc.)
        question: The question text
    
    Returns:
        Created conversation turn dictionary with id, or None if creation failed
    """
    if not supabase:
        return None
    
    try:
        response = supabase.table('conversation_turns').insert({
            'session_topic_id': session_topic_id,
            'turn_number': turn_number,
            'dimension': dimension,
            'difficulty_level': difficulty_level,
            'question': question
        }).execute()
        
        if response.data and len(response.data) > 0:
            turn = response.data[0]
            print(f"Created conversation turn {turn_number} for session_topic {session_topic_id} (ID: {turn['id']})")
            return turn
        return None
    except Exception as e:
        print(f"Error creating conversation turn: {e}")
        return None


def update_conversation_turn_with_response(
    turn_id: str,
    user_response: str,
    response_type: str,
    selected_option_index: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Update a conversation turn with the user's response.
    
    Args:
        turn_id: The conversation turn UUID
        user_response: The user's response text
        response_type: Type of response ('selected_option', 'custom_speech', 'custom_text')
        selected_option_index: Index of selected option (0, 1, or 2) if response_type is 'selected_option'
    
    Returns:
        Updated conversation turn dictionary or None if update failed
    """
    if not supabase:
        return None
    
    try:
        update_data = {
            'user_response': user_response,
            'response_type': response_type,
            'response_received_at': datetime.now().isoformat()
        }
        
        if selected_option_index is not None:
            update_data['selected_option_index'] = selected_option_index
        
        response = supabase.table('conversation_turns')\
            .update(update_data)\
            .eq('id', turn_id)\
            .execute()
        
        if response.data and len(response.data) > 0:
            print(f"Updated conversation turn {turn_id} with user response")
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error updating conversation turn with response: {e}")
        return None


def update_conversation_turn_with_speech_analysis(
    turn_id: str,
    transcript: str,
    clarity_score: float,
    wer_estimate: Optional[float],
    pace_wpm: int,
    filler_words: List[str],
    feedback: str,
    strengths: List[str],
    suggestions: List[str]
) -> Optional[Dict[str, Any]]:
    """
    Update a conversation turn with speech analysis results.
    
    Args:
        turn_id: The conversation turn UUID
        transcript: Transcribed speech text
        clarity_score: Clarity score (0.0 to 1.0)
        wer_estimate: Word Error Rate estimate (0.0 to 1.0, optional)
        pace_wpm: Speaking pace in words per minute
        filler_words: List of filler words found
        feedback: Encouraging feedback text
        strengths: List of strengths identified
        suggestions: List of suggestions for improvement
    
    Returns:
        Updated conversation turn dictionary or None if update failed
    """
    if not supabase:
        return None
    
    try:
        update_data = {
            'transcript': transcript,
            'clarity_score': clarity_score,
            'pace_wpm': pace_wpm,
            'filler_words': filler_words,
            'feedback': feedback,
            'strengths': strengths,
            'suggestions': suggestions
        }
        
        if wer_estimate is not None:
            update_data['wer_estimate'] = wer_estimate
        
        response = supabase.table('conversation_turns')\
            .update(update_data)\
            .eq('id', turn_id)\
            .execute()
        
        if response.data and len(response.data) > 0:
            print(f"Updated conversation turn {turn_id} with speech analysis")
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error updating conversation turn with speech analysis: {e}")
        return None


def save_response_options(
    conversation_turn_id: str,
    options: List[str]
) -> Optional[List[Dict[str, Any]]]:
    """
    Save response options for a conversation turn.
    
    Args:
        conversation_turn_id: The conversation turn UUID
        options: List of response option texts (should be 2-3 options)
    
    Returns:
        List of saved response option dictionaries or None if save failed
    """
    if not supabase:
        return None
    
    try:
        # Prepare options for insertion
        options_data = []
        for index, option_text in enumerate(options[:3]):  # Limit to 3 options
            options_data.append({
                'conversation_turn_id': conversation_turn_id,
                'option_index': index,
                'option_text': option_text
            })
        
        if not options_data:
            return None
        
        response = supabase.table('response_options').insert(options_data).execute()
        
        if response.data:
            print(f"Saved {len(response.data)} response options for turn {conversation_turn_id}")
            return response.data
        return None
    except Exception as e:
        print(f"Error saving response options: {e}")
        return None


def get_response_options_for_turn(turn_id: str) -> List[Dict[str, Any]]:
    """
    Get all response options for a conversation turn.
    
    Args:
        turn_id: The conversation turn UUID
    
    Returns:
        List of response option dictionaries, ordered by option_index
    """
    if not supabase:
        return []
    
    try:
        response = supabase.table('response_options')\
            .select('*')\
            .eq('conversation_turn_id', turn_id)\
            .order('option_index', desc=False)\
            .execute()
        
        if response.data:
            return response.data
        return []
    except Exception as e:
        print(f"Error getting response options for turn: {e}")
        return []


def save_vocabulary_word(
    conversation_turn_id: str,
    word: str,
    word_type: str,
    definition: str,
    example: str
) -> Optional[Dict[str, Any]]:
    """
    Save a vocabulary word for a conversation turn.
    
    Args:
        conversation_turn_id: The conversation turn UUID
        word: The vocabulary word
        word_type: Type of word (e.g., 'noun', 'verb', 'adjective')
        definition: Word definition
        example: Example sentence using the word
    
    Returns:
        Saved vocabulary word dictionary or None if save failed
    """
    if not supabase:
        return None
    
    try:
        response = supabase.table('vocabulary_words').insert({
            'conversation_turn_id': conversation_turn_id,
            'word': word,
            'word_type': word_type,
            'definition': definition,
            'example': example
        }).execute()
        
        if response.data and len(response.data) > 0:
            vocab = response.data[0]
            print(f"Saved vocabulary word '{word}' for turn {conversation_turn_id}")
            return vocab
        return None
    except Exception as e:
        print(f"Error saving vocabulary word: {e}")
        return None


if __name__ == "__main__":
    # Test database connection
    print("Testing Supabase connection...")
    if supabase:
        print("✓ Supabase client is initialized")
        # Test query
        try:
            response = supabase.table('users').select('count').execute()
            print("✓ Database connection successful")
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
    else:
        print("✗ Supabase client not initialized")
