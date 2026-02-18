# ConvoBridge - Agent Architecture for Demo

**Version**: 2.1.0  
**Date**: 2026-02-17  
**Purpose**: Demo presentation document

---

## Executive Summary

ConvoBridge uses a **multi-agent orchestration system** where an intelligent **Orchestrator Team** coordinates specialized sub-agents to deliver personalized, adaptive conversation practice sessions for autistic youth. Each agent has a specific role, and together they create a seamless, contextually-aware conversation experience.

---

## Agent Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│              Orchestrator Team (Coordinator)                │
│  - Intelligent decision-making                              │
│  - Coordinates all sub-agents                                │
│  - Adapts to user performance                                │
│  - Returns: {question, dimension, reasoning, difficulty}     │
└──────────────────┬──────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┬──────────────┐
        │           │           │              │
        ▼           ▼           ▼              ▼
┌─────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ Conversation│ │ Response │ │Vocabulary│ │Speech Analysis│
│   Agent     │ │  Agent   │ │  Agent   │ │    Agent      │
│             │ │          │ │          │ │               │
│ Generates   │ │ Generates│ │ Identifies│ │ Analyzes     │
│ questions   │ │ response │ │ relevant │ │ speech       │
│             │ │ options  │ │ vocab    │ │ performance  │
└─────────────┘ └──────────┘ └──────────┘ └──────────────┘
```

---

## 1. Orchestrator Team

**Role**: Intelligent Coordinator & Decision Maker  
**Model**: GPT-4o-mini with Reasoning Tools  
**Location**: `backend/orchestrator_agent.py`

### Key Responsibilities

#### 1.1 Topic-Based Reasoning
- Analyzes user-chosen topics (Gaming, Food, Hobbies, etc.)
- Determines the best conversation approach for each topic
- Selects appropriate conversation dimensions based on topic characteristics

#### 1.2 Intelligent Dimension Selection
 
- **Basic Preferences**: Likes, dislikes, favorites (always used for first question)
- **Depth/Specificity**: Deeper, more detailed questions
- **Social Context**: Social aspects of the topic
- **Emotional**: Feelings about the topic
- **Temporal/Frequency**: When, how often, past experiences
- **Comparative**: Comparing different aspects
- **Reflective/Why**: Reasons and motivations
- **Descriptive/Detail**: Detailed descriptions
- **Challenge/Growth**: Challenges and personal growth

**Selection Criteria**:
- Topic characteristics
- User's conversation history
- User engagement level (response length, detail)
- **Speech performance metrics** (clarity trends, pace, confidence)
- Dimension history (avoids repetition, enforces variety)

#### 1.3 Speech Performance Integration
- **Retrieves** speech metrics from database (clarity scores, pace, trends)
- **Analyzes** trends: improving, declining, or stable
- **Adapts** dimension selection and difficulty based on performance:
  - **Improving clarity** → Increase challenge, explore new dimensions
  - **Declining clarity** → Simplify, use familiar dimensions
  - **High clarity (>0.85)** → User excelling, can increase challenge
  - **Low clarity (<0.65)** → User struggling, provide more support

#### 1.4 Dimension Switching Enforcement
- **Critical Rule**: Never uses the same dimension for more than 2 consecutive turns
- Automatically detects if same dimension used 2+ times
- Forces switch to different dimension to maintain variety

#### 1.5 Difficulty Level Adjustment
- Adjusts difficulty (1-3) based on:
  - Speech performance trends
  - Confidence level (high/medium/low)
  - User engagement patterns

#### 1.6 Sub-Agent Delegation
- Delegates to **Conversation Agent** for question generation
- Provides context-aware instructions:
  - Topic-specific guidance
  - Dimension requirements
  - Difficulty level
  - Speech performance adaptation needs

#### 1.7 Output Format
Returns structured JSON:
```json
{
  "question": "What kind of video games do you enjoy playing?",
  "dimension": "Basic Preferences",
  "reasoning": "Starting with basic preferences to understand user's interests",
  "difficulty_level": 1
}
```

### Decision-Making Process

**For First Questions**:
1. **THINK**: Analyze topic characteristics
2. **ANALYZE**: Consider topic-specific conversation approach
3. **DECIDE**: Always choose "Basic Preferences" dimension
4. **DELEGATE**: Instruct Conversation Agent to generate welcoming first question

**For Follow-Up Questions**:
1. **THINK**: Analyze user response and engagement
2. **ANALYZE**: Review:
   - Previous questions and dimensions used
   - User's response content and emotional tone
   - **Speech performance metrics and trends**
   - Dimension history (enforce switching if needed)
3. **DECIDE**: 
   - Select next dimension (adapt based on speech performance)
   - Adjust difficulty level
4. **DELEGATE**: Instruct Conversation Agent with adaptation guidance

### Tools Available
- **Reasoning Tools**: `think` and `analyze` for complex decision-making
- **Sub-Agent Access**: Can delegate to Conversation, Response, Vocabulary, Speech Analysis agents

---

## 2. Conversation Agent

**Role**: Question Generator  
**Model**: GPT-4o-mini  
**Location**: `backend/subagents/conversation_agent.py`

### Key Responsibilities

#### 2.1 Question Generation
- Generates natural, engaging conversation questions
- Adapts to 9 conversation dimensions
- Ensures questions are teen-appropriate and supportive

#### 2.2 Contextual Awareness
- Uses conversation tools to gather context:
  - Previous questions
  - User responses
  - Conversation history
  - Topic and dimension

#### 2.3 Follow-Up Question Pattern
Generates follow-ups using **"Acknowledgement + Personal Preference + Question"** format:
- **Acknowledgement**: Recognizes user's response ("That's great!", "I understand")
- **Personal Preference**: Adds relatable personal touch ("I like that too", "That sounds fun")
- **Question**: Natural follow-up question

**Example**:
> "That's great! I like racing games too. Do you play alone or with friends?"

#### 2.4 Contextual Relevance
- References specific things mentioned by user
- Builds on previous conversation
- Never repeats the same question
- Varies acknowledgements to maintain natural flow

#### 2.5 Adaptation
- Adapts question complexity based on:
  - Orchestrator's difficulty level
  - Speech performance trends (from orchestrator)
  - User engagement level

### Tools Available
- **Conversation Tools**: 
  - `get_context`: Gathers conversation context
  - `generate_followup_question`: Generates contextually relevant follow-ups

---

## 3. Response Agent

**Role**: Response Option Generator  
**Model**: GPT-4o-mini  
**Location**: `backend/subagents/response_generate_agent.py`

### Key Responsibilities

#### 3.1 Response Option Generation
- Generates **2 topic-specific response options** for each question
- Adds "Choose your own response" as 3rd option
- Ensures options are simple and direct (Level 1 difficulty)

#### 3.2 Topic-Aware Generation
- **Critical**: Options MUST be specifically relevant to the topic
- Gaming → game-related options
- Food → food-related options
- Hobbies → hobby-related options
- **No generic options** that could apply to any topic

#### 3.3 User Context Integration
- Considers user's previous response when available
- Generates personalized options that reference what user mentioned
- Maintains conversation continuity

#### 3.4 Dimension Adaptation
- Adapts options to match the conversation dimension
- Basic Preferences → Preference-based options
- Social Context → Social interaction options
- Emotional → Feeling-based options

### Output Format
Returns JSON array:
```json
[
  "I really enjoy playing action games like Call of Duty.",
  "I prefer puzzle games because they challenge my mind.",
  "Choose your own response"
]
```

---

## 4. Vocabulary Agent

**Role**: Vocabulary Word Identifier  
**Model**: GPT-4o-mini  
**Location**: `backend/subagents/vocabulary_agent.py`

### Key Responsibilities

#### 4.1 Contextual Vocabulary Selection
- Identifies **contextually relevant** vocabulary words from questions
- Ensures vocabulary matches the specific question and topic
- Selects words that enhance conversation understanding

#### 4.2 Vocabulary Details
- Provides word definition
- Includes word type (noun, verb, adjective, etc.)
- Creates example sentence using the word

#### 4.3 Educational Value
- Helps users learn new words relevant to their conversations
- Reinforces vocabulary through context
- Supports language development

### Output Format
Returns JSON:
```json
{
  "word": "genre",
  "type": "noun",
  "definition": "A category of artistic composition characterized by similarities in form, style, or subject matter.",
  "example": "My favorite genre of video games is action-adventure."
}
```

---

## 5. Speech Analysis Agent

**Role**: Speech Performance Analyzer  
**Model**: GPT-4o-mini  
**Location**: `backend/subagents/speech_analysis_agent.py`

### Key Responsibilities

#### 5.1 Speech Transcription
- Transcribes user audio using OpenAI Whisper API
- Converts speech to text accurately
- Handles various audio formats (webm, mp3, wav, m4a)

#### 5.2 Speech Analysis
Analyzes transcribed speech for:
- **Clarity Score** (0.0 to 1.0): How clear and understandable the speech is
- **Word Error Rate (WER)**: How well speech matches expected response
- **Speaking Pace**: Words per minute
- **Filler Words**: Identifies "um", "uh", "like", etc.

#### 5.3 Feedback Generation
- Provides **encouraging feedback** to build confidence
- Identifies **strengths** in user's speech
- Offers **constructive suggestions** for improvement
- Focuses on positive reinforcement

#### 5.4 Performance Metrics
Calculates and stores:
- Clarity score for trend analysis
- Speaking pace for fluency assessment
- Filler word count for speech quality
- Overall communication effectiveness

### Output Format
Returns JSON:
```json
{
  "transcript": "I like playing Super Mario",
  "clarity_score": 0.85,
  "pace_wpm": 120,
  "filler_words": ["um"],
  "feedback": "Great job! Your speech was clear and well-paced.",
  "strengths": ["Clear pronunciation", "Good pace"],
  "suggestions": ["Try to reduce filler words"]
}
```

### Integration with Orchestrator
- **Saves metrics to database** after analysis
- **Orchestrator retrieves metrics** when generating next question
- **Creates feedback loop**: Speech performance influences future questions

---

## Agent Interaction Flow

### Flow 1: First Question Generation

```
User Selects Topic
    ↓
