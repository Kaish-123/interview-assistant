"""
Interview Assistant Web - FastAPI Backend
A modern web-based interview assistant with real-time transcription and AI-powered responses.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routes
from routes.chat import router as chat_router
from routes.audio import router as audio_router
from routes.documents import router as documents_router
from routes.prompts import router as prompts_router
from routes.hotkeys import router as hotkeys_router

# Import database
from database.db import init_db, SessionLocal, PromptTemplate


def seed_default_prompts():
    """Seed database with default prompt templates"""
    db = SessionLocal()
    
    # Check if prompts already exist
    existing = db.query(PromptTemplate).count()
    if existing > 0:
        db.close()
        return
    
    # Default prompts from the original application
    default_prompts = [
        # Amazon Tab
        ("Amazon", "JD Resume Behavioural coding", """I am in an interview answer me everything as per this resume consider yourself as resume candidate and give me all relevant answer as per this resume and given Job description. For next 3 hours.

If there is any behavioural questions then answer in STAR pattern relevant to resume for next 3 hours.

Explain me problem statement, Ask some questions from interviewer about question 
Then Tell me code in python with space and time complexity and explain me APPROACH to solve the problem, add proper comment on each syntax
And handle and explain edge cases as well

for next 3 hours.."""),
        ("Amazon", "Python Coding", """Explain me problem statement, Ask some questions from interviewer about question 
Then Tell me code in python with space and time complexity and explain me APPROACH to solve the problem, add proper comment on each syntax
And handle and explain edge cases as well for next 3 hours"""),
        ("Amazon", "System Design", """Answer this system design question create it using keyboard characters and ask the clarifying questions on system design and explain each component which u have created with its functionality for next 3 hours"""),
        ("Amazon", "Behavioural", """I am in interview answer me as per my attached resume in previous chats to answer all behavioural question in STAR pattern based on my resume by explaining the clear context of situation along with project and company name for next 3 hours"""),
        ("Amazon", "Intro", "Give me intro for this interview as per this JD and attached resume"),
        ("Amazon", "Recent Project", "Explain me about the recent project, requirement and its business goal as per this resume properly I am in interview"),
        ("Amazon", "Dry run", "Do the dry run of above code with given example step by step as per the code going through line by line give explanation and output dry run"),
        ("Amazon", "SQL Query", "write Sql query and explain me properly line by line"),
        ("Amazon", "Complexity", "Tell me the time and space complexity of above code with explanation"),
        
        # Assessment Tab
        ("Assessment", "Quick", "I am in an assessment, answer me everything directly quickly for next 3 hours"),
        ("Assessment", "Python coding", "Give me the python code for this, to pass all possible edge cases and to pass all test cases, for next 3 hours"),
        
        # General Tab
        ("General", "Answer above", "Answer above"),
        ("General", "Ask questions", "Ask any questions to the interviewer as per the JD and resume as interview is finished now"),
        ("General", "About company", "Tell me the overview about the interviewing company."),
        
        # Coding Languages Tab
        ("Coding", "Java coding", """Explain me problem statement, Ask some questions from interviewer about question 
Then Tell me code in java with space and time complexity and explain me APPROACH to solve the problem, add proper comment on each syntax
And handle and explain edge cases as well for next 3 hours.."""),
        ("Coding", "JavaScript Coding", """Explain me problem statement, Ask some questions from interviewer about question 
Then Tell me code in JavaScript with space and time complexity and explain me APPROACH to solve the problem, add proper comment on each syntax
And handle and explain edge cases as well for next 3 hours"""),
        ("Coding", "C++ coding", """Explain me problem statement, Ask some questions from interviewer about question 
Then Tell me code in C++ with space and time complexity and explain me APPROACH to solve the problem, add proper comment on each syntax
And handle and explain edge cases as well for next 3 hours.."""),
        ("Coding", "Scala Coding", """Explain me problem statement, Ask some questions from interviewer about question 
Then Tell me code in Scala with space and time complexity and explain me APPROACH to solve the problem, add proper comment on each syntax
And handle and explain edge cases as well for next 3 hours"""),
    ]
    
    for i, (tab, subtab, prompt) in enumerate(default_prompts):
        template = PromptTemplate(
            tab_name=tab,
            subtab_name=subtab,
            prompt_text=prompt,
            order_index=i
        )
        db.add(template)
    
    db.commit()
    db.close()
    print("✅ Default prompts seeded successfully")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting Interview Assistant Web Backend...")
    init_db()
    seed_default_prompts()
    print("✅ Database initialized")
    
    # Start global hotkey listener
    try:
        from services.global_hotkeys import init_global_hotkeys
        init_global_hotkeys()
        print("✅ Global hotkeys initialized")
    except Exception as e:
        print(f"⚠️ Global hotkeys not available: {e}")
    
    yield
    
    # Shutdown
    try:
        from services.global_hotkeys import stop_hotkey_listener
        stop_hotkey_listener()
    except:
        pass
    print("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Interview Assistant Web API",
    description="AI-powered interview assistant with real-time transcription and streaming responses",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(audio_router)
app.include_router(documents_router)
app.include_router(prompts_router)
app.include_router(hotkeys_router)


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "name": "Interview Assistant Web API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/api/status")
async def api_status():
    """Check API and OpenAI connection status"""
    from openai import AsyncOpenAI
    
    status = {
        "api": "running",
        "database": "connected",
        "openai": "unknown"
    }
    
    # Check OpenAI connection
    try:
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        await client.models.list()
        status["openai"] = "connected"
    except Exception as e:
        status["openai"] = f"error: {str(e)}"
    
    return status


@app.get("/api/models")
def get_available_models():
    """Get available AI models"""
    return {
        "models": {
            "gpt-4o": {
                "name": "GPT-4o",
                "description": "Best quality, multimodal",
                "speed": "medium",
                "cost": "high"
            },
            "gpt-4o-mini": {
                "name": "GPT-4o Mini",
                "description": "Fast, efficient, cheaper",
                "speed": "fast",
                "cost": "low"
            },
            "gpt-4-turbo": {
                "name": "GPT-4 Turbo",
                "description": "Balanced performance",
                "speed": "medium",
                "cost": "medium"
            }
        },
        "default": "gpt-4o"
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🚀 Starting server on {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        ws_ping_interval=20,
        ws_ping_timeout=20
    )



