"""
Database module for ConvoBridge - Supabase integration
Handles all database operations for users, sessions, and conversation tracking.
"""

from supabase import create_client, Client
from typing import Optional, Dict, Any
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
        # Try to get existing session topic
        response = supabase.table('session_topics').select('*').eq('session_id', session_id).eq('topic_name', topic_name).limit(1).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        
        # Create new session topic
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
        for session_id in session_ids:
            topic_response = supabase.table('session_topics').select('turn_count').eq('session_id', session_id).eq('topic_name', topic_name).limit(1).execute()
            
            if topic_response.data and len(topic_response.data) > 0:
                turn_count = topic_response.data[0].get('turn_count', 0)
                if turn_count > 0:
                    return False  # Found a topic with turns, so not first
        
        return True  # No turns found for this topic
    except Exception as e:
        print(f"Error checking first question: {e}")
        return True  # Default to True on error


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
