# Orchestrator and Speech Analysis Agent Interaction

## Overview

The **Orchestrator** and **Speech Analysis Agent** have an **indirect feedback loop relationship** where the Speech Analysis Agent analyzes user speech, stores metrics in the database, and the Orchestrator uses these metrics to make intelligent decisions about future questions.

---

## Relationship Type

**Indirect Feedback Loop** (not direct agent-to-agent communication)

```
Speech Analysis Agent → Database → Orchestrator → Conversation Agent
```

The agents don't directly call each other. Instead:
1. Speech Analysis Agent processes audio and saves metrics to database
2. Orchestrator retrieves these metrics from database when generating next question
3. Orchestrator uses metrics to adapt dimension selection and difficulty

---

## Complete Interaction Flow

### Step 1: User Records Audio Response

```
User speaks → Frontend records audio → POST /api/process-audio
```

### Step 2: Speech Analysis Agent Processes Audio

**Location**: `backend/main.py` → `/api/process-audio` endpoint

**Process**:
1. **Audio Conversion**: Converts audio to WAV format (16kHz, mono) using ffmpeg
2. **Transcription**: Uses OpenAI Whisper API to transcribe audio
3. **Speech Analysis Agent Call**: 
   - Agent receives transcript and expected response (if available)
   - Agent analyzes:
     - Clarity score (0.0 to 1.0)
     - Word Error Rate (WER) estimate
     - Speaking pace (words per minute)
     - Filler words (um, uh, like, etc.)
     - Feedback, strengths, suggestions
4. **Returns JSON**:
```json
{
  "transcript": "I like playing Super Mario",
  "wer_estimate": 0.05,
  "clarity_score": 0.85,
  "pace_wpm": 120,
  "filler_words": ["um"],
  "feedback": "Great job! Your speech was clear.",
  "strengths": ["Clear pronunciation", "Good pace"],
  "suggestions": ["Try to reduce filler words"]
}
```

### Step 3: Save Metrics to Database

**Location**: `backend/main.py` → `update_conversation_turn_with_speech_analysis()`

**What's Saved**:
- `transcript`: What the user said
- `clarity_score`: 0.0 to 1.0 (e.g., 0.85)
- `pace_wpm`: Words per minute (e.g., 120)
- `wer_estimate`: Word Error Rate (e.g., 0.05)
- `filler_words_count`: Number of filler words
- Linked to `conversation_turn` via `turn_id`

**Database Table**: `conversation_turns`
- These metrics are stored as columns in the conversation turn record

### Step 4: Trigger Pre-Generation (Background)

**Location**: `backend/main.py` → `/api/process-audio` endpoint

After speech analysis completes:
- Retrieves `user_id`, `topic`, `previous_question`, `session_id` from database
- Triggers `pre_generate_next_question()` as background task
- This pre-generates the next question using orchestrator (which will use speech metrics)

### Step 5: Orchestrator Retrieves Speech Metrics

**Location**: `backend/main.py` → `/api/continue_conversation` or `pre_generate_next_question()`

**Process**:
1. **Fetch Speech Metrics**: 
   ```python
   speech_metrics = get_recent_speech_metrics_for_user_topic(user_id, topic, limit=5)
   ```
   - Retrieves last 5 conversation turns with speech analysis data
   - Only includes turns where `clarity_score` is not null

2. **Analyze Trends**:
   ```python
   speech_trends = analyze_speech_trends(speech_metrics)
   ```
   - Calculates:
     - `clarity_trend`: "improving", "declining", or "stable"
     - `pace_trend`: "improving", "declining", or "stable"
     - `average_clarity`: Average of recent clarity scores
     - `average_pace`: Average speaking pace
     - `recent_clarity`: Most recent clarity score
     - `confidence_level`: "high", "medium", or "low"
   - Requires at least 3 metrics to calculate trends

### Step 6: Build Speech Context for Orchestrator

**Location**: `backend/main.py` → Orchestrator prompt building

**Format** (ultra-compressed for token efficiency):

**If trends available**:
```
Speech: clarity_trend=improving, clarity_avg=0.85, clarity_recent=0.88, 
        pace_trend=stable, pace_avg=120wpm, conf=high, 
        recent_scores=[0.85, 0.88, 0.82]
```

**Ultra-compressed version** (for continue_conversation):
```
sp:tr=i,cl=0.88
```
- `tr=i`: trend=improving
- `cl=0.88`: recent clarity score

**If only limited data**:
```
Speech: clarity_recent=0.85 (limited data)
```

### Step 7: Orchestrator Uses Speech Context

**Location**: `backend/orchestrator_agent.py` → System instructions

**Orchestrator Instructions Include**:

1. **Analyze Speech Performance**:
   - Review clarity scores and trends
   - Consider speaking pace and pace trends
   - Assess overall confidence level

2. **Adapt Dimension Selection**:
   - **If clarity is improving**: Gradually increase challenge, explore new dimensions
   - **If clarity is declining**: Simplify, use familiar dimensions, reduce difficulty
   - **If clarity is stable and high (>0.85)**: User is excelling, can increase challenge
   - **If clarity is stable and low (<0.65)**: User may be struggling, provide more support

3. **Adjust Difficulty Level**:
   - **If confidence level is HIGH and clarity is improving**: Consider increasing difficulty
   - **If confidence level is LOW or clarity is declining**: Consider decreasing difficulty
   - **If confidence level is MEDIUM**: Maintain current difficulty or slight adjustment

4. **Adapt Question Complexity**:
   - Instruct Conversation Agent to adapt complexity based on speech performance trends
   - Match question complexity to user's demonstrated ability

### Step 8: Orchestrator Generates Question

**Location**: `backend/orchestrator_agent.py` → Orchestrator Team

**Process**:
1. Orchestrator receives speech context in prompt
2. Uses reasoning tools (think, analyze) to process speech metrics
3. Makes decision about:
   - Which dimension to use (adapts based on speech performance)
   - What difficulty level is appropriate
   - How complex the question should be
4. Delegates to Conversation Agent with adaptation instructions
5. Returns structured JSON with question, dimension, reasoning, difficulty_level

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Records Audio                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  /api/process-audio                                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Convert audio to WAV (ffmpeg)                         │  │
│  │ 2. Transcribe (OpenAI Whisper)                            │  │
│  │ 3. Call Speech Analysis Agent                             │  │
│  │    ┌──────────────────────────────────────────────────┐  │  │
│  │    │ Speech Analysis Agent                            │  │  │
│  │    │ - Analyzes transcript                            │  │  │
│  │    │ - Calculates clarity_score, pace, filler_words   │  │  │
│  │    │ - Generates feedback, strengths, suggestions     │  │  │
│  │    │ - Returns JSON with metrics                      │  │  │
│  │    └──────────────────────────────────────────────────┘  │  │
│  │ 4. Save metrics to database (conversation_turns)        │  │
│  │ 5. Trigger pre_generate_next_question() (background)    │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Database: conversation_turns                                    │
│  - transcript: "I like playing Super Mario"                      │
│  - clarity_score: 0.85                                          │
│  - pace_wpm: 120                                                │
│  - filler_words_count: 1                                        │
│  - wer_estimate: 0.05                                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ (Retrieved when generating next question)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  /api/continue_conversation or pre_generate_next_question()      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. get_recent_speech_metrics_for_user_topic()            │  │
│  │    → Returns last 5 turns with speech data               │  │
│  │ 2. analyze_speech_trends()                               │  │
│  │    → Calculates trends, averages, confidence level       │  │
│  │ 3. Build speech context (ultra-compressed)               │  │
│  │    → "sp:tr=i,cl=0.88"                                   │  │
│  │ 4. Include in orchestrator prompt                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Orchestrator Team                                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Receives:                                                 │  │
│  │ - Speech context: "sp:tr=i,cl=0.88"                      │  │
│  │ - Dimension history                                      │  │
│  │ - Conversation history                                   │  │
│  │ - User response                                          │  │
│  │                                                          │  │
│  │ Uses Reasoning Tools:                                    │  │
│  │ 1. THINK: Analyze speech performance                     │  │
│  │ 2. ANALYZE: Review trends and patterns                    │  │
│  │ 3. DECIDE: Adapt dimension and difficulty                │  │
│  │    - Clarity improving → Increase challenge               │  │
│  │    - Clarity declining → Simplify                        │  │
│  │    - High clarity (>0.85) → User excelling               │  │
│  │    - Low clarity (<0.65) → Provide support                │  │
│  │ 4. DELEGATE: Instruct Conversation Agent                  │  │
│  │    - Adapt complexity based on speech trends             │  │
│  │                                                          │  │
│  │ Returns:                                                 │  │
│  │ {                                                        │  │
│  │   "question": "...",                                     │  │
│  │   "dimension": "...",                                    │  │
│  │   "reasoning": "Adapted based on improving clarity...", │  │
│  │   "difficulty_level": 1 or 2 or 3                        │  │
│  │ }                                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Characteristics

### 1. **Indirect Communication**
- Speech Analysis Agent and Orchestrator **never directly call each other**
- Communication happens through **database storage and retrieval**
- This is a **decoupled architecture** - agents are independent

