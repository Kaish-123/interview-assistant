"""
Authentication Service - JWT, Password hashing, OAuth
"""
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database.db import User, RefreshToken, UserSubscription, SubscriptionTier

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Handle authentication operations"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """Decode and verify a JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_oauth(db: Session, provider: str, oauth_id: str) -> Optional[User]:
        """Get user by OAuth provider and ID"""
        return db.query(User).filter(
            User.auth_provider == provider,
            User.oauth_id == oauth_id
        ).first()
    
    @staticmethod
    def create_user(
        db: Session,
        email: str,
        password: Optional[str] = None,
        full_name: Optional[str] = None,
        auth_provider: str = "local",
        oauth_id: Optional[str] = None,
        picture_url: Optional[str] = None,
        is_verified: bool = False
    ) -> User:
        """Create a new user"""
        hashed_password = AuthService.hash_password(password) if password else None
        
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            auth_provider=auth_provider,
            oauth_id=oauth_id,
            picture_url=picture_url,
            is_verified=is_verified or (auth_provider != "local"),  # OAuth users are auto-verified
            subscription_tier=SubscriptionTier.FREE.value
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = AuthService.get_user_by_email(db, email)
        if not user:
            return None
        if not user.hashed_password:
            return None  # OAuth user, can't login with password
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    def create_tokens(user: User) -> Dict[str, Any]:
        """Create access and refresh tokens for a user"""
        access_token = AuthService.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        refresh_token = AuthService.create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    @staticmethod
    def store_refresh_token(db: Session, user_id: int, token: str) -> RefreshToken:
        """Store a refresh token in the database"""
        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(refresh_token)
        db.commit()
        return refresh_token
    
    @staticmethod
    def revoke_refresh_token(db: Session, token: str) -> bool:
        """Revoke a refresh token"""
        db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
        if db_token:
            db_token.is_revoked = True
            db.commit()
            return True
        return False
    
    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh an access token using a refresh token"""
        payload = AuthService.decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
        
        # Check if token is in database and not revoked
        db_token = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.is_revoked == False
        ).first()
        
        if not db_token or db_token.expires_at < datetime.utcnow():
            return None
        
        user = AuthService.get_user_by_id(db, int(payload["sub"]))
        if not user or not user.is_active:
            return None
        
        # Create new access token
        access_token = AuthService.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    @staticmethod
    def update_last_login(db: Session, user: User):
        """Update user's last login timestamp"""
        user.last_login = datetime.utcnow()
        db.commit()
    
    @staticmethod
    def get_user_from_token(db: Session, token: str) -> Optional[User]:
        """Get user from access token"""
        payload = AuthService.decode_token(token)
        if not payload or payload.get("type") != "access":
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        return AuthService.get_user_by_id(db, int(user_id))


# OAuth Handlers
class GoogleOAuthService:
    """Handle Google OAuth authentication"""
    
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/google/callback")
    
    @staticmethod
    def get_authorization_url() -> str:
        """Get Google OAuth authorization URL"""
        import urllib.parse
        
        params = {
            "client_id": GoogleOAuthService.GOOGLE_CLIENT_ID,
            "redirect_uri": GoogleOAuthService.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    
    @staticmethod
    async def exchange_code_for_tokens(code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for tokens"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": GoogleOAuthService.GOOGLE_CLIENT_ID,
                    "client_secret": GoogleOAuthService.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": GoogleOAuthService.GOOGLE_REDIRECT_URI
                }
            )
            
            if response.status_code != 200:
                return None
            
            return response.json()
    
    @staticmethod
    async def get_user_info(access_token: str) -> Optional[Dict[str, Any]]:
        """Get user info from Google"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                return None
            
            return response.json()
    
    @staticmethod
    async def authenticate_or_create_user(db: Session, code: str) -> Optional[Dict[str, Any]]:
        """Authenticate or create user from Google OAuth code"""
        # Exchange code for tokens
        tokens = await GoogleOAuthService.exchange_code_for_tokens(code)
        if not tokens:
            return None
        
        # Get user info
        user_info = await GoogleOAuthService.get_user_info(tokens.get("access_token", ""))
        if not user_info:
            return None
        
        google_id = user_info.get("id")
        email = user_info.get("email")
        name = user_info.get("name")
        picture = user_info.get("picture")
        
        if not email:
            return None
        
        # Check if user exists
        user = AuthService.get_user_by_oauth(db, "google", google_id)
        
        if not user:
            # Check if email exists with different provider
            existing_user = AuthService.get_user_by_email(db, email)
            if existing_user:
                # Link Google to existing account
                existing_user.oauth_id = google_id
                existing_user.auth_provider = "google"
                existing_user.picture_url = picture
                existing_user.is_verified = True
                db.commit()
                user = existing_user
            else:
                # Create new user
                user = AuthService.create_user(
                    db,
                    email=email,
                    full_name=name,
                    auth_provider="google",
                    oauth_id=google_id,
                    picture_url=picture,
                    is_verified=True
                )
        
        # Update last login
        AuthService.update_last_login(db, user)
        
        # Create tokens
        tokens = AuthService.create_tokens(user)
        
        # Store refresh token
        AuthService.store_refresh_token(db, user.id, tokens["refresh_token"])
        
        return {
            **tokens,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "picture_url": user.picture_url,
                "subscription_tier": user.subscription_tier
            }
        }


auth_service = AuthService()
google_oauth_service = GoogleOAuthService()

