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

**ConvoBridge** is a conversation practice platform designed to help autistic youth build confidence in social interactions through structured, AI-powered conversation sessions. The system uses a multi-agent architecture to generate contextually appropriate questions and responses based on selected topics.

### Key Features
- **Topic-Based Conversations**: Users select from predefined topics (Gaming, Food, Hobbies, etc.)
- **AI-Generated Questions**: Dynamic question generation focused on "basic preferences" dimension
- **Structured Responses**: Pre-generated response options to guide users
- **Vocabulary Learning**: Integrated vocabulary feature (planned)
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
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└────────────────────────────┬────────────────────────────────┘
                              │ HTTP/REST API
                              │ (CORS Enabled)
┌─────────────────────────────▼────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         API Endpoints (/api/start_conversation)        │  │
│  └────────────────────┬───────────────────────────────────┘  │
│                       │                                       │
│  ┌────────────────────▼───────────────────────────────────┐  │
│  │         Orchestrator Team (Agno Team)                   │  │
│  │  - Coordinates sub-agents                               │  │
│  │  - Delegates tasks                                       │  │
│  │  - Synthesizes responses                                │  │
│  └────────────────────┬───────────────────────────────────┘  │
│                       │                                       │
│  ┌────────────────────▼───────────────────────────────────┐  │
│  │         Sub-Agents (Agno Agents)                        │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  Conversation Agent                               │  │  │
│  │  │  - Generates questions                            │  │  │
│  │  │  - Focus: Basic preferences                       │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  Response Agent (Planned)                         │  │  │
│  │  │  Vocabulary Agent (Planned)                       │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                       │                                       │
│  ┌────────────────────▼───────────────────────────────────┐  │
│  │         OpenAI GPT-4o (via Agno)                       │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Principles

1. **Multi-Agent System**: Uses Agno's Team architecture for coordinated agent collaboration
2. **Separation of Concerns**: Frontend handles UI, backend handles AI logic
3. **Modular Design**: Sub-agents are independently developed and can be added incrementally
4. **RESTful API**: Clean API interface between frontend and backend
5. **Scalable**: Team-based architecture allows easy addition of new agents

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
- **LLM Provider**: OpenAI GPT-4o
- **Server**: Uvicorn (ASGI)
- **Environment**: python-dotenv
- **CORS**: FastAPI CORS Middleware

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
│   ├── main.py                   # FastAPI application
│   ├── orchestrator_agent.py    # Orchestrator team
│   ├── requirements.txt          # Python dependencies
│   └── subagents/                # Sub-agent modules
│       └── conversation_agent.py # Conversation question generator
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

The **Orchestrator Team** is the central coordination point for all agent interactions. It uses Agno's Team architecture to manage and delegate tasks to specialized sub-agents.

**Location**: `backend/orchestrator_agent.py`

**Responsibilities**:
- Receive user requests from the API
- Analyze requests and determine which sub-agents to involve
- Delegate tasks to appropriate sub-agents
- Synthesize responses from multiple agents
- Provide a unified response to the user

**Configuration**:
- **Model**: OpenAI GPT-4o
- **Mode**: Coordinate (default) - delegates and synthesizes
- **Members**: Conversation Agent (and future agents)

**Key Instructions**:
- Friendly and supportive team leader
- Delegates to Conversation Agent when topics are chosen
- Focuses on "basic preferences" dimension
- Synthesizes member responses

### Conversation Agent

The **Conversation Agent** is a specialized sub-agent responsible for generating conversation questions based on selected topics.

**Location**: `backend/subagents/conversation_agent.py`

**Responsibilities**:
- Generate contextually appropriate questions for selected topics
- Focus on "basic preferences" dimension (likes, dislikes, favorites, simple choices)
- Ensure questions are clear, simple, and encouraging
- Adapt to difficulty levels (future enhancement)

**Configuration**:
- **Model**: OpenAI GPT-4o
- **Type**: Single Agent (member of Orchestrator Team)
- **Focus**: Basic preferences dimension

