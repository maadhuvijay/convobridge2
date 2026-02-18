# ConvoBridge

**Version**: 2.1.0  
**Last Updated**: 2026-02-17

**ConvoBridge** is a conversation practice platform designed to help autistic youth build confidence in social interactions through structured, AI-powered conversation sessions. The system uses an intelligent multi-agent orchestration architecture that adapts to each user's speech performance in real-time.

---

## 🎯 Overview

ConvoBridge uses a **multi-agent orchestration system** where an intelligent **Orchestrator Team** coordinates specialized sub-agents to deliver personalized, adaptive conversation practice sessions. The system learns from user's speech performance and adapts questions, difficulty, and conversation dimensions to create a truly personalized learning experience.

### Key Highlights

- **Intelligent Orchestration**: Orchestrator makes context-aware decisions based on multiple data sources
- **Speech Performance Feedback Loop**: System adapts in real-time based on user's speech clarity, pace, and confidence
- **9 Conversation Dimensions**: Varied, engaging conversations that never get repetitive
- **Pre-Generation System**: Instant question delivery through intelligent caching
- **Topic-Specific Content**: All responses and vocabulary are relevant to chosen topics

---

## ✨ Features

### Core Features

- **Topic-Based Conversations**: Select from predefined topics (Gaming, Food, Hobbies, Weekend Plans, YouTube)
- **Intelligent Question Generation**: Orchestrator-based question generation with 9 conversation dimensions
- **Speech Analysis**: Real-time speech transcription, clarity scoring (0-100), pace analysis, and encouraging feedback
- **Text-to-Speech**: Automatic audio generation for all questions with on-demand replay
- **Structured Responses**: 2 topic-specific response options plus "Choose your own response"
- **Vocabulary Learning**: Contextually relevant vocabulary words with definitions and examples
- **User & Session Management**: Persistent user tracking and session management via Supabase
- **Progressive Loading**: Optimized UX with immediate question display and background content loading

### Advanced Features

- **Pre-Generation System**: 
  - First questions pre-generated on login (instant topic selection)
  - Next questions pre-generated after speech analysis (instant continue chat)
- **Speech Performance Feedback Loop**: 
  - Speech metrics influence orchestrator decisions
  - Adaptive difficulty and dimension selection
  - Trend analysis (improving/declining/stable)
- **Dimension Switching Enforcement**: Automatically prevents repetition (max 2 consecutive turns on same dimension)
- **Parallel Execution**: Response options and vocabulary generated simultaneously
- **Performance Optimizations**: 
  - Database query caching (30-second TTL)
  - Token optimization (60-70% reduction)
  - Parallel TTS + database operations

---

## 🏗️ Architecture

### Multi-Agent System

ConvoBridge uses a **multi-agent orchestration architecture** built with Agno Teams:

```
┌─────────────────────────────────────────────────────────────┐
│              Orchestrator Team (Coordinator)                │
│  - Intelligent decision-making                              │
│  - Coordinates all sub-agents                               │
│  - Adapts to user performance                               │
│  - Returns: {question, dimension, reasoning, difficulty}    │
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

### Agent Responsibilities

1. **Orchestrator Team**: 
   - Topic-based reasoning
   - Intelligent dimension selection (9 dimensions)
   - Speech performance integration
   - Difficulty adjustment
   - Sub-agent coordination

2. **Conversation Agent**: 
   - Generates contextually relevant questions
   - Follow-up questions with "Acknowledgement + Personal Preference + Question" pattern
   - Adapts to conversation dimensions and difficulty

3. **Response Agent**: 
   - Generates 2 topic-specific response options
   - Ensures options are relevant to chosen topic
   - Considers user's previous responses

4. **Vocabulary Agent**: 
   - Identifies contextually relevant vocabulary words
   - Provides definitions and examples
   - Matches question and topic context

5. **Speech Analysis Agent**: 
   - Transcribes audio using Whisper API
   - Analyzes clarity, pace, filler words
   - Provides encouraging feedback
   - Creates feedback loop with orchestrator

### 9 Conversation Dimensions

- **Basic Preferences**: Likes, dislikes, favorites (always used for first question)
- **Depth/Specificity**: Deeper, more detailed questions
- **Social Context**: Social aspects of the topic
- **Emotional**: Feelings about the topic
- **Temporal/Frequency**: When, how often, past experiences
- **Comparative**: Comparing different aspects
- **Reflective/Why**: Reasons and motivations
- **Descriptive/Detail**: Detailed descriptions
- **Challenge/Growth**: Challenges and personal growth

---

## 🚀 Quick Start

### Prerequisites

- **Node.js**: v18+ (for Next.js)
- **Python**: 3.8+ (for backend)
- **OpenAI API Key**: Required for AI functionality (GPT-4o-mini, TTS, Whisper)
- **Supabase** (Optional but recommended): For user and session management

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

3. Create `.env` file in `backend/` directory:
```env
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

