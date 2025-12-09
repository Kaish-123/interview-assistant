"""
Authentication Routes - Login, Signup, OAuth, Token management
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from database.db import get_db, User, SUBSCRIPTION_PLANS
from services.auth_service import AuthService, GoogleOAuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


# ============================================================================
# Pydantic Models
# ============================================================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    picture_url: Optional[str]
    auth_provider: str
    subscription_tier: str
    is_verified: bool
    
    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class GoogleAuthRequest(BaseModel):
    code: str


# ============================================================================
# Dependencies
# ============================================================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current authenticated user from token"""
    if not token:
        return None
    
    user = AuthService.get_user_from_token(db, token)
    return user


async def get_current_user_required(
    user: Optional[User] = Depends(get_current_user)
) -> User:
    """Require authenticated user"""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    return user


# ============================================================================
# Routes
# ============================================================================

@router.post("/signup", response_model=AuthResponse)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if email already exists
    existing_user = AuthService.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )
    
    # Create user
    user = AuthService.create_user(
        db,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        auth_provider="local"
    )
    
    # Create tokens
    tokens = AuthService.create_tokens(user)
    
    # Store refresh token
    AuthService.store_refresh_token(db, user.id, tokens["refresh_token"])
    
    # Update last login
    AuthService.update_last_login(db, user)
    
    return AuthResponse(
        **tokens,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            picture_url=user.picture_url,
            auth_provider=user.auth_provider,
            subscription_tier=user.subscription_tier,
            is_verified=user.is_verified
        )
    )


@router.post("/login", response_model=AuthResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login with email and password"""
    user = AuthService.authenticate_user(db, user_data.email, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Create tokens
    tokens = AuthService.create_tokens(user)
    
    # Store refresh token
    AuthService.store_refresh_token(db, user.id, tokens["refresh_token"])
    
    # Update last login
    AuthService.update_last_login(db, user)
    
    return AuthResponse(
        **tokens,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            picture_url=user.picture_url,
            auth_provider=user.auth_provider,
            subscription_tier=user.subscription_tier,
            is_verified=user.is_verified
        )
    )


@router.post("/login/form", response_model=TokenResponse)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 compatible login endpoint"""
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    tokens = AuthService.create_tokens(user)
    AuthService.store_refresh_token(db, user.id, tokens["refresh_token"])
    AuthService.update_last_login(db, user)
    
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    result = AuthService.refresh_access_token(db, request.refresh_token)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=request.refresh_token,  # Return same refresh token
        token_type=result["token_type"],
        expires_in=result["expires_in"]
    )


@router.post("/logout")
async def logout(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required)
):
    """Logout and revoke refresh token"""
    AuthService.revoke_refresh_token(db, request.refresh_token)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user_required)):
    """Get current user info"""
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        picture_url=user.picture_url,
        auth_provider=user.auth_provider,
        subscription_tier=user.subscription_tier,
        is_verified=user.is_verified
    )


# ============================================================================
# Google OAuth Routes
# ============================================================================

@router.get("/google")
async def google_auth():
    """Get Google OAuth authorization URL"""
    url = GoogleOAuthService.get_authorization_url()
    return {"authorization_url": url}


@router.post("/google/callback", response_model=AuthResponse)
async def google_callback(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    result = await GoogleOAuthService.authenticate_or_create_user(db, request.code)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to authenticate with Google"
        )
    
    return AuthResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"],
        user=UserResponse(**result["user"])
    )


# ============================================================================
# Subscription Routes
# ============================================================================

@router.get("/subscription/plans")
async def get_subscription_plans():
    """Get available subscription plans"""
    return SUBSCRIPTION_PLANS


@router.get("/subscription/current")
async def get_current_subscription(
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Get current user's subscription details"""
    plan = SUBSCRIPTION_PLANS.get(user.subscription_tier, SUBSCRIPTION_PLANS["free"])
    
    return {
        "tier": user.subscription_tier,
        "plan": plan,
        "expires_at": user.subscription_expires_at,
        "api_calls_today": user.api_calls_today,
        "api_calls_month": user.api_calls_month
    }


# ============================================================================
# Password Reset (Placeholder)
# ============================================================================

@router.post("/forgot-password")
async def forgot_password(email: EmailStr, db: Session = Depends(get_db)):
    """Request password reset email"""
    user = AuthService.get_user_by_email(db, email)
    
    # Always return success to prevent email enumeration
    # In production, send email with reset link
    return {"message": "If an account exists with this email, a reset link will be sent"}


@router.post("/reset-password")
async def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    """Reset password with token"""
    # In production, validate reset token and update password
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset not yet implemented"
    )

