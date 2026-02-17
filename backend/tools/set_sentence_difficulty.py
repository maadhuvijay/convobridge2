"""
Set Sentence Difficulty Tool - Tool for ConvoBridge Response Agent
This tool increases the response sentence difficulty level if the user's average clarity score
is > 85% across the last 5 conversation turns.
"""

from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
import os

# Import database module for accessing Supabase
try:
    from database import supabase
except ImportError:
    supabase = None

# Load .env file from the backend directory
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / '.env'
load_dotenv(dotenv_path=env_path)


def set_sentence_difficulty(
    user_id: str,
    session_topic_id: str,
    current_difficulty_level: int = 1
) -> Dict[str, Any]:
    """
    Check if the user's average clarity score is > 85% across the last 5 conversation turns.
    If so, increase the sentence difficulty level.
    
    The difficulty levels are:
    - Level 1: Simple and direct responses (default starting level)
    - Level 2: Medium complexity with some detail
    - Level 3: More elaborate with reasoning (2-3 sentences with complex high school vocabulary)
    
    Args:
        user_id: The user's UUID
        session_topic_id: The session_topic UUID to check turns for
        current_difficulty_level: The current sentence difficulty level (1, 2, or 3). Defaults to 1.
    
    Returns:
        A dictionary with the following keys:
        - new_difficulty_level: The updated difficulty level (same or increased)
        - previous_difficulty_level: The previous difficulty level
        - average_clarity_score: The average clarity score across last 5 turns (0.0 to 1.0)
        - turns_checked: Number of turns that had clarity scores (0 to 5)
        - difficulty_increased: Boolean indicating if difficulty was increased
        - message: A descriptive message about what happened
        
    Example:
        >>> result = set_sentence_difficulty(
        ...     user_id="123e4567-e89b-12d3-a456-426614174000",
        ...     session_topic_id="123e4567-e89b-12d3-a456-426614174001",
        ...     current_difficulty_level=1
        ... )
        >>> result['difficulty_increased']
        True or False
        >>> result['new_difficulty_level'] in [1, 2, 3]
        True
    """
    # Validate current difficulty level
    if current_difficulty_level < 1:
        current_difficulty_level = 1
    elif current_difficulty_level > 3:
        current_difficulty_level = 3
    
    # Initialize result
    result = {
        "new_difficulty_level": current_difficulty_level,
        "previous_difficulty_level": current_difficulty_level,
        "average_clarity_score": 0.0,
        "turns_checked": 0,
        "difficulty_increased": False,
        "message": ""
    }
    
    # Check if database is available
    if not supabase:
        result["message"] = "Database not available. Difficulty level unchanged."
        return result
    
    try:
        # Get the last 5 conversation turns for this session_topic_id
        # Order by turn_number descending to get the most recent turns
        response = supabase.table('conversation_turns')\
            .select('clarity_score, turn_number')\
            .eq('session_topic_id', session_topic_id)\
            .not_.is_('clarity_score', 'null')\
            .order('turn_number', desc=True)\
            .limit(5)\
            .execute()
        
        if not response.data:
            result["message"] = "No conversation turns with clarity scores found. Difficulty level unchanged."
            return result
        
        # Extract clarity scores (they are stored as DECIMAL, so they should be floats)
        clarity_scores = []
        for turn in response.data:
            clarity_score = turn.get('clarity_score')
            if clarity_score is not None:
                # Convert to float if it's not already
                try:
                    score = float(clarity_score)
                    # Clarity scores are stored as 0.00 to 1.00 (0% to 100%)
                    clarity_scores.append(score)
                except (ValueError, TypeError):
                    continue
        
        result["turns_checked"] = len(clarity_scores)
        
        # Need at least 5 turns with clarity scores to evaluate
        if len(clarity_scores) < 5:
            result["message"] = f"Only {len(clarity_scores)} turns with clarity scores found. Need 5 turns to evaluate. Difficulty level unchanged."
            result["average_clarity_score"] = sum(clarity_scores) / len(clarity_scores) if clarity_scores else 0.0
            return result
        
        # Calculate average clarity score (using last 5 turns)
        average_clarity = sum(clarity_scores) / len(clarity_scores)
        result["average_clarity_score"] = average_clarity
        
        # Check if average clarity > 85% (0.85)
        if average_clarity > 0.85:
            # Increase difficulty level (but don't exceed level 3)
            if current_difficulty_level < 3:
                new_level = current_difficulty_level + 1
                result["new_difficulty_level"] = new_level
                result["difficulty_increased"] = True
                result["message"] = (
                    f"Average clarity score ({average_clarity:.1%}) exceeds 85%. "
                    f"Difficulty level increased from {current_difficulty_level} to {new_level}."
                )
            else:
                result["message"] = (
                    f"Average clarity score ({average_clarity:.1%}) exceeds 85%, "
                    f"but difficulty is already at maximum level (3)."
                )
        else:
            result["message"] = (
                f"Average clarity score ({average_clarity:.1%}) is below 85% threshold. "
                f"Difficulty level remains at {current_difficulty_level}."
            )
        
        return result
        
    except Exception as e:
        result["message"] = f"Error checking clarity scores: {str(e)}. Difficulty level unchanged."
        return result


def get_current_difficulty_level(
    user_id: str,
    session_topic_id: str
) -> int:
    """
    Get the current sentence difficulty level for a user's session topic.
    Checks the most recent conversation turn to get the current difficulty level.
    
    Args:
        user_id: The user's UUID
        session_topic_id: The session_topic UUID
    
    Returns:
        The current difficulty level (1, 2, or 3). Defaults to 1 if not found.
    """
    if not supabase:
        return 1  # Default to Level 1 if database not available
    
    try:
        # Get the most recent conversation turn for this session_topic
        response = supabase.table('conversation_turns')\
            .select('difficulty_level')\
            .eq('session_topic_id', session_topic_id)\
            .order('turn_number', desc=True)\
            .limit(1)\
            .execute()
        
        if response.data and len(response.data) > 0:
            difficulty = response.data[0].get('difficulty_level', 1)
            # Validate difficulty level
            if isinstance(difficulty, int) and 1 <= difficulty <= 3:
                return difficulty
        
        return 1  # Default to Level 1
    except Exception as e:
        print(f"Error getting current difficulty level: {e}")
        return 1  # Default to Level 1 on error


if __name__ == "__main__":
    # Simple test
    print("Set Sentence Difficulty Tool - Ready!\n")
    
    # Test with mock data (will fail if database not configured, but shows the structure)
    print("Testing set_sentence_difficulty function...")
    print("Note: This requires a valid user_id and session_topic_id in the database.")
    print()
    
    # Example usage (commented out as it requires actual database entries)
    # result = set_sentence_difficulty(
    #     user_id="123e4567-e89b-12d3-a456-426614174000",
    #     session_topic_id="123e4567-e89b-12d3-a456-426614174001",
    #     current_difficulty_level=1
    # )
    # print("Result:")
    # print(f"  Previous Level: {result['previous_difficulty_level']}")
    # print(f"  New Level: {result['new_difficulty_level']}")
    # print(f"  Average Clarity: {result['average_clarity_score']:.1%}")
    # print(f"  Turns Checked: {result['turns_checked']}")
    # print(f"  Increased: {result['difficulty_increased']}")
    # print(f"  Message: {result['message']}")