**Note**: If Supabase credentials are not provided, the system will fall back to in-memory user ID generation, but session tracking and conversation history will not persist.

4. Start the backend server:
```bash
python main.py
```

The backend will run on `http://localhost:8000`

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

---

## 📁 Project Structure

```
convobridge2/
├── app/                          # Next.js frontend (App Router)
│   ├── chat/                     # Chat interface pages
│   │   ├── page.tsx             # Main chat page
│   │   └── components/          # Chat components
│   │       └── ChatInterface.tsx # Main chat interface
│   ├── login/                   # Login page
│   ├── components/              # Shared components
│   │   ├── Hero.tsx            # Home page hero
│   │   └── Navbar.tsx          # Navigation bar
│   └── globals.css              # Global styles
├── backend/                      # Python backend
│   ├── main.py                  # FastAPI application & API endpoints
│   ├── orchestrator_agent.py    # Orchestrator Team
│   ├── database.py             # Supabase database operations
│   ├── subagents/               # Sub-agent modules
│   │   ├── conversation_agent.py      # Question generation
│   │   ├── response_generate_agent.py # Response options
│   │   ├── vocabulary_agent.py        # Vocabulary words
│   │   └── speech_analysis_agent.py  # Speech analysis
│   └── tools/                   # Utility tools
│       ├── conversation_tools.py     # Conversation context tools
│       ├── text_to_speech.py         # TTS integration
│       └── speech_transcription_tool.py # Whisper integration
├── ARCHITECTURE.md              # Comprehensive technical documentation
├── AGENT_FLOW.md                # Detailed agent flow documentation
├── DATAFLOW.md                  # Complete dataflow diagrams
├── DEMO_AGENT_ARCHITECTURE.md  # Demo-ready agent architecture
├── ORCHESTRATOR_SPEECH_INTERACTION.md # Orchestrator-Speech interaction
└── README.md                    # This file
```

---

## 🛠️ Technology Stack

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
- **TTS Provider**: OpenAI TTS API (tts-1-hd model, voice: nova)
- **Speech Recognition**: OpenAI Whisper API
- **Database**: Supabase (PostgreSQL)
- **Server**: Uvicorn (ASGI)
- **Audio Processing**: ffmpeg (for format conversion)

---

## 📚 Documentation

### Core Documentation

- **[ARCHITECTURE.md](./ARCHITECTURE.md)**: Comprehensive technical architecture documentation
  - System architecture
  - Agent system design
  - API documentation
  - Performance optimizations
  - Recent improvements (v2.1.0)

- **[DEMO_AGENT_ARCHITECTURE.md](./DEMO_AGENT_ARCHITECTURE.md)**: Demo-ready agent architecture document
  - Agent hierarchy and responsibilities
  - Interaction flows
  - Key features and highlights

- **[DATAFLOW.md](./DATAFLOW.md)**: Complete dataflow documentation
  - Detailed flow diagrams
  - Technical features
  - Performance optimizations
  - API endpoint flows

- **[AGENT_FLOW.md](./AGENT_FLOW.md)**: Detailed agent flow documentation
  - Orchestrator abilities
  - Agent interaction patterns
  - Decision-making processes

- **[ORCHESTRATOR_SPEECH_INTERACTION.md](./ORCHESTRATOR_SPEECH_INTERACTION.md)**: Orchestrator-Speech Analysis interaction
  - Feedback loop mechanism
  - Speech performance integration
  - Adaptation strategies

---

## 🎯 Key Features Explained

### 1. Intelligent Orchestration

The Orchestrator Team makes intelligent decisions by:
- Analyzing user-chosen topics
- Selecting appropriate conversation dimensions (9 available)
- Considering speech performance metrics
- Enforcing dimension variety (max 2 consecutive turns on same dimension)
- Adjusting difficulty based on user performance

### 2. Speech Performance Feedback Loop

**How it works**:
1. User records audio response
2. Speech Analysis Agent analyzes clarity, pace, filler words
3. Metrics saved to database
4. Orchestrator retrieves metrics when generating next question
5. Next question adapts based on performance:
   - **Improving clarity** → Increase challenge
   - **Declining clarity** → Simplify, provide support
   - **High clarity (>0.85)** → User excelling, can increase challenge
   - **Low clarity (<0.65)** → User struggling, provide more support

