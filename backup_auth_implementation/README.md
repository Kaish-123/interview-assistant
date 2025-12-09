# Interview Assistant Web

A modern, web-based interview assistant with real-time audio transcription, AI-powered responses, user authentication, and subscription management. Built with FastAPI backend and Next.js frontend.

**🌐 Coming soon to [techyera.co](https://techyera.co)**

## Features

### Core Features
- 🎤 **Real-time Audio Recording** - Record and transcribe interview questions using your microphone or BlackHole for internal audio
- 🤖 **AI-Powered Responses** - Get intelligent answers using GPT-4o, GPT-4o-mini, or GPT-4-turbo
- 📝 **Streaming Responses** - See answers appear in real-time as they're generated
- 📸 **Image Support** - Paste screenshots or upload images for visual context
- 📄 **Document Upload** - Upload resumes and job descriptions for context

### Interview Tools
- 🚀 **Quick Setup** - Apply multiple prompts in one click with saved profiles
- 📋 **Prompt Templates** - Organized prompts for coding, behavioral, system design questions
- 🔖 **Bookmarks** - Save important Q&A pairs for quick reference
- 📊 **Performance Diagnostics** - Monitor token usage and optimize for speed

### Authentication & Users
- 🔐 **User Authentication** - Sign up with email/password or Google OAuth
- 👤 **User Profiles** - Personal chat history and preferences
- 💳 **Subscription Plans** - Free, Starter, Pro, and Enterprise tiers
- 🔄 **Session Management** - Secure JWT-based authentication

### Customization
- 🎯 **Answer Modes** - Default, Quick, Detailed, or Code-focused responses
- ⚡ **Fast Mode** - Optimize context for faster responses
- 🔤 **Font Size Control** - Adjust text size for comfortable reading
- 🌙 **Dark Theme** - Easy on the eyes during long interviews
- ⌨️ **Global Hotkeys** - Control recording and navigation without focus

## Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **WebSocket** - Real-time bidirectional communication
- **OpenAI API** - GPT-4 and Whisper integration
- **SQLite/PostgreSQL** - Database for persistence
- **SQLAlchemy** - ORM for database operations
- **JWT** - Secure authentication tokens
- **Passlib** - Password hashing with bcrypt
- **HTTPX** - OAuth2 client requests

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Zustand** - Lightweight state management
- **Web Audio API** - Browser-based audio recording
- **Context API** - Authentication state management

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API Key
- (Optional) Google OAuth Credentials

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

# Create .env file with your configuration
cat > .env << EOF
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Security (auto-generated if not set)
SECRET_KEY=$(openssl rand -hex 32)

# Database (defaults to SQLite)
DATABASE_URL=sqlite:///./interview_assistant.db

# Google OAuth (optional - for Google Sign-In)
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback

# CORS (for production)
# CORS_ORIGINS=https://techyera.co
EOF

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

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run the development server
npm run dev
```

The frontend will start at `http://localhost:3000`

### 4. Open in Browser

Navigate to `http://localhost:3000` in your browser (Chrome recommended for best audio support).

## Setting Up Google OAuth (Optional)

To enable "Sign in with Google":

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the Google+ API
4. Go to Credentials > Create Credentials > OAuth Client ID
5. Select "Web application"
6. Add authorized redirect URI: `http://localhost:3000/auth/google/callback`
7. Copy the Client ID and Client Secret to your `.env` file

## Subscription Plans

| Plan | Price | Features |
|------|-------|----------|
| **Free** | $0 | 20 messages/day, 5 sessions, GPT-4o Mini |
| **Starter** | $9.99/mo | 100 messages/day, 50 sessions, GPT-4o |
| **Pro** | $29.99/mo | Unlimited, all models, priority support |
| **Enterprise** | $99.99/mo | Team features, API access, custom AI |

## Project Structure

```
interview_assistant_web/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── requirements.txt        # Python dependencies
│   ├── database/
│   │   └── db.py              # Database models (User, Chat, etc.)
│   ├── routes/
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── chat.py            # Chat endpoints and WebSocket
│   │   ├── audio.py           # Audio transcription
│   │   ├── documents.py       # Document upload
│   │   └── prompts.py         # Prompt templates
│   └── services/
│       ├── auth_service.py    # JWT, OAuth, password handling
│       ├── openai_service.py  # OpenAI API integration
│       └── chat_service.py    # Chat management
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx         # Root layout with AuthProvider
│   │   ├── page.tsx           # Main chat page
│   │   ├── auth/page.tsx      # Login/Signup page
│   │   └── pricing/page.tsx   # Subscription plans
│   ├── components/
│   │   ├── Sidebar.tsx        # Session & prompt sidebar
│   │   ├── ChatInput.tsx      # Input with audio recording
│   │   ├── ControlBar.tsx     # Settings toolbar
│   │   └── UserMenu.tsx       # User dropdown menu
│   ├── contexts/
│   │   └── AuthContext.tsx    # Authentication state
│   ├── hooks/
│   │   ├── useStore.ts        # Zustand state
│   │   └── useAudioRecorder.ts
│   └── lib/
│       └── api.ts             # API client
│
└── README.md
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Authentication Endpoints
- `POST /auth/signup` - Register new user
- `POST /auth/login` - Login with email/password
- `GET /auth/google` - Get Google OAuth URL
- `POST /auth/google/callback` - Handle Google OAuth callback
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout and revoke token
- `GET /auth/me` - Get current user info

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `` ` `` (backtick) | Start/stop recording |
| `4+5` | Record with BlackHole |
| `5+6` | Record with microphone |
| `Ctrl+N` | New chat |
| `PageDown` | Scroll to bottom |
| `PageUp` | Scroll to top |
| `F2` | Save UI layout |
| `+/-` | Adjust font size |

## Environment Variables

### Backend (.env)
```env
# Required
OPENAI_API_KEY=sk-...           # Your OpenAI API key

# Security
SECRET_KEY=...                  # JWT secret (auto-generated if not set)

# Database
DATABASE_URL=sqlite:///...      # SQLite or PostgreSQL connection

# Google OAuth (optional)
GOOGLE_CLIENT_ID=...            # From Google Cloud Console
GOOGLE_CLIENT_SECRET=...        # From Google Cloud Console
GOOGLE_REDIRECT_URI=...         # OAuth callback URL

# Production
CORS_ORIGINS=https://...        # Allowed frontend origins
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Production Deployment

### For techyera.co deployment:

1. **Backend**: Deploy to Railway, Render, or AWS
2. **Frontend**: Deploy to Vercel
3. **Database**: Use PostgreSQL (Supabase, Neon, or managed)
4. **Update environment variables** for production URLs

```env
# Production Backend
DATABASE_URL=postgresql://user:pass@host:5432/db
CORS_ORIGINS=https://techyera.co,https://www.techyera.co
GOOGLE_REDIRECT_URI=https://techyera.co/auth/google/callback

# Production Frontend
NEXT_PUBLIC_API_URL=https://api.techyera.co
```

## Troubleshooting

### Audio Recording Not Working
- Ensure you've granted microphone permission
- Use Chrome/Edge for best compatibility
- For BlackHole: Install and configure as audio input

### Authentication Issues
- Clear localStorage and try again
- Check that SECRET_KEY is consistent
- Verify Google OAuth credentials

### WebSocket Connection Issues
- Check that the backend is running
- Verify CORS settings
- Check browser console for errors

## Contributing

Feel free to submit issues and pull requests!

## License

MIT License - feel free to use this for your interview prep!

---

**Built with ❤️ by TechYera**