Orchestrator Team
    ├─ THINK: Analyze topic
    ├─ DECIDE: Choose "Basic Preferences" dimension
    └─ DELEGATE → Conversation Agent
         └─ Generates first question
    ↓
Returns: {question, dimension, reasoning, difficulty_level}
    ↓
Frontend displays question + audio
```

### Flow 2: Follow-Up Question Generation

```
User Responds
    ↓
Orchestrator Team
    ├─ THINK: Analyze user response
    ├─ ANALYZE: 
    │   ├─ Review dimension history
    │   ├─ Check speech performance metrics
    │   └─ Assess engagement level
    ├─ DECIDE: 
    │   ├─ Select next dimension (adapt based on speech)
    │   └─ Adjust difficulty level
    └─ DELEGATE → Conversation Agent
         └─ Generates follow-up question
    ↓
Returns: {question, dimension, reasoning, difficulty_level}
    ↓
Frontend displays question + audio
```

### Flow 3: Speech Analysis & Feedback Loop

```
User Records Audio
    ↓
Speech Analysis Agent
    ├─ Transcribes audio (Whisper)
    ├─ Analyzes clarity, pace, filler words
    └─ Generates feedback
    ↓
Saves metrics to database
    ↓
(Next question generation)
    ↓
Orchestrator retrieves metrics
    ├─ Analyzes trends
    └─ Adapts next question based on performance