### 3. Pre-Generation System

**First Questions**:
- Pre-generated for all topics on user login
- Cached for 30 minutes
- Instant topic selection (<100ms response time)

**Next Questions**:
- Pre-generated after speech analysis completes
- Cached for 5 minutes
- Instant "Continue Chat" response (<100ms response time)

### 4. Performance Optimizations

- **Parallel Database Queries**: Conversation history, dimensions, and speech metrics fetched concurrently
- **Database Query Caching**: 30-second TTL cache reduces redundant queries
- **Token Optimization**: 60-70% reduction in LLM token usage through:
  - Ultra-compressed speech context
  - Rule-based history summarization
  - Structured JSON with shortened field names
- **Parallel Execution**: TTS generation and database saves run in parallel

---

## 🧪 Testing Agents

### Test Orchestrator Team
```bash
cd backend
python orchestrator_agent.py
```

### Test Conversation Agent
```bash
cd backend
python subagents/conversation_agent.py
```

### Test Response Agent
```bash
cd backend
python subagents/response_generate_agent.py
```

### Test Vocabulary Agent
```bash
cd backend
python subagents/vocabulary_agent.py
```

### Test Speech Analysis Agent
```bash
cd backend
python subagents/speech_analysis_agent.py
```

---

## 📊 API Endpoints

### Core Endpoints

- `POST /api/login` - User login and session creation
- `POST /api/logout` - User logout and session termination
- `POST /api/start_conversation` - Generate first question for a topic
- `POST /api/continue_conversation` - Generate follow-up question
- `POST /api/get_conversation_details` - Generate response options and vocabulary
- `POST /api/process-audio` - Speech analysis and transcription
- `POST /api/text_to_speech` - On-demand TTS audio generation
- `POST /api/check_pre_generation_status` - Check if pre-generated question is ready

For detailed API documentation, see [ARCHITECTURE.md](./ARCHITECTURE.md#api-documentation).

---

## 🎨 UI Features

- **Cyberpunk Theme**: Modern, engaging interface with copper/cyan accents
- **Real-time Updates**: Instant question display with progressive loading
- **Speech Analysis Display**: Visual clarity scores, pace, filler words, and feedback
- **Vocabulary Bonus Challenge**: Expandable section for vocabulary practice (+20 brownie points)
- **Brownie Points System**: Gamification with coin icons
- **Responsive Design**: Mobile-first approach with Tailwind CSS

---

## 🔄 Recent Updates (v2.1.0)

### Orchestrator Integration
- ✅ Full orchestrator control for all question generation
- ✅ Topic-based reasoning and intelligent dimension selection
- ✅ Structured JSON response with reasoning visibility
- ✅ Speech performance integration

### Performance Optimizations
- ✅ Pre-generation system (first questions + next questions)
- ✅ Parallel database queries and caching
- ✅ Token optimization (60-70% reduction)
- ✅ Parallel TTS + database operations

### Speech Feedback Loop
- ✅ Speech metrics influence orchestrator decisions
- ✅ Trend analysis (improving/declining/stable)
- ✅ Adaptive difficulty and dimension selection

### Dimension Switching
- ✅ Automatic enforcement (max 2 consecutive turns)
- ✅ Active dimension rotation
- ✅ Variety maintenance

### Topic-Aware Generation
- ✅ Response options are topic-specific
- ✅ Aggressive topic enforcement
- ✅ No generic content

---

## 🔮 Future Enhancements

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

---

## 🤝 Contributing

When adding new features:

1. Follow the existing agent structure in `backend/subagents/`
2. Update `orchestrator_agent.py` to include new agents if needed
3. Update API endpoints in `backend/main.py` if needed
4. Update documentation (ARCHITECTURE.md, AGENT_FLOW.md, etc.)
5. Test thoroughly before committing

---

## 📝 License

[Add license information here]

---

## 🙏 Acknowledgments

Built with ❤️ for helping autistic youth build conversation confidence through AI-powered practice sessions.

---

**For detailed technical documentation, see [ARCHITECTURE.md](./ARCHITECTURE.md)**  
**For demo presentation, see [DEMO_AGENT_ARCHITECTURE.md](./DEMO_AGENT_ARCHITECTURE.md)**  
**For complete dataflow, see [DATAFLOW.md](./DATAFLOW.md)**
