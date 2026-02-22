# ConvoBridge - Agent Tools Documentation

**Version**: 2.1.0  
**Date**: 2026-02-17

This document provides a comprehensive overview of all tools used by each agent in the ConvoBridge system.

---

## Overview

Each agent in ConvoBridge has access to specific tools that enable them to perform their designated tasks. Tools are either:
- **Built-in Agno tools** (e.g., ReasoningTools)
- **Custom Python functions** registered as tools
- **External API integrations** (e.g., OpenAI Whisper, TTS)
- **OpenAI API** (via Agno's model interface) - All agents use OpenAI API to call LLMs, but some agents also use additional tools

**Note**: All agents use OpenAI API (through Agno's `OpenAIChat` model) to interact with GPT-4o-mini. The "Tools Used" section for each agent refers to additional tools beyond the base LLM API calls.

---

## 1. Orchestrator Team

**Location**: `backend/orchestrator_agent.py`

### Tools Used

#### 1.1 ReasoningTools (Built-in Agno Tool)
- **Type**: Built-in Agno reasoning tool
- **Enabled Features**:
  - `think`: Enables structured thinking process
  - `analyze`: Enables analytical reasoning
  - `add_instructions`: Adds reasoning instructions to the agent
  - `add_few_shot`: Adds few-shot examples for reasoning

**Usage**:
```python
tools=[
    ReasoningTools(
        enable_think=True,
        enable_analyze=True,
        add_instructions=True,
        add_few_shot=True,
    )
]
```

**Purpose**:
- Analyze user-chosen topics and determine conversation approach
- Decide which conversation dimension is most appropriate
- Consider user's conversation history and engagement level
- Break down complex coordination tasks into steps
- Decide which sub-agent to delegate to and when
- Reflect on the quality of responses from sub-agents
- Adjust approach based on conversation context
- Consider multiple perspectives before making decisions

**When Used**:
- **First Questions**: Analyze topic characteristics, decide on "Basic Preferences" dimension
- **Follow-Up Questions**: Analyze user response, review dimension history, check speech performance metrics, decide on next dimension and difficulty

### Sub-Agent Access

The Orchestrator has access to delegate to:
- **Conversation Agent**: For question generation
- **Response Agent**: Available for response option generation (called separately via API)
- **Vocabulary Agent**: Available for vocabulary generation (called separately via API)
- **Speech Analysis Agent**: Available for speech analysis (called separately via API)

**Note**: While the Orchestrator has these agents as team members, they are typically called directly via API endpoints rather than through delegation in the current implementation.

---

## 2. Conversation Agent

**Location**: `backend/subagents/conversation_agent.py`  
**Tools File**: `backend/tools/conversation_tools.py`

### Tools Used

#### 2.1 `get_context`
- **Type**: Custom Python function tool
- **Function Signature**:
  ```python
  def get_context(
      user_response: str,
      current_dimension: str,
      topic: str,
      previous_question: Optional[str] = None
  ) -> Dict[str, Any]
  ```

**Purpose**:
- Gathers conversation context for follow-up question generation
- Provides structured context including:
  - User's response
  - Current dimension
  - Topic
  - Previous question (if available)
  - Formatted context summary

**Returns**:
```python
{
    "user_response": "I like playing Super Mario",
    "current_dimension": "social context",
    "topic": "gaming",
    "previous_question": "What type of video games do you enjoy playing?",
    "context_summary": "Topic: gaming\nUser Response: I like playing Super Mario\n..."
}
```

**When Used**:
- For follow-up questions (when user response is provided)
- Called before `generate_followup_question` to gather context

#### 2.2 `generate_followup_question`
- **Type**: Custom Python function tool
- **Function Signature**:
  ```python
  def generate_followup_question(
      user_response: str,
      current_dimension: str,
      topic: str,
      previous_question: Optional[str] = None
  ) -> str
  ```

**Purpose**:
- Generates a formatted prompt for creating contextual follow-up questions
- Provides structured instructions for:
  - Emotional tone matching (positive/negative/neutral)
  - Acknowledgement + Personal Preference + Question format
  - Dimension adaptation
  - Avoiding question repetition
  - Natural conversation flow

**Returns**:
- A formatted prompt string with detailed instructions for the agent to generate the follow-up question

**When Used**:
- For follow-up questions (after `get_context` is called)
- Provides the agent with structured guidance for generating contextually relevant follow-ups

**Key Features**:
- **Emotional Tone Matching**: Analyzes user's emotional tone and matches acknowledgements accordingly
- **Variety Enforcement**: Ensures different acknowledgement phrases are used
- **Question Uniqueness**: Prevents repeating the same question
- **Dimension Adaptation**: Adapts question to the selected conversation dimension

### Tool Usage Flow

**For Initial Questions**:
- No tools used - agent generates question directly based on topic and dimension

**For Follow-Up Questions**:
1. Call `get_context()` to gather conversation context
2. Call `generate_followup_question()` to get structured prompt
3. Agent uses the prompt to generate the follow-up question

---

## 3. Response Agent

**Location**: `backend/subagents/response_generate_agent.py`

### Tools Used

**No Custom Tools** - The Response Agent does not use any custom tools.

**LLM Integration**:
- **Model**: OpenAI GPT-4o-mini (via Agno's `OpenAIChat`)
- **API**: Uses OpenAI API to call the LLM
- The agent uses Agno's model interface which handles OpenAI API calls internally

**How It Works**:
- Agent receives a prompt with:
  - Question text
  - Topic
  - Dimension
  - User's previous response (if available)
- Agent calls OpenAI API (via Agno) to generate JSON array using its instructions
- Returns: `["option1", "option2"]`

**Output Format**:
```json
[
  "I really enjoy playing action games like Call of Duty.",
  "I prefer puzzle games because they challenge my mind."
]
```

**Note**: The agent relies on OpenAI API (via Agno's `OpenAIChat` model) to generate topic-specific response options. While it doesn't use custom tools, it does make direct LLM API calls through Agno's model interface.

---

## 4. Vocabulary Agent

**Location**: `backend/subagents/vocabulary_agent.py`

### Tools Used

**No Custom Tools** - The Vocabulary Agent does not use any custom tools.

**LLM Integration**:
- **Model**: OpenAI GPT-4o-mini (via Agno's `OpenAIChat`)
- **API**: Uses OpenAI API to call the LLM
- The agent uses Agno's model interface which handles OpenAI API calls internally

**How It Works**:
- Agent receives a prompt with:
  - Question text
  - Topic (optional)
- Agent calls OpenAI API (via Agno) to generate JSON object using its instructions
- Returns vocabulary word with definition, type, and example

**Output Format**:
```json
{
  "word": "genre",
  "type": "noun",
  "definition": "A category of artistic composition characterized by similarities in form, style, or subject matter.",
  "example": "My favorite genre of video games is action-adventure."
}
```

**Note**: The agent relies on OpenAI API (via Agno's `OpenAIChat` model) to identify contextually relevant vocabulary words. While it doesn't use custom tools, it does make direct LLM API calls through Agno's model interface.

---

## 5. Speech Analysis Agent

**Location**: `backend/subagents/speech_analysis_agent.py`  
**Tools File**: `backend/tools/speech_transcription_tool.py`

### Tools Used

#### 5.1 `transcribe_audio` (Indirect Usage)
- **Type**: Custom Python function (not directly registered as tool)
- **Location**: `backend/tools/speech_transcription_tool.py`
- **Function Signature**:
  ```python
  def transcribe_audio(
      audio_data: Optional[bytes] = None,
      audio_filepath: Optional[Union[str, Path]] = None,
      audio_format: str = "mp3"
  ) -> str
  ```

**Purpose**:
- Transcribes audio to text using OpenAI Whisper API (via Agno's audio capabilities)
- Supports multiple audio formats (mp3, wav, m4a, webm)
- Can accept audio as bytes or file path

**How It Works**:
1. Creates a transcription agent with `gpt-4o-audio-preview` model
2. Uses Agno's `Audio` class to handle audio input
3. Sends audio to OpenAI Whisper API for transcription
4. Returns transcribed text

**When Used**:
- Called by `analyze_speech_with_audio()` function before speech analysis
- Used in the speech analysis workflow:
  1. Audio → `transcribe_audio()` → Transcript
  2. Transcript + Expected Response → Speech Analysis Agent → Analysis JSON

**Usage Pattern**:
```python
# In speech_analysis_agent.py
from tools.speech_transcription_tool import transcribe_audio

# First transcribe
transcript = transcribe_audio(
    audio_data=audio_data,
    audio_filepath=audio_filepath,
    audio_format=audio_format
)

# Then analyze
response = agent.run(prompt_with_transcript)
```

### Speech Analysis Workflow

**Complete Flow**:
1. **Audio Input**: User records audio response
2. **Transcription**: `transcribe_audio()` converts audio to text
3. **Analysis**: Speech Analysis Agent analyzes transcript
4. **Output**: Returns JSON with:
   - `transcript`: Transcribed text
   - `wer_estimate`: Word Error Rate (0.0-1.0)
   - `clarity_score`: Clarity score (0.0-1.0)
   - `pace_wpm`: Speaking pace (words per minute)
   - `filler_words`: List of filler words found
   - `feedback`: Encouraging feedback
   - `strengths`: List of strengths
   - `suggestions`: List of suggestions

**Note**: The Speech Analysis Agent itself doesn't have `transcribe_audio` registered as a tool. Instead, it's called programmatically in the `analyze_speech_with_audio()` helper function before the agent processes the transcript.

---

## Tool Summary Table

| Agent | Tools Used | Tool Type | Purpose |
|-------|-----------|-----------|---------|
| **Orchestrator** | `ReasoningTools` (think, analyze) | Built-in Agno | Complex decision-making, topic analysis, dimension selection |
| **Conversation Agent** | `get_context` | Custom Python | Gather conversation context |
| **Conversation Agent** | `generate_followup_question` | Custom Python | Generate structured follow-up question prompts |
| **Response Agent** | None (uses OpenAI API via Agno) | OpenAI API | Direct JSON generation via LLM (GPT-4o-mini) |
| **Vocabulary Agent** | None (uses OpenAI API via Agno) | OpenAI API | Direct JSON generation via LLM (GPT-4o-mini) |
| **Speech Analysis Agent** | `transcribe_audio` (indirect) | Custom Python | Audio transcription via Whisper API |

---

## Tool Implementation Details

### Custom Tool Registration

Custom tools are registered in the agent definition:

```python
# Example: Conversation Agent
agent = Agent(
    name="Conversation Agent",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[get_context, generate_followup_question],  # Tools registered here
    ...
)
```

### Tool Function Requirements

For a Python function to be used as an Agno tool:
1. Must be a callable function
2. Should have type hints for parameters
3. Should have a docstring describing its purpose
4. Should return a value that the agent can use

### External API Tools

Some tools interact with external APIs:
- **`transcribe_audio`**: Uses OpenAI Whisper API (via Agno's audio capabilities)
- **TTS**: Uses OpenAI TTS API (called separately, not as agent tool)

---

## Tool Usage Patterns

### Pattern 1: Sequential Tool Usage (Conversation Agent)
```
get_context() → generate_followup_question() → Agent generates question
```

### Pattern 2: Indirect Tool Usage (Speech Analysis Agent)
```
transcribe_audio() → Agent analyzes transcript → Returns analysis JSON
```

### Pattern 3: Direct LLM API Calls (Response/Vocabulary Agents)
```
Agent receives prompt → OpenAI API (via Agno) → Agent generates JSON directly
```

### Pattern 4: Built-in Tools (Orchestrator)
```
think() → analyze() → decide → delegate to sub-agent
```

---

## Future Tool Enhancements

### Potential New Tools

1. **Database Query Tools**: Direct database access for agents
2. **Cache Management Tools**: Tools for managing pre-generation cache
3. **Speech Metrics Analysis Tools**: Tools for analyzing speech trends
4. **Context Summarization Tools**: Tools for compressing conversation history

### Tool Improvements

1. **Error Handling**: Enhanced error handling in custom tools
2. **Tool Validation**: Input validation for tool parameters
3. **Tool Logging**: Better logging for tool usage and performance
4. **Tool Testing**: Unit tests for all custom tools

---

## Related Documentation

- **[ARCHITECTURE.md](./ARCHITECTURE.md)**: System architecture and design
- **[AGENT_FLOW.md](./AGENT_FLOW.md)**: Detailed agent interaction flows
- **[DATAFLOW.md](./DATAFLOW.md)**: Complete dataflow documentation
- **[DEMO_AGENT_ARCHITECTURE.md](./DEMO_AGENT_ARCHITECTURE.md)**: Demo-ready agent architecture

---

**Last Updated**: 2026-02-17  
**Version**: 2.1.0