**Key Instructions**:
- Generate questions for autistic youth
- Focus on basic preferences (likes, dislikes, favorites)
- Keep questions clear and simple
- Ask one question at a time
- Make questions natural and conversational

### Agent Communication Flow

```
User Request
    │
    ▼
API Endpoint (/api/start_conversation)
    │
    ▼
Orchestrator Team
    │
    ├─ Analyzes request
    ├─ Determines: "Need question for topic X"
    │
    ▼
Delegates to Conversation Agent
    │
    ├─ Receives topic and context
    ├─ Generates question (basic preferences focus)
    │
    ▼
Returns to Orchestrator Team
    │
    ├─ Synthesizes response
    ├─ Formats output
    │
    ▼
Returns to API
    │
    ▼
Frontend displays question
```

### Future Agents (Planned)

1. **Response Agent**: Generate multiple response options for user selection
2. **Vocabulary Agent**: Identify and explain vocabulary words from conversations
3. **Difficulty Agent**: Adjust conversation complexity based on user level
4. **Progress Agent**: Track user progress and adapt sessions

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

#### POST `/api/start_conversation`
Start a conversation by generating a question for a selected topic.

**Request Body**:
```json
{
  "topic": "gaming",
  "user_id": "user123",
  "difficulty_level": 1
}
```

**Request Schema**:
- `topic` (string, required): The conversation topic (e.g., "gaming", "food", "hobbies")
- `user_id` (string, required): Unique identifier for the user
- `difficulty_level` (integer, optional, default: 1): Conversation difficulty level

**Response**:
```json
{
  "question": "What kind of video games do you enjoy playing the most?",
  "response_options": [
    "I like that topic.",
    "I'm not sure about that.",
    "Can you tell me more?"
  ]
}
```

**Response Schema**:
- `question` (string): Generated conversation question
- `response_options` (array of strings): Pre-generated response options

**Error Responses**:
- `500 Internal Server Error`: Error generating question
  ```json
  {
    "detail": "Error generating question: [error message]"
  }
  ```

### CORS Configuration

The API is configured to accept requests from:
- `http://localhost:3000`
- `http://127.0.0.1:3000`

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
- `responses`: Array of response options
- `vocab`: Vocabulary word object
- `isLoading`: Loading state
- `welcomeMessage`: Welcome message state

**Key Functions**:
- `handleTopicSelect(topicId)`: Handles topic selection and API call

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
```

4. Start the backend server:
```bash
python main.py
```

The server will start on `http://localhost:8000`

### Environment Variables

**Backend** (`backend/.env`):
- `OPENAI_API_KEY`: Your OpenAI API key (required)

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

## Future Enhancements

### Planned Features

1. **Response Agent**
   - Generate multiple response options dynamically
   - Provide varied response styles (simple, detailed, follow-up)

2. **Vocabulary Agent**
   - Identify key vocabulary words from conversations
   - Provide definitions and examples
   - Track learned vocabulary

3. **Difficulty Adjustment**
   - Automatic difficulty adjustment based on user responses
   - Manual difficulty selection
   - Progress tracking

4. **User Authentication**
   - User accounts and profiles
   - Session persistence
   - Progress tracking across sessions

5. **Additional Conversation Dimensions**
   - Beyond "basic preferences"
   - Emotional understanding
   - Social scenarios
   - Problem-solving conversations

6. **Analytics & Reporting**
   - Conversation statistics
   - Progress reports
   - Performance metrics

### Technical Improvements

1. **Database Integration**
   - User data persistence
   - Conversation history
   - Vocabulary tracking

2. **Enhanced Error Handling**
   - Better error messages
   - Retry mechanisms
   - Fallback responses

3. **Performance Optimization**
   - Response caching
   - Async processing improvements
   - Load balancing for multiple users

4. **Testing**
   - Unit tests for agents
   - Integration tests for API
   - E2E tests for frontend

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

**Last Updated**: 2025-02-16
**Version**: 1.0.0
