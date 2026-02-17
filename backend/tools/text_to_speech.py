"""
Text-to-Speech Tool - Converts text to speech using OpenAI's TTS API directly
This tool generates audio from text for reading questions aloud.
"""

import base64
from typing import Optional
from pathlib import Path
import os
import tempfile
from dotenv import load_dotenv
from openai import OpenAI

# Load .env file from the backend directory
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / '.env'
load_dotenv(dotenv_path=env_path)

# Initialize OpenAI client
openai_client = None
try:
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        openai_client = OpenAI(api_key=api_key)
        print("[TTS] OpenAI client initialized successfully")
    else:
        print("[TTS] WARNING: OPENAI_API_KEY not found")
except Exception as e:
    print(f"[TTS] ERROR: Failed to initialize OpenAI client: {e}")


def text_to_speech(
    text: str,
    voice: str = "nova",
    model: str = "tts-1-hd",
    output_format: str = "mp3"
) -> Optional[bytes]:
    """
    Convert text to speech using OpenAI's TTS API directly.
    
    Args:
        text: The text to convert to speech
        voice: The voice to use (default: "nova"). Options: "alloy", "echo", "fable", "onyx", "nova", "shimmer"
        model: The TTS model to use (default: "tts-1-hd"). Options: "tts-1", "tts-1-hd"
        output_format: The audio format (default: "mp3"). Options: "mp3", "opus", "aac", "flac", "wav", "pcm"
    
    Returns:
        Audio data as bytes, or None if generation failed
    """
    try:
        if not openai_client:
            print("[TTS] ERROR: OpenAI client not initialized")
            return None
        
        if not text or not text.strip():
            print("[TTS] ERROR: Empty text provided")
            return None
        
        print(f"[TTS] Generating speech for text: {text[:50]}...")
        print(f"[TTS] Using voice: {voice}, model: {model}, format: {output_format}")
        
        # Call OpenAI TTS API directly
        response = openai_client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format=output_format
        )
        
        # Read the audio data
        audio_data = response.content
        
        if audio_data:
            print(f"[TTS] Successfully generated audio ({len(audio_data)} bytes)")
            return audio_data
        else:
            print("[TTS] ERROR: No audio data in response")
            return None
        
    except Exception as e:
        print(f"[TTS] Error generating speech: {e}")
        import traceback
        traceback.print_exc()
        return None


def text_to_speech_file(
    text: str,
    output_path: Optional[str] = None,
    voice: str = "nova",
    model: str = "tts-1-hd",
    output_format: str = "mp3"
) -> Optional[str]:
    """
    Convert text to speech and save to a file.
    
    Args:
        text: The text to convert to speech
        output_path: Optional path to save the audio file. If None, creates a temp file.
        voice: The voice to use (default: "nova")
        model: The TTS model to use (default: "tts-1-hd")
        output_format: The audio format (default: "mp3")
    
    Returns:
        Path to the saved audio file, or None if generation failed
    """
    try:
        # Generate audio
        audio_data = text_to_speech(text, voice=voice, model=model, output_format=output_format)
        
        if not audio_data:
            return None
        
        # Determine output path
        if output_path is None:
            # Create temp file
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"tts_{os.getpid()}_{hash(text) % 10000}.{output_format}")
        
        # Ensure directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save audio data
        with open(output_path, 'wb') as f:
            f.write(audio_data)
        
        return output_path
        
    except Exception as e:
        print(f"Error saving speech to file: {e}")
        import traceback
        traceback.print_exc()
        return None


def text_to_speech_base64(
    text: str,
    voice: str = "nova",
    model: str = "tts-1-hd",
    output_format: str = "mp3"
) -> Optional[str]:
    """
    Convert text to speech and return as base64-encoded string.
    
    Args:
        text: The text to convert to speech
        voice: The voice to use (default: "nova")
        model: The TTS model to use (default: "tts-1-hd")
        output_format: The audio format (default: "mp3")
    
    Returns:
        Base64-encoded audio string, or None if generation failed
    """
    try:
        # Generate audio
        audio_data = text_to_speech(text, voice=voice, model=model, output_format=output_format)
        
        if not audio_data:
            return None
        
        # Encode to base64
        base64_audio = base64.b64encode(audio_data).decode("utf-8")
        return base64_audio
        
    except Exception as e:
        print(f"Error encoding speech to base64: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Test the text-to-speech tool
    print("Text-to-Speech Tool - Testing...\n")
    
    test_text = "Hello! This is a test of the text-to-speech functionality."
    
    # Test 1: Generate audio data
    print("Test 1: Generating audio data...")
    audio_data = text_to_speech(test_text)
    if audio_data:
        print(f"✓ Generated audio data ({len(audio_data)} bytes)")
    else:
        print("✗ Failed to generate audio data")
    
    # Test 2: Save to file
    print("\nTest 2: Saving to file...")
    file_path = text_to_speech_file(test_text, output_format="mp3")
    if file_path:
        print(f"✓ Saved audio to: {file_path}")
        # Clean up
        try:
            os.unlink(file_path)
            print(f"✓ Cleaned up temp file")
        except:
            pass
    else:
        print("✗ Failed to save audio to file")
    
    # Test 3: Base64 encoding
    print("\nTest 3: Base64 encoding...")
    base64_audio = text_to_speech_base64(test_text)
    if base64_audio:
        print(f"✓ Generated base64 audio ({len(base64_audio)} characters)")
    else:
        print("✗ Failed to generate base64 audio")
