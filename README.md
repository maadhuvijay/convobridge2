# ConvoBridge

**ConvoBridge** is a conversation practice platform designed to help autistic youth build confidence in social interactions through structured, AI-powered conversation sessions.

## 🎯 Overview

ConvoBridge uses a multi-agent AI system to generate contextually appropriate conversation questions based on selected topics. The platform focuses on the "basic preferences" dimension, helping users practice expressing likes, dislikes, favorites, and simple choices in a safe, structured environment.

## ✨ Features

- **Topic-Based Conversations**: Select from predefined topics (Gaming, Food, Hobbies, Weekend Plans, YouTube)
- **AI-Generated Questions**: Dynamic question generation using OpenAI GPT-4o
- **Multi-Agent Architecture**: Coordinated team of specialized AI agents
- **Structured Responses**: Pre-generated response options to guide users
- **Modern UI**: Cyberpunk-themed interface with smooth animations
- **Vocabulary Learning**: Integrated vocabulary feature (in development)

## 🏗️ Architecture

ConvoBridge uses a **multi-agent system** built with Agno Teams:

- **Orchestrator Team**: Coordinates and delegates tasks to specialized sub-agents
- **Conversation Agent**: Generates questions focused on basic preferences
- **Future Agents**: Response Agent, Vocabulary Agent (planned)

For detailed architecture documentation, see [ARCHITECTURE.md](./ARCHITECTURE.md).

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.8+
- OpenAI API Key

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

3. Create `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

4. Start the backend server:
```bash
python main.py
```

The backend will run on `http://localhost:8000`

## 📁 Project Structure

```
convobridge2/
├── app/                    # Next.js frontend
│   ├── chat/              # Chat interface
│   └── components/        # Shared components
├── backend/               # Python backend
│   ├── main.py           # FastAPI application
│   ├── orchestrator_agent.py  # Orchestrator team
│   └── subagents/        # Sub-agent modules
└── ARCHITECTURE.md       # Detailed architecture docs
```

## 🛠️ Technology Stack

**Frontend:**
- Next.js 16.1.6 (App Router)
- TypeScript 5
- Tailwind CSS 4
- React 19.2.3

**Backend:**
- FastAPI
- Agno 2.5.2 (AI framework)
- OpenAI GPT-4o
- Uvicorn

## 📚 Documentation

- **[ARCHITECTURE.md](./ARCHITECTURE.md)**: Comprehensive technical documentation
  - System architecture
  - Agent system design
  - API documentation
  - Development workflow

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

## 🔮 Future Enhancements

- Response Agent for dynamic response generation
- Vocabulary Agent for word learning
- User authentication and progress tracking
- Additional conversation dimensions
- Difficulty adjustment system

## 📝 License

[Add license information here]

## 🤝 Contributing

See [ARCHITECTURE.md](./ARCHITECTURE.md) for development guidelines and architecture details.

---

**Built with ❤️ for helping autistic youth build conversation confidence**