```

### Flow 4: Response Options & Vocabulary

```
Question Displayed
    ↓
Parallel Generation:
    ├─ Response Agent → Generates 2 topic-specific options
    └─ Vocabulary Agent → Identifies relevant vocabulary word
    ↓
Frontend displays options + vocabulary
```

---

## Key Features

### 1. Intelligent Orchestration
- Orchestrator makes context-aware decisions
- Coordinates all agents seamlessly
- Adapts to user performance in real-time

### 2. Speech Performance Feedback Loop
- Speech Analysis Agent analyzes user speech
- Metrics stored in database
- Orchestrator uses metrics to adapt future questions
- Creates personalized learning experience

### 3. Dimension Variety
- 9 conversation dimensions ensure variety
- Automatic dimension switching prevents repetition
- Adapts dimensions based on speech performance

### 4. Contextual Awareness
- All agents maintain conversation context
- Questions reference previous responses
- Natural conversation flow

### 5. Topic-Specific Generation
- Response options are topic-specific
- Vocabulary words match question context
- No generic content

### 6. Adaptive Difficulty
- Adjusts based on speech performance
- Increases challenge when user excels
- Provides support when user struggles

---

## Technical Architecture

### Agent Communication
- **Orchestrator → Conversation Agent**: Direct delegation via Agno Team
- **Orchestrator → Response/Vocabulary Agents**: Available but called separately via API
- **Speech Analysis Agent → Orchestrator**: Indirect via database (feedback loop)

### Data Flow
- **Question Generation**: Orchestrator → Conversation Agent → Question
- **Speech Analysis**: Audio → Speech Analysis Agent → Database → Orchestrator (next question)
- **Response Options**: Response Agent (parallel with Vocabulary Agent)
- **Vocabulary**: Vocabulary Agent (parallel with Response Agent)

### Performance Optimizations
- **Pre-generation**: Questions pre-generated in background
- **Parallel Execution**: Response options and vocabulary generated simultaneously
- **Caching**: Speech metrics and conversation history cached
- **Token Optimization**: Ultra-compressed prompts for efficiency

---

## Demo Highlights

### What Makes This Special

1. **Intelligent Adaptation**: System learns from user's speech performance and adapts in real-time

2. **Multi-Agent Coordination**: Orchestrator seamlessly coordinates 4 specialized agents

3. **Speech Feedback Loop**: Speech analysis directly influences future questions

4. **Contextual Awareness**: Every question builds on previous conversation

5. **Personalized Experience**: Adapts difficulty, dimensions, and complexity to each user

6. **Topic-Specific**: All content is relevant to chosen topic (no generic responses)

7. **Variety Enforcement**: Automatic dimension switching ensures engaging conversations

---

## Summary

ConvoBridge's agent architecture creates a **self-improving, adaptive conversation system**:

- **Orchestrator** makes intelligent decisions based on multiple data sources
- **Conversation Agent** generates contextually relevant questions
- **Response Agent** provides topic-specific response options
- **Vocabulary Agent** identifies relevant learning words
- **Speech Analysis Agent** analyzes performance and creates feedback loop

Together, these agents deliver a **personalized, supportive conversation practice experience** that adapts to each user's unique needs and abilities.

---

**For Technical Details**: See [DATAFLOW.md](./DATAFLOW.md) and [AGENT_FLOW.md](./AGENT_FLOW.md)  
**For Architecture**: See [ARCHITECTURE.md](./ARCHITECTURE.md)  
**For Orchestrator-Speech Interaction**: See [ORCHESTRATOR_SPEECH_INTERACTION.md](./ORCHESTRATOR_SPEECH_INTERACTION.md)
