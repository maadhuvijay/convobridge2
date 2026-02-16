"""
Speech Transcription Tool - Tool for ConvoBridge
This tool handles audio file transcription using Agno's audio capabilities.
It transcribes audio files to text using OpenAI's audio-enabled models.
"""

from pathlib import Path
from typing import Optional, Union
from agno.agent import Agent
from agno.media import Audio
from agno.models.openai import OpenAIChat
import os
from dotenv import load_dotenv

# Load .env file from the backend directory
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / '.env'
load_dotenv(dotenv_path=env_path)

def transcribe_audio(
    audio_data: Optional[bytes] = None,
    audio_filepath: Optional[Union[str, Path]] = None,
    audio_format: str = "mp3"
) -> str:
    """
    Transcribe audio to text using Agno's audio transcription capabilities.
    
    Args:
        audio_data: Audio content as bytes (optional)
        audio_filepath: Path to audio file (optional)
        audio_format: Format of the audio file (e.g., "mp3", "wav", "m4a")
    
    Returns:
        Transcribed text as a string
    
    Raises:
        ValueError: If neither audio_data nor audio_filepath is provided
    """
    if not audio_data and not audio_filepath:
        raise ValueError("Either audio_data or audio_filepath must be provided")
    
    # Create a transcription agent with audio capabilities
    # Note: gpt-4o-audio-preview requires OpenAIChat (not OpenAIResponses)
    # as it's not supported with the Responses API
    transcription_agent = Agent(
        model=OpenAIChat(id="gpt-4o-audio-preview", modalities=["text"]),
        markdown=False,
    )
    
    # Prepare audio input
    if audio_data:
        audio_input = Audio(content=audio_data, format=audio_format)
    else:
        audio_path = Path(audio_filepath) if isinstance(audio_filepath, str) else audio_filepath
        audio_input = Audio(filepath=audio_path, format=audio_format)
    
    # Transcribe the audio
    try:
        prompt = "Transcribe exactly what was said in this audio. Return only the transcribed text, nothing else."
        response = transcription_agent.run(prompt, audio=[audio_input])
        
        if not response or not response.content:
            raise ValueError("Transcription agent returned empty response")
        
        return response.content.strip()
    except Exception as e:
        error_msg = f"Error transcribing audio: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        raise RuntimeError(error_msg) from e

if __name__ == "__main__":
    # Simple test
    print("Speech Transcription Tool - Ready!")
    print("This tool transcribes audio files to text.\n")
    print("Usage:")
    print("  transcribe_audio(audio_filepath='path/to/audio.mp3')")
    print("  transcribe_audio(audio_data=audio_bytes, audio_format='mp3')")
