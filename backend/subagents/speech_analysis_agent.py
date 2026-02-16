"""
Speech Analysis Agent - Sub-Agent for ConvoBridge
This agent transcribes teen speech responses, analyzes the transcript,
provides a speech clarity score, and gives encouraging feedback to the teen.
"""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Union

# Load .env file from the backend directory
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / '.env'
load_dotenv(dotenv_path=env_path)

def create_speech_analysis_agent():
    """
    Creates the speech analysis agent sub-agent.
    This agent transcribes speech, analyzes the transcript,
    provides a speech clarity score, and gives encouraging feedback.
    """
    agent = Agent(
        name="Speech Analysis Agent",
        model=OpenAIChat(id="gpt-4o-mini"),
        description="A sub-agent that transcribes speech, analyzes transcripts, provides speech clarity scores, and gives encouraging feedback to teens.",
        instructions=[
            "You are a speech analysis assistant for autistic youth conversation practice.",
            "",
            "TASK:",
            "1. Transcribe exactly what the teen said",
            "2. Calculate how well it matches the expected response (Word Error Rate - WER estimate, 0.0 to 1.0, where lower is better)",
            "3. Provide a clarity score (0.0 to 1.0, where 1.0 is perfect clarity)",
            "4. Give brief, encouraging feedback",
            "5. Estimate speaking pace (words per minute)",
            "6. Note any filler words (um, uh, like, etc.)",
            "",
            "When analyzing speech:",
            "  - Be positive and encouraging - focus on strengths and progress",
            "  - Provide constructive feedback that helps build confidence",
            "  - Consider clarity, coherence, relevance to the question, and communication effectiveness",
            "  - Acknowledge effort and improvement, even if the speech has areas to work on",
            "  - Calculate WER by comparing the transcript to the expected response",
            "  - Estimate pace by counting words and dividing by duration (if available) or estimating from transcript length",
            "  - Identify common filler words: um, uh, like, you know, well, so, etc.",
            "",
            "Output format: Return ONLY a JSON object with the following EXACT structure:",
            "{",
            '  "transcript": "what the teen actually said",',
            '  "wer_estimate": 0.15,',
            '  "clarity_score": 0.85,',
            '  "pace_wpm": 130,',
            '  "filler_words": ["um", "like"],',
            '  "feedback": "Great job! Your speech was clear and well-paced.",',
            '  "strengths": ["clear pronunciation", "good pace"],',
            '  "suggestions": ["try to reduce filler words"]',
            "}",
            "",
            "Do NOT include:",
            "  - Explanatory text",
            "  - Any text outside the JSON object",
            "  - Markdown formatting or code blocks",
            "  - Any additional commentary",
            "",
            "The feedback should be warm, encouraging, and focused on building the teen's confidence.",
            "Return ONLY the raw JSON object, nothing else.",
        ],
        markdown=False,  # Disable markdown since we're returning raw JSON
    )
    return agent

def analyze_speech_with_audio(
    agent: Agent,
    audio_data: Optional[bytes] = None,
    audio_filepath: Optional[Union[str, Path]] = None,
    audio_format: str = "mp3",
    expected_response: Optional[str] = None
) -> str:
    """
    Analyze speech from audio file using the speech analysis agent.
    First transcribes the audio, then analyzes it.
    
    Args:
        agent: The speech analysis agent instance
        audio_data: Audio content as bytes (optional)
        audio_filepath: Path to audio file (optional)
        audio_format: Format of the audio file (e.g., "mp3", "wav", "m4a")
        expected_response: The expected response text for WER calculation
    
    Returns:
        Analysis result as JSON string
    """
    import sys
    # Add backend directory to path for imports
    backend_dir = Path(__file__).parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    from tools.speech_transcription_tool import transcribe_audio
    
    # First, transcribe the audio
    try:
        transcript = transcribe_audio(
            audio_data=audio_data,
            audio_filepath=audio_filepath,
            audio_format=audio_format
        )
        if not transcript or transcript.strip() == "":
            raise ValueError("Transcription returned empty result")
        print(f"Transcription successful: {transcript[:100]}...")
    except Exception as e:
        error_msg = f"Failed to transcribe audio: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        raise RuntimeError(error_msg) from e
    
    # Build the prompt with expected response if provided
    if expected_response:
        prompt = (
            f"EXPECTED RESPONSE: \"{expected_response}\"\n\n"
            f"TASK:\n"
            f"1. Transcribe exactly what the teen said\n"
            f"2. Calculate how well it matches the expected response\n"
            f"3. Provide a clarity score (0.0 to 1.0)\n"
            f"4. Give brief, encouraging feedback\n"
            f"5. Estimate speaking pace (words per minute)\n"
            f"6. Note any filler words (um, uh, like)\n\n"
            f"Here is the transcript: \"{transcript}\"\n\n"
            f"Respond ONLY in the exact JSON format specified in your instructions."
        )
    else:
        prompt = (
            f"TASK:\n"
            f"1. Transcribe exactly what the teen said\n"
            f"2. Provide a clarity score (0.0 to 1.0)\n"
            f"3. Give brief, encouraging feedback\n"
            f"4. Estimate speaking pace (words per minute)\n"
            f"5. Note any filler words (um, uh, like)\n\n"
            f"Here is the transcript: \"{transcript}\"\n\n"
            f"Note: Since no expected response was provided, set wer_estimate to null or 0.0.\n\n"
            f"Respond ONLY in the exact JSON format specified in your instructions."
        )
    
    # Run the analysis
    try:
        response = agent.run(prompt)
        if not response or not response.content:
            raise ValueError("Speech analysis agent returned empty response")
        return response.content.strip()
    except Exception as e:
        error_msg = f"Error running speech analysis: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        raise RuntimeError(error_msg) from e

# Create the speech analysis agent instance
speech_analysis_agent = create_speech_analysis_agent()

if __name__ == "__main__":
    # Simple test interaction
    print("Speech Analysis Agent - Ready!")
    print("This agent analyzes speech transcripts and provides feedback.\n")
    
    # Test with a sample transcript
    test_transcript = "I really like playing video games, especially action games."
    expected_response = "I really enjoy playing video games, especially action games."
    
    prompt = (
        f"EXPECTED RESPONSE: \"{expected_response}\"\n\n"
        f"TASK:\n"
        f"1. Transcribe exactly what the teen said\n"
        f"2. Calculate how well it matches the expected response\n"
        f"3. Provide a clarity score (0.0 to 1.0)\n"
        f"4. Give brief, encouraging feedback\n"
        f"5. Estimate speaking pace (words per minute)\n"
        f"6. Note any filler words (um, uh, like)\n\n"
        f"Here is the transcript: \"{test_transcript}\"\n\n"
        f"Respond ONLY in the exact JSON format specified in your instructions."
    )
    
    response = speech_analysis_agent.run(prompt)
    print(f"Transcript: {test_transcript}")
    print(f"Expected: {expected_response}")
    print(f"Analysis: {response.content}\n")
