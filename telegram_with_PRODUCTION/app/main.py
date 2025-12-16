"""
TechyEra Marketing - Production SaaS Application
Main FastAPI Application
"""
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Depends, HTTPException, status, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings, PLANS
from app.database import get_db, init_db, close_db
from app.models import User, TelegramAccount, TargetGroup, MarketingMessage, UserSettings
from app.auth import (
    get_current_user, get_current_user_optional, create_user, authenticate_user,
    create_access_token, UserCreate, UserLogin, TokenResponse, UserResponse
)
from app.stripe_service import StripeService, process_subscription_event


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


# Create FastAPI app
app = FastAPI(
    title="TechyEra Marketing",
    description="Professional Telegram Marketing Automation SaaS",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# ==================== PUBLIC PAGES ====================

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request, user: Optional[User] = Depends(get_current_user_optional)):
    """Landing page"""
    return templates.TemplateResponse("landing.html", {
        "request": request,
        "user": user,
        "plans": PLANS
    })


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user: Optional[User] = Depends(get_current_user_optional)):
    """Login page"""
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("auth/login.html", {"request": request})


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request, user: Optional[User] = Depends(get_current_user_optional)):
    """Signup page"""
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("auth/signup.html", {"request": request})


@app.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request, user: Optional[User] = Depends(get_current_user_optional)):
    """Pricing page"""
    return templates.TemplateResponse("pricing.html", {
        "request": request,
        "user": user,
        "plans": PLANS
    })


# ==================== AUTH ROUTES ====================

@app.post("/api/auth/signup", response_model=TokenResponse)
async def signup(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register new user"""
    user = await create_user(db, user_data)
    token = create_access_token(str(user.id))
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            plan=user.plan.value,
            is_verified=user.is_verified,
            created_at=user.created_at
        )
    )


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(user_data: UserLogin, response: Response, db: AsyncSession = Depends(get_db)):
    """Login user"""
    user = await authenticate_user(db, user_data.email, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    token = create_access_token(str(user.id))
    
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=86400,  # 24 hours
        samesite="lax"
    )
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            plan=user.plan.value,
            is_verified=user.is_verified,
            created_at=user.created_at
        )
    )


@app.post("/api/auth/logout")
async def logout(response: Response):
    """Logout user"""
    response.delete_cookie("access_token")
    return {"success": True, "message": "Logged out"}


@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Get current user"""
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        plan=user.plan.value,
        is_verified=user.is_verified,
        created_at=user.created_at
    )


# ==================== DASHBOARD ====================

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: User = Depends(get_current_user)):
    """User dashboard"""
    return templates.TemplateResponse("dashboard/index.html", {
        "request": request,
        "user": user,
        "plan": PLANS.get(user.plan.value, PLANS["free"])
    })


@app.get("/dashboard/groups", response_class=HTMLResponse)
async def dashboard_groups(request: Request, user: User = Depends(get_current_user)):
    """Groups management page"""
    return templates.TemplateResponse("dashboard/groups.html", {
        "request": request,
        "user": user
    })


@app.get("/dashboard/messages", response_class=HTMLResponse)
async def dashboard_messages(request: Request, user: User = Depends(get_current_user)):
    """Messages management page"""
    return templates.TemplateResponse("dashboard/messages.html", {
        "request": request,
        "user": user
    })


@app.get("/dashboard/settings", response_class=HTMLResponse)
async def dashboard_settings(request: Request, user: User = Depends(get_current_user)):
    """Settings page"""
    return templates.TemplateResponse("dashboard/settings.html", {
        "request": request,
        "user": user
    })


@app.get("/dashboard/billing", response_class=HTMLResponse)
async def dashboard_billing(request: Request, user: User = Depends(get_current_user)):
    """Billing page"""
    return templates.TemplateResponse("dashboard/billing.html", {
        "request": request,
        "user": user,
        "plans": PLANS
    })


# ==================== API: DASHBOARD DATA ====================

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics"""
    plan_config = PLANS.get(user.plan.value, PLANS["free"])
    
    # Count telegram accounts
    result = await db.execute(
        select(TelegramAccount).where(TelegramAccount.user_id == user.id)
    )
    telegram_accounts = len(result.scalars().all())
    
    # Count target groups
    result = await db.execute(
        select(TargetGroup).where(TargetGroup.user_id == user.id)
    )
    groups = result.scalars().all()
    total_groups = len(groups)
    enabled_groups = len([g for g in groups if g.enabled])
    
    # Count messages
    result = await db.execute(
        select(MarketingMessage).where(MarketingMessage.user_id == user.id)
    )
    messages = len(result.scalars().all())
    
    return {
        "telegram_accounts": telegram_accounts,
        "max_telegram_accounts": plan_config["max_telegram_accounts"],
        "total_groups": total_groups,
        "enabled_groups": enabled_groups,
        "max_groups": plan_config["max_groups"],
        "messages": messages,
        "messages_sent_today": user.messages_sent_today,
        "max_messages_per_day": plan_config["max_messages_per_day"],
        "plan": user.plan.value,
        "plan_name": plan_config["name"]
    }


# ==================== STRIPE ROUTES ====================

@app.post("/api/billing/create-checkout")
async def create_checkout(
    plan: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create Stripe checkout session"""
    if plan not in ["starter", "pro", "business"]:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    try:
        session = await StripeService.create_checkout_session(
            user=user,
            plan=plan,
            success_url=f"{settings.APP_URL}/dashboard/billing?success=true",
            cancel_url=f"{settings.APP_URL}/dashboard/billing?canceled=true"
        )
        
        # Update customer ID if created
        if not user.stripe_customer_id and session.get("customer"):
            user.stripe_customer_id = session["customer"]
            await db.commit()
        
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/billing/portal")
async def billing_portal(user: User = Depends(get_current_user)):
    """Get Stripe billing portal URL"""
    if not user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No active subscription")
    
    try:
        url = await StripeService.create_billing_portal_session(
            user=user,
            return_url=f"{settings.APP_URL}/dashboard/billing"
        )
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/webhooks/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Stripe webhooks"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = await StripeService.handle_webhook(payload, sig_header)
        await process_subscription_event(db, event["type"], event["data"])
        return {"received": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

