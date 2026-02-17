"""
Tools package for ConvoBridge backend.
Contains utility tools for speech processing, conversation management, and other operations.
"""

from .speech_transcription_tool import transcribe_audio
from .conversation_tools import get_context, generate_followup_question, create_conversation_context
from .generate_response_options import generate_response_options
from .set_sentence_difficulty import set_sentence_difficulty, get_current_difficulty_level
from .text_to_speech import text_to_speech, text_to_speech_file, text_to_speech_base64

__all__ = [
    'transcribe_audio',
    'get_context',
    'generate_followup_question',
    'create_conversation_context',
    'generate_response_options',
    'set_sentence_difficulty',
    'get_current_difficulty_level',
    'text_to_speech',
    'text_to_speech_file',
    'text_to_speech_base64',
]