### 2. **Asynchronous Feedback Loop**
- Speech analysis happens **immediately** when user records audio
- Metrics are saved to database **synchronously**
- Orchestrator uses metrics **later** when generating next question
- Pre-generation happens **in background** after speech analysis

### 3. **Trend-Based Adaptation**
- Orchestrator doesn't just look at single metrics
- Analyzes **trends over multiple turns** (last 3-5 turns)
- Makes decisions based on **patterns** (improving/declining/stable)
- Considers **confidence level** (high/medium/low)

### 4. **Multi-Dimensional Adaptation**
- **Dimension Selection**: Chooses dimensions that match user's performance level
- **Difficulty Adjustment**: Increases/decreases difficulty based on clarity trends
- **Question Complexity**: Adapts complexity of questions based on speech performance
- **Support Level**: Provides more support if user is struggling

### 5. **Token Optimization**
- Speech context is **ultra-compressed** for token efficiency
- Format: `sp:tr=i,cl=0.88` instead of verbose descriptions
- Only essential metrics included in orchestrator prompt

---

## Example Scenarios

### Scenario 1: User Improving

**Speech Metrics**:
- Turn 1: clarity_score = 0.70
- Turn 2: clarity_score = 0.75
- Turn 3: clarity_score = 0.80

**Trend Analysis**:
- `clarity_trend`: "improving"
- `confidence_level`: "high"
- `average_clarity`: 0.75

**Orchestrator Decision**:
- **Dimension**: May explore deeper dimensions (Depth/Specificity, Reflective/Why)
- **Difficulty**: May increase difficulty level (1 → 2)
- **Reasoning**: "User's clarity is improving, indicating growing confidence. Can increase challenge."

### Scenario 2: User Struggling

**Speech Metrics**:
- Turn 1: clarity_score = 0.80
- Turn 2: clarity_score = 0.75
- Turn 3: clarity_score = 0.70

**Trend Analysis**:
- `clarity_trend`: "declining"
- `confidence_level`: "low"
- `average_clarity`: 0.75

**Orchestrator Decision**:
- **Dimension**: May use familiar dimensions (Basic Preferences, Social Context)
- **Difficulty**: May decrease difficulty level (2 → 1)
- **Reasoning**: "User's clarity is declining, may be struggling. Simplifying to provide support."

### Scenario 3: User Stable and High

**Speech Metrics**:
- Turn 1: clarity_score = 0.88
- Turn 2: clarity_score = 0.87
- Turn 3: clarity_score = 0.89

**Trend Analysis**:
- `clarity_trend`: "stable"
- `confidence_level`: "high"
- `average_clarity`: 0.88

**Orchestrator Decision**:
- **Dimension**: Can explore challenging dimensions (Challenge/Growth, Comparative)
- **Difficulty**: Can maintain or slightly increase difficulty
- **Reasoning**: "User is excelling with stable high clarity. Can increase challenge."

---

## Code Locations

### Speech Analysis Agent
- **Definition**: `backend/subagents/speech_analysis_agent.py`
- **Usage**: `backend/main.py` → `/api/process-audio` endpoint
- **Function**: `analyze_speech_with_audio()`

### Database Functions
- **Save Metrics**: `backend/database.py` → `update_conversation_turn_with_speech_analysis()`
- **Retrieve Metrics**: `backend/database.py` → `get_recent_speech_metrics_for_user_topic()`
- **Analyze Trends**: `backend/database.py` → `analyze_speech_trends()`

### Orchestrator Integration
- **Prompt Building**: `backend/main.py` → `/api/continue_conversation` and `pre_generate_next_question()`
- **Instructions**: `backend/orchestrator_agent.py` → System instructions (lines 104-127)
- **Context Format**: Ultra-compressed speech context in orchestrator prompts

---

## Benefits of This Architecture

1. **Decoupling**: Agents are independent - changes to one don't affect the other
2. **Scalability**: Can process speech analysis and question generation independently
3. **Persistence**: Speech metrics are stored permanently for historical analysis
4. **Flexibility**: Can analyze trends over any time period
5. **Performance**: Background pre-generation doesn't block user experience
6. **Adaptability**: System learns and adapts to user's performance over time

---

## Summary

The **Orchestrator** and **Speech Analysis Agent** have an **indirect feedback loop relationship**:

1. **Speech Analysis Agent** → Analyzes user speech → Saves metrics to database
2. **Orchestrator** → Retrieves metrics from database → Analyzes trends → Adapts decisions
3. **Feedback Loop** → Next question adapts based on speech performance → User responds → Cycle repeats

This creates a **self-improving system** that adapts to each user's unique speech performance patterns, providing personalized conversation practice that grows with the user's abilities.
