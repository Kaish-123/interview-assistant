# Interview Assistant Web

A modern, web-based interview assistant with real-time audio transcription and AI-powered responses. Built with FastAPI backend and Next.js frontend.

## Features

### Core Features
- 🎤 **Real-time Audio Recording** - Record and transcribe interview questions using your microphone
- 🤖 **AI-Powered Responses** - Get intelligent answers using GPT-4o, GPT-4o-mini, or GPT-4-turbo
- 📝 **Streaming Responses** - See answers appear in real-time as they're generated
- 📸 **Image Support** - Paste screenshots or upload images for visual context
- 📄 **Document Upload** - Upload resumes and job descriptions for context

### Interview Tools
- 🚀 **Quick Setup** - Apply multiple prompts in one click with saved profiles
- 📋 **Prompt Templates** - Organized prompts for coding, behavioral, system design questions
- 🔖 **Bookmarks** - Save important Q&A pairs for quick reference
- 📊 **Performance Diagnostics** - Monitor token usage and optimize for speed

### Customization
- 🎯 **Answer Modes** - Default, Quick, Detailed, or Code-focused responses
- ⚡ **Fast Mode** - Optimize context for faster responses
- 🔤 **Font Size Control** - Adjust text size for comfortable reading
- 🌙 **Dark Theme** - Easy on the eyes during long interviews

## Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **WebSocket** - Real-time bidirectional communication
- **OpenAI API** - GPT-4 and Whisper integration
- **SQLite** - Lightweight database for persistence
- **SQLAlchemy** - ORM for database operations

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Zustand** - Lightweight state management
- **Web Audio API** - Browser-based audio recording

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API Key

### 1. Clone and Setup

```bash
cd interview_assistant_web
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
echo "SECRET_KEY=your_secret_key_here" >> .env
echo "DATABASE_URL=sqlite:///./interview_assistant.db" >> .env
echo "CORS_ORIGINS=http://localhost:3000" >> .env

# Run the server
python main.py
```

The backend will start at `http://localhost:8000`

### 3. Frontend Setup

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

The frontend will start at `http://localhost:3000`

### 4. Open in Browser

Navigate to `http://localhost:3000` in your browser (Chrome recommended for best audio support).

## Project Structure

```
interview_assistant_web/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── requirements.txt        # Python dependencies
│   ├── database/
│   │   ├── __init__.py
│   │   └── db.py              # Database models and setup
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Pydantic schemas
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py            # Chat endpoints and WebSocket
│   │   ├── audio.py           # Audio transcription
│   │   ├── documents.py       # Document upload/management
│   │   └── prompts.py         # Prompt template management
│   └── services/
│       ├── __init__.py
│       ├── openai_service.py  # OpenAI API integration
│       ├── chat_service.py    # Chat management logic
│       └── audio_service.py   # Audio processing
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Main page component
│   │   └── globals.css        # Global styles
│   ├── components/
│   │   ├── Sidebar.tsx        # Session & prompt sidebar
│   │   ├── ChatMessage.tsx    # Message display component
│   │   ├── ChatInput.tsx      # Input with audio recording
│   │   ├── ControlBar.tsx     # Settings toolbar
│   │   ├── QuickSetupModal.tsx
│   │   ├── DiagnosticsModal.tsx
│   │   └── BookmarksModal.tsx
│   ├── hooks/
│   │   ├── useStore.ts        # Zustand state management
│   │   ├── useAudioRecorder.ts
│   │   └── useChatWebSocket.ts
│   ├── lib/
│   │   ├── api.ts             # API client functions
│   │   └── utils.ts           # Utility functions
│   ├── types/
│   │   └── index.ts           # TypeScript definitions
│   ├── package.json
│   ├── tailwind.config.ts
│   └── next.config.js
│
└── README.md
```

## Usage Guide

### Starting a New Chat
1. Click "New Chat" or use the sidebar
2. Upload your resume/JD for context (optional)
3. Start asking questions or use prompts

### Recording Audio
1. Click the microphone button to start recording
2. Speak your question
3. Click again to stop and transcribe
4. The transcription appears in the input field
5. Press Enter to send

### Using Prompts
1. Open the Prompts tab in the sidebar
2. Click any prompt to send it immediately
3. Or use Quick Setup (🚀) to combine multiple prompts

### Keyboard Shortcuts
- `Enter` - Send message
- `Shift+Enter` - New line
- `Cmd/Ctrl+V` - Paste image

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Environment Variables

### Backend (.env)
```env
OPENAI_API_KEY=sk-...       # Required: Your OpenAI API key
SECRET_KEY=...              # Optional: For session security
DATABASE_URL=sqlite:///...  # Optional: Database connection
CORS_ORIGINS=http://...     # Optional: Allowed origins
```

## Troubleshooting

### Audio Recording Not Working
- Ensure you've granted microphone permission
- Use Chrome/Edge for best compatibility
- Check that no other app is using the microphone

### WebSocket Connection Issues
- Check that the backend is running on port 8000
- Verify CORS settings if using different ports
- Check browser console for error messages

### API Errors
- Verify your OpenAI API key is valid
- Check you have sufficient API credits
- Look at backend console for detailed errors

## Contributing

Feel free to submit issues and pull requests!

## License

MIT License - feel free to use this for your interview prep!
