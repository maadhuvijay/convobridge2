# ConvoBridge - Technical Architecture Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Agent System Design](#agent-system-design)
6. [API Documentation](#api-documentation)
7. [Frontend Architecture](#frontend-architecture)
8. [Setup & Installation](#setup--installation)
9. [Development Workflow](#development-workflow)
10. [Future Enhancements](#future-enhancements)

---

## Project Overview

**ConvoBridge** is a conversation practice platform designed to help autistic youth build confidence in social interactions through structured, AI-powered conversation sessions. The system uses a multi-agent architecture with **contextual awareness** to generate **contextually relevant** questions and responses that adapt to user input and engagement levels.

### Key Features
- **Topic-Based Conversations**: Users select from predefined topics (Gaming, Food, Hobbies, Weekend Plans, YouTube, etc.)
- **Contextually Aware Question Generation**: Dynamic questions that adapt to user responses with **contextual relevance**
- **Follow-Up Questions**: Context-aware follow-ups using "Acknowledgement + Personal Preference + Question" pattern
- **Text-to-Speech**: Automatic audio generation for questions with on-demand replay
- **Speech Analysis**: Real-time speech transcription, clarity scoring, and feedback
- **Structured Responses**: Pre-generated response options to guide users
- **Vocabulary Learning**: Contextually relevant vocabulary words for each question
- **User & Session Management**: Persistent user tracking and session management via Supabase
- **Progressive Loading**: Optimized UX with immediate question display and background content loading
- **Multiple Conversation Dimensions**: 9 dimensions for varied, contextually relevant follow-up questions
- **Difficulty Levels**: Adjustable conversation difficulty (Level 1+)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Chat UI    │  │  Topic       │  │ Vocabulary  │       │
│  │  Component   │  │  Selection   │  │  Display    │       │
│  │  + Audio     │  │              │  │  + Speech   │       │
│  │  Playback    │  │              │  │  Analysis   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└────────────────────────────┬────────────────────────────────┘
                              │ HTTP/REST API
                              │ (CORS Enabled)
┌─────────────────────────────▼────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         API Endpoints                                 │  │
│  │  - /api/login                                        │  │
│  │  - /api/start_conversation                           │  │
│  │  - /api/continue_conversation                        │  │
│  │  - /api/get_conversation_details                     │  │
│  │  - /api/text_to_speech                               │  │
│  │  - /api/process-audio                                │  │
│  └────────────────────┬───────────────────────────────────┘  │
│                       │                                       │
│  ┌────────────────────▼───────────────────────────────────┐  │
│  │         Supabase Database                             │  │
│  │  - User Management                                    │  │
│  │  - Session Tracking                                   │  │
│  │  - Conversation History                               │  │
│  └────────────────────┬───────────────────────────────────┘  │
│                       │                                       │
│  ┌────────────────────▼───────────────────────────────────┐  │
│  │         Orchestrator Team (Agno Team)                 │  │
│  │  - Coordinates sub-agents                              │  │
│  │  - Delegates tasks with contextual awareness          │  │
│  │  - Synthesizes responses                              │  │
│  └────────────────────┬───────────────────────────────────┘  │
│                       │                                       │
│  ┌────────────────────▼───────────────────────────────────┐  │
│  │         Sub-Agents (Agno Agents)                      │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  Conversation Agent                              │  │  │
│  │  │  - Context-aware question generation             │  │  │
│  │  │  - Uses conversation tools for contextual relevance│ │  │
│  │  │  - Follow-up questions with personal preferences │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  Response Agent                                    │  │  │
│  │  │  - Generates contextually relevant response options│  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  Vocabulary Agent                                 │  │  │
│  │  │  - Identifies contextually relevant vocabulary    │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  Speech Analysis Agent                           │  │  │
│  │  │  - Transcribes and analyzes speech                │  │  │
│  │  │  - Provides clarity scores and feedback          │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                       │                                       │
│  ┌────────────────────▼───────────────────────────────────┐  │
│  │         Tools & Services                              │  │
│  │  - Conversation Tools (contextual awareness)          │  │
│  │  - Text-to-Speech (OpenAI TTS)                        │  │
│  │  - Speech Transcription                               │  │
│  └─────────────────────────────────────────────────────────┘  │
│                       │                                       │
│  ┌────────────────────▼───────────────────────────────────┐  │
│  │         OpenAI API (via Agno)                          │  │
│  │  - GPT-4o-mini (conversation, responses, vocabulary)   │  │
│  │  - TTS API (text-to-speech)                           │  │
│  │  - Whisper (speech transcription)                     │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Principles

1. **Multi-Agent System**: Uses Agno's Team architecture for coordinated agent collaboration
2. **Contextual Awareness**: System maintains conversation context for **contextually relevant** follow-up questions
3. **Contextual Relevance**: Questions and responses adapt to user input, ensuring high **contextual relevance**
4. **Separation of Concerns**: Frontend handles UI, backend handles AI logic
5. **Modular Design**: Sub-agents are independently developed and can be added incrementally
6. **RESTful API**: Clean API interface between frontend and backend
7. **Progressive Loading**: Optimized UX with immediate question display and background content loading
8. **Scalable**: Team-based architecture allows easy addition of new agents
9. **Persistent State**: User and session management via Supabase for continuity

---

## Technology Stack

### Frontend
- **Framework**: Next.js 16.1.6 (App Router)
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 4
- **UI Components**: React 19.2.3
- **Icons**: Lucide React
- **Build Tool**: Turbopack

### Backend
- **Framework**: FastAPI (Python)
- **AI Framework**: Agno 2.5.2
- **LLM Provider**: OpenAI GPT-4o-mini (optimized for performance)
- **TTS Provider**: OpenAI TTS API (tts-1-hd model)
- **Speech Recognition**: OpenAI Whisper API
- **Database**: Supabase (PostgreSQL)
- **Server**: Uvicorn (ASGI)
- **Environment**: python-dotenv
- **CORS**: FastAPI CORS Middleware
- **Audio Processing**: ffmpeg (for format conversion)

### Development Tools
- **Package Manager**: npm
- **Linting**: ESLint
- **Type Checking**: TypeScript

---

## Project Structure

```
convobridge2/
├── app/                          # Next.js App Router
│   ├── chat/                     # Chat interface pages
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx  # Main chat UI component
│   │   │   └── ChatNavbar.tsx    # Navigation bar
│   │   └── page.tsx              # Chat page route
│   ├── components/              # Shared components
│   │   ├── Hero.tsx
│   │   ├── LoginNavbar.tsx
│   │   ├── Navbar.tsx
│   │   └── PuzzleIcon.tsx
│   ├── login/                     # Login page
│   │   └── page.tsx
│   ├── globals.css               # Global styles
│   ├── layout.tsx                # Root layout
│   └── page.tsx                  # Home page
│
├── backend/                      # Python backend
│   ├── main.py                   # FastAPI application & API endpoints
│   ├── orchestrator_agent.py     # Orchestrator team
│   ├── database.py               # Supabase database integration
│   ├── database_schema.sql        # Database schema definitions
│   ├── requirements.txt          # Python dependencies
│   ├── subagents/                # Sub-agent modules
│   │   ├── conversation_agent.py # Context-aware question generator
│   │   ├── response_generate_agent.py # Response options generator
│   │   ├── vocabulary_agent.py  # Vocabulary word generator
│   │   └── speech_analysis_agent.py # Speech transcription & analysis
│   └── tools/                    # Agent tools and utilities
│       ├── conversation_tools.py # Contextual conversation tools
│       ├── text_to_speech.py     # Text-to-speech functionality
│       ├── speech_transcription_tool.py # Speech transcription
│       ├── generate_response_options.py # Response generation helper
│       └── set_sentence_difficulty.py # Difficulty adjustment
│
├── public/                       # Static assets
├── .gitignore                    # Git ignore rules
├── ARCHITECTURE.md               # This file
├── package.json                  # Node.js dependencies
├── tsconfig.json                 # TypeScript config
└── README.md                     # Project README
```

---

## Agent System Design

### Orchestrator Team

The **Orchestrator Team** is the central coordination point for all agent interactions. It uses Agno's Team architecture to manage and delegate tasks to specialized sub-agents with **contextual awareness** of user engagement and conversation flow.

**Location**: `backend/orchestrator_agent.py`

**Responsibilities**:
- Receive user requests from the API
- Analyze requests with **contextual awareness** of user state and history
- **Intelligent Dimension Selection**: Choose conversation dimensions based on:
  - Topic characteristics and user history
  - User engagement level (response length, detail, enthusiasm)
  - Speech performance metrics (clarity trends, pace, confidence)
  - Dimension history (avoid repetition, enforce max 2 consecutive turns on same dimension)
- Determine which sub-agents to involve based on **contextual relevance**
- Delegate tasks to appropriate sub-agents with topic-specific guidance
- Synthesize responses from multiple agents
- Provide a unified, **contextually relevant** response to the user
- Return structured JSON with question, dimension, reasoning, and difficulty_level

**Configuration**:
- **Model**: OpenAI GPT-4o-mini (optimized for performance)
- **Mode**: Coordinate (default) - delegates and synthesizes
- **Members**: Conversation Agent, Response Agent, Vocabulary Agent

**Key Instructions**:
- Friendly and supportive team leader with strong reasoning capabilities
- **Topic-Based Reasoning**: Analyzes user-chosen topics to determine best conversation approach
- **Dimension Selection Rules**:
  - CRITICAL: Do NOT use the same dimension for more than 2 consecutive turns
  - If last 2 turns used same dimension, MUST switch to different dimension
  - Analyze dimension history and actively rotate through dimensions
  - Consider speech performance trends when selecting dimensions
- Delegates to Conversation Agent when topics are chosen
- Uses **contextual awareness** to choose appropriate dimensions for follow-up questions
- Ensures **contextual relevance** in all generated content
- Synthesizes member responses with attention to conversation flow
- Returns JSON: `{"question": "...", "dimension": "...", "reasoning": "...", "difficulty_level": 1}`

### Conversation Agent

The **Conversation Agent** is a specialized sub-agent responsible for generating **contextually relevant** conversation questions with **contextual awareness** of user responses and conversation history.

**Location**: `backend/subagents/conversation_agent.py`

**Responsibilities**:
- Generate **contextually relevant** questions for selected topics
- Use **contextual awareness** tools (`get_context`, `generate_followup_question`) for follow-up questions
- Ensure first question on any topic uses "Basic Preferences" dimension
- Generate follow-up questions with "Acknowledgement + Personal Preference + Question" pattern
- Maintain **contextual relevance** by varying acknowledgements and avoiding question repetition
- Adapt questions to multiple conversation dimensions based on orchestrator's **contextual awareness**
- Ensure questions are clear, simple, and encouraging

**Configuration**:
- **Model**: OpenAI GPT-4o-mini (optimized for performance)
- **Type**: Single Agent (member of Orchestrator Team)
- **Tools**: `get_context`, `generate_followup_question` (for **contextual awareness**)
- **Focus**: Context-aware question generation with **contextual relevance**

**Key Instructions**:
- Generate questions for autistic youth with **contextual awareness**
- For initial questions: Generate simple questions using "Basic Preferences" dimension
- For follow-up questions: Use tools to gather context and generate **contextually relevant** follow-ups
- Follow "Acknowledgement + Personal Preference + Question" format for follow-ups
- Vary acknowledgements to maintain natural conversation flow
- Never repeat the same question
- Ask about specific things mentioned in user responses (high **contextual relevance**)
- Adapt to 9 conversation dimensions based on orchestrator's **contextual awareness**

**Conversation Dimensions** (for **contextually relevant** follow-ups):
- Basic Preferences: Likes, dislikes, favorites, simple choices
- Depth/Specificity: Dig deeper into specific aspects
- Social Context: Involve friends, family, or social situations
- Emotional: Feelings, excitement, frustration, reactions
- Temporal/Frequency: When, how often, past experiences, future plans
- Comparative: Compare two things, what is better/worse
- Reflective/Why: Reasons, motivations, 'why' questions
- Descriptive/Detail: Sensory details, appearance, setting
- Challenge/Growth: Learning curves, difficulties, improvements

### Conversation Tools (Contextual Awareness)

The Conversation Agent uses specialized tools to maintain **contextual awareness** and generate **contextually relevant** follow-up questions.

**Location**: `backend/tools/conversation_tools.py`

**Tools**:

1. **`get_context`**: Gathers conversation context for **contextual awareness**
   - User's response
   - Current conversation dimension
   - Topic
   - Previous question
   - Returns structured context summary

2. **`generate_followup_question`**: Generates **contextually relevant** follow-up questions
   - Uses gathered context for **contextual awareness**
   - Ensures "Acknowledgement + Personal Preference + Question" format
   - Maintains **contextual relevance** by referencing specific user mentions
   - Varies acknowledgements to avoid repetition
   - Adapts to selected dimension

**Contextual Awareness Features**:
- Tracks previous questions to avoid repetition
- Maintains conversation history for **contextual relevance**
- Adapts questions to specific things mentioned by the user
- Ensures high **contextual relevance** in all follow-up questions

### Agent Communication Flow

#### Initial Question Flow
```
User Selects Topic
    │
    ▼
API Endpoint (/api/start_conversation)
    │
    ├─ Checks database for first question on topic
    ├─ Determines: "Basic Preferences" dimension
    │
    ▼
Conversation Agent (Direct Call)
    │
    ├─ Generates initial question
    ├─ Uses "Basic Preferences" dimension
    │
    ▼
Returns to API
    │
    ├─ Generates text-to-speech audio
    ├─ Returns question + audio
    │
    ▼
Frontend displays question + auto-plays audio
    │
    ▼
Background: Parallel loading of responses & vocabulary
```

#### Follow-Up Question Flow (Contextual Awareness)
```
User Responds
    │
    ▼
API Endpoint (/api/continue_conversation)
    │
    ├─ Orchestrator chooses dimension (contextual awareness)
    │
    ▼
Conversation Agent
    │
    ├─ Uses get_context tool (contextual awareness)
    │  ├─ Gathers: user response, dimension, topic, previous question
    │
    ├─ Uses generate_followup_question tool
    │  ├─ Generates contextually relevant follow-up
    │  ├─ Format: "Acknowledgement + Personal Preference + Question"
    │  ├─ Ensures contextual relevance to user's specific response
    │
    ▼
Returns to API
    │
    ├─ Formats question with line breaks
    ├─ Generates text-to-speech audio
    ├─ Returns question + audio
    │
    ▼
Frontend displays follow-up question + auto-plays audio
```

### Sub-Agents

#### Response Agent

**Location**: `backend/subagents/response_generate_agent.py`

**Responsibilities**:
- Generate **contextually relevant** response options based on question, dimension, and **topic**
- **Topic-Aware Generation**: Options MUST be specifically relevant to the topic (gaming→games, food→food, hobbies→hobbies)
- Create 2 response options plus "Choose your own response"
- Adapt to conversation dimension for **contextual relevance**
- Use user's previous response context when available for personalized options
- Ensure responses are simple and direct (Level 1 difficulty)
- **Aggressive Topic Enforcement**: NO generic options that could apply to any topic

**Configuration**:
- **Model**: OpenAI GPT-4o-mini
- **Type**: Sub-agent (member of Orchestrator Team)

#### Vocabulary Agent

**Location**: `backend/subagents/vocabulary_agent.py`

**Responsibilities**:
- Identify **contextually relevant** vocabulary words from questions
- Provide definitions and examples
- Ensure vocabulary is relevant to the specific question and topic

**Configuration**:
- **Model**: OpenAI GPT-4o-mini
- **Type**: Sub-agent (member of Orchestrator Team)

#### Speech Analysis Agent

**Location**: `backend/subagents/speech_analysis_agent.py`

**Responsibilities**:
- Transcribe user speech using OpenAI Whisper
- Analyze transcript for clarity, pace, and filler words
- Calculate Word Error Rate (WER) when expected response is provided
- Provide encouraging feedback with strengths and suggestions
- Award brownie points for 100% clarity

**Configuration**:
- **Model**: OpenAI GPT-4o-mini
- **Type**: Sub-agent (member of Orchestrator Team)
- **Tools**: Speech transcription tool

---

## API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### GET `/`
Health check endpoint.

**Response**:
```json
{
  "status": "ConvoBridge Backend Active"
}
```

#### POST `/api/login`
User login and session creation with **contextual awareness** of user state.

**Request Body**:
```json
{
  "username": "John"
}
```

**Response**:
```json
{
  "user_id": "uuid-here",
  "username": "John",
  "login_timestamp": "2025-01-16T10:30:00",
  "session_id": "session-uuid",
  "message": "Login successful"
}
```

**Features**:
- Creates or retrieves user from Supabase database
- Creates new session for tracking
- Returns user ID and session ID for **contextual awareness**

#### POST `/api/get_user`
Retrieve user information from database.

**Request Body**:
```json
{
  "user_id": "uuid-here"
}
```
or
```json
{
  "username": "John"
}
```

**Response**:
```json
{
  "user_id": "uuid-here",
  "username": "John",
  "created_at": "2025-01-16T10:30:00",
  "updated_at": "2025-01-16T10:30:00"
}
```

#### POST `/api/start_conversation`
Start a conversation by generating a **contextually relevant** initial question for a selected topic.

**Request Body**:
```json
{
  "topic": "gaming",
  "user_id": "uuid-here",
  "difficulty_level": 1,
  "session_id": "session-uuid"
}
```

**Request Schema**:
- `topic` (string, required): The conversation topic (e.g., "gaming", "food", "hobbies", "weekend", "youtube")
- `user_id` (string, required): Unique identifier for the user
- `difficulty_level` (integer, optional, default: 1): Conversation difficulty level
- `session_id` (string, required): Session identifier

**Response**:
```json
{
  "question": "What kind of video games do you enjoy playing the most?",
  "dimension": "Basic Preferences",
  "audio_base64": "base64-encoded-audio-string",
  "turn_id": "turn-uuid",
  "reasoning": "This question explores gaming preferences, appropriate for a first question."
}
```

**Response Schema**:
- `question` (string): Generated conversation question
- `dimension` (string): Conversation dimension used (always "Basic Preferences" for first question)
- `audio_base64` (string, optional): Base64-encoded audio for text-to-speech
- `turn_id` (string): Conversation turn ID for linking response options and vocabulary
- `reasoning` (string, optional): Orchestrator's reasoning for dimension selection

**Features**:
- **Orchestrator-Based**: Uses orchestrator for intelligent topic-based reasoning
- **Pre-Generation Support**: Checks cache for pre-generated first questions (instant topic selection)
- Always uses "Basic Preferences" dimension for first question on any topic
- **Optimized for Returning Users**: Skips history retrieval for first questions (faster response)
- Uses **contextual awareness** to check if this is the first question for the topic
- Generates text-to-speech audio automatically
- Returns question immediately (progressive loading)
- **Rate Limit Handling**: Automatic retry with exponential backoff

#### POST `/api/continue_conversation`
Generate a **contextually relevant** follow-up question with **contextual awareness** of user response and conversation history.

**Request Body**:
```json
{
  "topic": "gaming",
  "user_id": "uuid-here",
  "previous_question": "What kind of video games do you enjoy playing?",
  "user_response": "I like playing Super Mario",
  "difficulty_level": 1,
  "previous_turn_id": "turn-uuid"
}
```

**Request Schema**:
- `topic` (string, required): The conversation topic
- `user_id` (string, required): Unique identifier for the user
- `previous_question` (string, required): The previous question that was asked
- `user_response` (string, required): The user's response to the previous question
- `difficulty_level` (integer, optional, default: 1): Conversation difficulty level
- `previous_turn_id` (string, required): Previous conversation turn ID

**Response**:
```json
{
  "question": "That's great! I like that too.\n\nDo you play alone or with someone?",
  "dimension": "Social Context",
  "audio_base64": "base64-encoded-audio-string",
  "turn_id": "turn-uuid",
  "reasoning": "Switching to Social Context to explore gaming interactions, avoiding repetition of Basic Preferences."
}
```

**Response Schema**:
- `question` (string): Follow-up question with "Acknowledgement + Personal Preference + Question" format
- `dimension` (string): Conversation dimension chosen by orchestrator (based on **contextual awareness**)
- `audio_base64` (string, optional): Base64-encoded audio for text-to-speech (may be null if TTS still generating)
- `turn_id` (string): Conversation turn ID for linking response options and vocabulary
- `reasoning` (string, optional): Orchestrator's reasoning for dimension selection

**Features**:
- **Orchestrator-Based**: Uses orchestrator for intelligent dimension selection and question generation
- **Dimension Switching Enforcement**: Automatically switches dimension if same dimension used 2+ times consecutively
- **Speech Performance Integration**: Considers speech metrics (clarity, pace, trends) when selecting dimensions
- **Pre-Generation Support**: Checks cache for pre-generated questions (instant response after speech analysis)
- **Optimized Performance**:
  - Parallelizes orchestrator call + previous turn update
  - Returns question before TTS completion (TTS continues in background)
  - Reduced prompt size for faster LLM response
- Orchestrator analyzes user engagement, dimension history, and speech performance
- Ensures **contextual relevance** by referencing specific things mentioned by user
- Varies acknowledgements to maintain natural conversation
- Never repeats the same question
- **Rate Limit Handling**: Automatic retry with exponential backoff

#### POST `/api/get_conversation_details`
Background endpoint for loading response options and vocabulary in parallel (progressive loading).

**Request Body**:
```json
{
  "question": "What kind of video games do you enjoy playing?",
  "topic": "gaming",
  "turn_id": "turn-uuid",
  "difficulty_level": 1,
  "dimension": "Basic Preferences",
  "user_response": "I like action games"
}
```

**Request Schema**:
- `question` (string, required): The conversation question
- `topic` (string, required): The conversation topic
- `turn_id` (string, required): Conversation turn ID for saving response options and vocabulary
- `difficulty_level` (integer, optional, default: 1): Conversation difficulty level
- `dimension` (string, optional, default: "Basic Preferences"): Conversation dimension
- `user_response` (string, optional): User's previous response for context-aware options

**Response**:
```json
{
  "response_options": [
    "I really enjoy playing action games like Call of Duty.",
    "I prefer puzzle games because they challenge my mind.",
    "Choose your own response"
  ],
  "vocabulary": {
    "word": "Gaming",
    "type": "noun",
    "definition": "The activity of playing video games.",
    "example": "Gaming is a popular hobby."
  }
}
```

**Features**:
- **Topic-Aware Generation**: Response options are specifically relevant to the topic (gaming→games, food→food, etc.)
- Runs in parallel for performance
- Generates **contextually relevant** response options based on question, dimension, and topic
- Uses user's previous response context when available for personalized options
- Generates **contextually relevant** vocabulary word for the specific question
- Saves response options and vocabulary to database linked to turn_id

#### POST `/api/text_to_speech`
Generate speech from text using OpenAI's TTS API (on-demand audio generation).

**Request Body**:
```json
{
  "text": "What kind of video games do you enjoy playing?",
  "voice": "nova",
  "model": "tts-1-hd",
  "format": "mp3"
}
```

**Response**:
```json
{
  "audio_base64": "base64-encoded-audio-string",
  "format": "mp3"
}
```

**Features**:
- Direct OpenAI TTS API integration
- Configurable voice, model, and format
- Used for on-demand audio replay

#### POST `/api/process-audio`
Process uploaded audio file for speech analysis with **contextual awareness**.

**Request** (multipart/form-data):
- `audio` (file, required): Audio file (webm, mp3, wav, m4a)
- `expected_response` (string, optional): Expected response text for WER calculation

**Response**:
```json
{
  "transcript": "I like playing Super Mario",
  "wer_estimate": 0.05,
  "clarity_score": 0.95,
  "pace_wpm": 120,
  "filler_words": ["um"],
  "feedback": "Great job! Your speech was clear and easy to understand.",
  "strengths": ["Clear pronunciation", "Good pace"],
  "suggestions": ["Try to reduce filler words"]
}
```

**Features**:
- Transcribes audio using OpenAI Whisper
- Analyzes speech with **contextual awareness** of expected response
- Provides clarity score, pace, and feedback
- Awards brownie points for 100% clarity
- Supports multiple audio formats (converts via ffmpeg if needed)

### CORS Configuration

The API is configured to accept requests from:
- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:3001`

---

## Frontend Architecture

### Component Hierarchy

```
ChatPage (page.tsx)
└── ChatNavbar
└── ChatInterface
    ├── Topic Selection Panel
    ├── Question Display Area
    ├── Response Options
    └── Vocabulary Panel
```

### Key Components

#### ChatInterface (`app/chat/components/ChatInterface.tsx`)

Main chat interface component that handles:
- Topic selection
- API communication with backend
- Question display
- Response option rendering
- Loading states
- Error handling

**State Management**:
- `currentTopic`: Currently selected topic
- `question`: Generated question text
- `previousQuestion`: Previous question for **contextual awareness**
- `questionAudio`: Base64 audio data for text-to-speech
- `isPlayingAudio`: Audio playback state
- `responses`: Array of response options
- `vocab`: Vocabulary word object
- `isLoading`: Loading state
- `welcomeMessage`: Welcome message state
- `speechAnalysis`: Speech analysis results
- `browniePoints`: User's earned points
- `clarityPointsAnimation`: Animation state for clarity points

**Key Functions**:
- `handleTopicSelect(topicId)`: Handles topic selection and API call (progressive loading)
- `handleContinueChat()`: Generates **contextually relevant** follow-up questions
- `handleListenClick()`: Plays or generates audio for question
- `playAudio()`: Plays base64-encoded audio
- `startRecording()` / `stopRecording()`: Speech recording functionality
- `handleAudioUpload()`: Processes recorded audio for analysis

#### ChatNavbar (`app/chat/components/ChatNavbar.tsx`)

Navigation bar component for the chat interface.

### Styling Architecture

The frontend uses a cyberpunk-themed design system with:
- **Color Palette**: Copper/Orange accents, Cyan highlights, Black background
- **Typography**: Geist Sans and Geist Mono fonts
- **Effects**: Glow effects, backdrop blur, animated backgrounds
- **Responsive**: Mobile-first design with Tailwind CSS

**CSS Variables** (defined in `globals.css`):
- `--copper`: Primary accent color (#FF6B35)
- `--cyan`: Secondary accent color (#00E5FF)
- `--background`: Background color (#000000)
- `--foreground`: Text color (#ffffff)

---

## Setup & Installation

### Prerequisites

- **Node.js**: v18+ (for Next.js)
- **Python**: 3.8+ (for backend)
- **OpenAI API Key**: Required for AI functionality

### Frontend Setup

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install agno fastapi uvicorn python-dotenv openai
```

3. Create `.env` file in `backend/` directory:
```env
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

4. Start the backend server:
```bash
python main.py
```

The server will start on `http://localhost:8000`

### Environment Variables

**Backend** (`backend/.env`):
- `OPENAI_API_KEY` (required): Your OpenAI API key for LLM, TTS, and speech transcription
- `SUPABASE_URL` (optional but recommended): Your Supabase project URL for database integration
- `SUPABASE_ANON_KEY` (optional but recommended): Your Supabase anonymous key for database access

**Note**: If Supabase credentials are not provided, the system will fall back to in-memory user ID generation, but session tracking and conversation history will not persist.

**Frontend**: No environment variables required for basic setup.

---

## Development Workflow

### Running the Full Stack

1. **Terminal 1 - Backend**:
```bash
cd backend
python main.py
```

2. **Terminal 2 - Frontend**:
```bash
npm run dev
```

### Testing Agents

#### Test Orchestrator Team
```bash
cd backend
python orchestrator_agent.py
```

#### Test Conversation Agent
```bash
cd backend
python subagents/conversation_agent.py
```

### Adding New Sub-Agents

1. Create a new file in `backend/subagents/`:
```python
# backend/subagents/new_agent.py
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def create_new_agent():
    agent = Agent(
        name="New Agent",
        model=OpenAIChat(id="gpt-4o"),
        description="Agent description",
        instructions=[
            "Instruction 1",
            "Instruction 2",
        ],
        markdown=True,
    )
    return agent
```

2. Import and add to orchestrator team in `orchestrator_agent.py`:
```python
from subagents.new_agent import create_new_agent

def create_orchestrator_agent():
    conversation_agent = create_conversation_agent()
    new_agent = create_new_agent()
    
    team = Team(
        # ... existing config ...
        members=[conversation_agent, new_agent],
    )
    return team
```

---

## Database Schema (Supabase)

The system uses Supabase (PostgreSQL) for persistent data storage with **contextual awareness** of user history and conversation flow.

### Key Tables

1. **`users`**: User accounts and profiles
   - `id` (UUID): Unique user identifier
   - `name` (string): Username
   - `created_at`, `updated_at`: Timestamps

2. **`sessions`**: User session tracking
   - `id` (UUID): Session identifier
   - `user_id` (UUID): Reference to user
   - `started_at`, `ended_at`: Session timestamps
   - `status`: Active or completed

3. **`session_topics`**: Topic tracking per session (for **contextual awareness**)
   - `session_id` (UUID): Reference to session
   - `topic_name` (string): Topic name
   - `turn_count` (integer): Number of turns for this topic

4. **`conversation_turns`**: Conversation history (for **contextual awareness**)
   - Stores questions, responses, dimensions
   - Enables **contextual relevance** in follow-ups

### Contextual Awareness Features

- **First Question Detection**: System checks if this is the first question for a topic using `session_topics` table
- **User History**: Tracks conversation history for **contextual relevance**
- **Session Continuity**: Maintains session state for **contextual awareness** across interactions

## Tools & Utilities

### Conversation Tools (`backend/tools/conversation_tools.py`)

Specialized tools for **contextual awareness** and **contextually relevant** question generation:

1. **`get_context`**: Gathers conversation context
   - User response
   - Current dimension
   - Topic
   - Previous question
   - Returns structured context for **contextual awareness**

2. **`generate_followup_question`**: Generates **contextually relevant** follow-up questions
   - Uses context for **contextual awareness**
   - Ensures "Acknowledgement + Personal Preference + Question" format
   - Maintains **contextual relevance** to user's specific response

### Text-to-Speech Tool (`backend/tools/text_to_speech.py`)

- Direct OpenAI TTS API integration
- Generates audio from text
- Supports multiple voices and formats
- Returns base64-encoded audio for frontend playback

### Speech Transcription Tool (`backend/tools/speech_transcription_tool.py`)

- OpenAI Whisper integration
- Transcribes audio to text
- Used by Speech Analysis Agent

## Progressive Loading Architecture

The system uses a **progressive loading** strategy for optimal UX:

1. **Fast Path**: `/api/start_conversation` returns question immediately
2. **Background Path**: `/api/get_conversation_details` loads responses and vocabulary in parallel
3. **Result**: User sees question immediately while other content loads in background

This ensures **contextually relevant** questions appear quickly while maintaining full functionality.

## Pre-Generation System

The system implements intelligent pre-generation to minimize user wait times:

### First Question Pre-Generation
- **On Login**: Pre-generates first questions for ALL topics in the background
- **Sequential Processing**: Topics processed one-by-one with 2-second delays to avoid rate limits
- **Caching**: First questions cached for 30 minutes with user-specific keys
- **Instant Topic Selection**: When user selects a topic, question is served from cache (instant response)
- **Race Condition Handling**: If user selects topic before pre-generation completes, system waits up to 10 seconds

### Next Question Pre-Generation
- **After Speech Analysis**: Automatically pre-generates next follow-up question
- **Background Processing**: Runs asynchronously after speech analysis completes
- **Caching**: Questions cached with 5-minute TTL, keyed by user_id + topic + previous_turn_id
- **Instant Continue Chat**: When user clicks "Continue Chat", question served from cache
- **Status Polling**: Frontend polls `/api/check_pre_generation_status` to enable button when ready
- **Hybrid Approach**: Button enables after 4 seconds OR when ready (whichever comes first)

### Cache Management
- **In-Memory Cache**: Thread-safe dictionary with expiration tracking
- **Cache Keys**: Normalized (lowercase, trimmed) to ensure consistency
- **Cache Clearing**: Automatically cleared when user starts new conversation or changes topic
- **Fallback**: If pre-generation fails or cache miss, system falls back to on-demand generation

## Performance Optimizations

### Database Query Optimization
- **Parallel Queries**: Conversation history, dimension history, and speech metrics fetched concurrently using `asyncio.gather`
- **Query Caching**: Database query results cached for 30 seconds to reduce redundant queries
- **Cache Keys**: User-specific cache keys ensure data consistency

### LLM Token Reduction
- **Compressed Speech Context**: Ultra-compressed format (e.g., `sp:tr=i,cl=0.88`)
- **Rule-Based History Summarization**: Concise summaries of conversation history (max 2-3 turns)
- **Structured JSON Context**: Compact JSON format with shortened field names
- **Shortened Instructions**: Minimal task instructions referencing system instructions
- **Truncated Context**: Previous questions and responses truncated to essential length

### Response Time Optimization
- **Parallel Orchestrator + Database Update**: Previous turn update runs in parallel with orchestrator call
- **Return Before TTS**: Question returned immediately, TTS continues in background (1-second wait max)
- **Simplified First Questions**: Returning users skip history retrieval for first questions

### Rate Limit Handling
- **Automatic Retry**: 3 retry attempts with exponential backoff (2s → 4s → 8s)
- **Error Detection**: Detects rate limit errors by checking for "rate limit", "tpm", or "rpm" in error messages
- **Graceful Degradation**: Pre-generation failures don't block user flow (fallback to on-demand)
- **User-Friendly Errors**: Returns HTTP 429 with clear message for user-facing endpoints

## Contextual Awareness & Relevance

### Contextual Awareness Features

1. **Conversation Context Tracking**:
   - Maintains user response history
   - Tracks previous questions to avoid repetition
   - Monitors conversation dimensions used
   - Tracks speech performance metrics and trends

2. **Contextual Relevance in Questions**:
   - Follow-up questions reference specific things mentioned by user
   - Questions adapt to user's interests and responses
   - High **contextual relevance** ensures natural conversation flow
   - Topic-aware question generation

3. **Intelligent Dimension Selection**:
   - Orchestrator uses **contextual awareness** to choose appropriate dimensions
   - **Dimension Switching Enforcement**: Automatically switches dimension if same dimension used 2+ consecutive turns
   - Dimensions adapt based on:
     - User engagement level (response length, detail, enthusiasm)
     - Speech performance metrics (clarity trends, pace, confidence)
     - Dimension history (avoid recent repetition)
     - Topic characteristics
   - Ensures **contextually relevant** follow-up questions

4. **Speech Performance Feedback Loop**:
   - Speech analysis metrics influence orchestrator decisions
   - **Immediate Feedback**: Next question adapts based on recent speech performance
   - **Trend Analysis**: Analyzes clarity/pace trends over multiple turns
   - **Adaptive Difficulty**: Adjusts difficulty level based on confidence and clarity trends
   - **Dimension Adaptation**: Selects dimensions that match user's performance level

5. **Variety & Naturalness**:
   - Varies acknowledgements to avoid repetition
   - Never repeats the same question
   - Maintains **contextual relevance** while keeping conversations fresh
   - Active dimension rotation prevents getting stuck on one dimension

## Recent Architectural Improvements (v2.1.0)

### Orchestrator Integration
- **Full Orchestrator Control**: All question generation now goes through orchestrator for intelligent decision-making
- **Topic-Based Reasoning**: Orchestrator analyzes user-chosen topics and selects appropriate dimensions
- **Structured JSON Response**: Orchestrator returns `{"question", "dimension", "reasoning", "difficulty_level"}` for transparency
- **Reasoning Visibility**: Orchestrator's reasoning included in API responses for debugging and transparency

### Dimension Switching Enforcement
- **Max 2 Consecutive Turns**: System enforces maximum 2 consecutive turns on same dimension
- **Automatic Detection**: Checks last 2 dimensions in history before generating next question
- **Forced Switching**: If same dimension detected 2+ times, explicit warning added to orchestrator prompt
- **Active Rotation**: Ensures conversation variety and prevents getting stuck on one dimension

### Speech Analysis Feedback Loop
- **Immediate Adaptation**: Next question adapts based on recent speech performance
- **Trend Analysis**: Analyzes clarity/pace trends over multiple turns
- **Confidence-Based Selection**: Selects dimensions and adjusts difficulty based on confidence level
- **Performance Context**: Speech metrics included in orchestrator prompt for informed decisions

### Topic-Aware Response Generation
- **Topic Context**: Response agent receives topic information in prompt
- **Aggressive Enforcement**: Short, aggressive prompts ensure topic-specific options
- **No Generic Options**: System prevents generic responses that could apply to any topic
- **User Context Integration**: Combines topic awareness with user's previous response for personalized options

### Performance Optimizations
- **Parallel Database Queries**: Conversation history, dimensions, and speech metrics fetched concurrently
- **Database Query Caching**: 30-second cache for database query results
- **LLM Token Reduction**: 
  - Compressed speech context format
  - Rule-based history summarization
  - Structured JSON with shortened field names
  - Truncated context fields
- **Response Time Improvements**:
  - Parallel orchestrator + database update
  - Return question before TTS completion
  - Simplified first questions (skip history for returning users)

### Rate Limit Resilience
- **Automatic Retry**: 3 retry attempts with exponential backoff (2s → 4s → 8s)
- **Error Detection**: Intelligent detection of rate limit errors
- **Graceful Degradation**: Pre-generation failures don't block user flow
- **Sequential Pre-Generation**: First questions generated sequentially with delays to avoid rate limits

## Future Enhancements

### Planned Features

1. **Enhanced Contextual Awareness**
   - Deeper conversation history analysis
   - User preference learning
   - Adaptive dimension selection based on engagement patterns

2. **Advanced Speech Features**
   - Real-time speech feedback
   - Pronunciation practice
   - Accent and dialect adaptation

3. **Progress Tracking**
   - Conversation skill progression
   - Vocabulary mastery tracking
   - Personalized difficulty adjustment

4. **Social Features**
   - Conversation sharing
   - Progress comparison (anonymized)
   - Achievement system

### Technical Improvements

1. **Enhanced Contextual Awareness**
   - Machine learning for dimension selection
   - Predictive question generation
   - User preference modeling

2. **Performance Optimization**
   - Response caching with **contextual awareness**
   - Async processing improvements
   - Load balancing for multiple users

3. **Testing**
   - Unit tests for agents and tools
   - Integration tests for API
   - E2E tests for frontend
   - Contextual relevance validation tests

---

## Architecture Decisions

### Why Agno Teams?

- **Modularity**: Easy to add/remove agents without rewriting core logic
- **Coordination**: Built-in delegation and synthesis capabilities
- **Scalability**: Can handle complex multi-agent workflows
- **Maintainability**: Clear separation of agent responsibilities

### Why FastAPI?

- **Performance**: High-performance async framework
- **Type Safety**: Built-in Pydantic validation
- **Documentation**: Auto-generated API docs
- **Modern**: Python 3.8+ features, async/await support

### Why Next.js App Router?

- **Modern React**: Latest React features and patterns
- **Server Components**: Better performance and SEO
- **TypeScript**: Built-in TypeScript support
- **Developer Experience**: Excellent tooling and hot reload

---

## Security Considerations

### Current Implementation

- CORS configured for localhost only
- API keys stored in environment variables
- No user authentication (planned)

### Future Security Enhancements

- User authentication and authorization
- Rate limiting for API endpoints
- Input validation and sanitization
- HTTPS in production
- API key rotation
- Session management

---

## Troubleshooting

### Common Issues

1. **Backend not starting**
   - Check if port 8000 is available
   - Verify OpenAI API key is set in `.env`
   - Ensure all dependencies are installed

2. **Frontend can't connect to backend**
   - Verify backend is running on port 8000
   - Check CORS configuration
   - Verify API endpoint URLs

3. **Agent not generating questions**
   - Check OpenAI API key is valid
   - Verify API quota/limits
   - Check backend logs for errors

---

## Contributing

When adding new features:

1. Follow the existing agent structure in `subagents/`
2. Update `orchestrator_agent.py` to include new agents
3. Update API endpoints in `main.py` if needed
4. Update this documentation
5. Test thoroughly before committing

---

## License

[Add license information here]

---

## Contact & Support

[Add contact information here]

---

**Last Updated**: 2026-02-17
**Version**: 2.1.0

## Key Architectural Concepts

### Contextual Awareness

The system maintains **contextual awareness** throughout conversations by:
- Tracking user responses and conversation history
- Using specialized tools (`get_context`, `generate_followup_question`) to gather context
- Maintaining session state in Supabase database
- Adapting questions based on user engagement and responses

### Contextual Relevance

All generated content maintains high **contextual relevance** by:
- Referencing specific things mentioned by users
- Adapting questions to user interests and responses
- Ensuring follow-up questions relate directly to previous responses
- Using conversation dimensions that match user engagement patterns
- Varying content while maintaining relevance to conversation flow

### Progressive Loading

The system optimizes user experience through progressive loading:
- Questions appear immediately upon topic selection
- Response options and vocabulary load in parallel in the background
- Text-to-speech audio is generated automatically and plays on question display
- Users can replay audio on-demand via the listen button

### Multi-Dimensional Conversations

The system supports 9 conversation dimensions for varied, **contextually relevant** follow-ups:
1. Basic Preferences (always used for first question)
2. Depth/Specificity
3. Social Context
4. Emotional
5. Temporal/Frequency
6. Comparative
7. Reflective/Why
8. Descriptive/Detail
9. Challenge/Growth

The orchestrator uses **contextual awareness** to select the most appropriate dimension for each follow-up question.
