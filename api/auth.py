"""
Authentication API endpoints for user signup, login, and profile management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta, timezone
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config.database import get_db
from models.user import User, UserSession
from utils.password import hash_password, verify_password, validate_password_strength
from utils.jwt_handler import create_access_token, verify_token
from middleware.auth_middleware import get_current_user
import hashlib

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])


# Pydantic models for request/response
class SignupRequest(BaseModel):
    """User signup request."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Login/signup response with token."""
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    """User profile response."""
    user_id: int
    email: str
    display_name: Optional[str]
    created_at: str
    last_login: Optional[str]
    preferences: dict


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """
    Create a new user account.
    
    Args:
        request: Signup request with email, password, display_name
        db: Database session
        
    Returns:
        Access token and user info
    """
    try:
        # Validate password strength
        is_valid, error_msg = validate_password_strength(request.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = hash_password(request.password)
        
        new_user = User(
            email=request.email,
            password_hash=hashed_password,
            display_name=request.display_name or request.email.split('@')[0],
            created_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc),
            is_active=True,
            preferences={}
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # User IDs start at 1000000 by default, but if lower, adjust
        # This ensures new users don't conflict with MovieLens demo users
        if new_user.id < 1000000:
            # Update the ID to start from 1000000
            old_id = new_user.id
            db.execute(text(f"UPDATE users SET id = id + 1000000 WHERE id = {old_id}"))
            db.commit()
            
            # Re-fetch the user with the new ID
            new_id = old_id + 1000000
            # Expire the old instance to avoid confusion
            db.expire(new_user)
            new_user = db.query(User).filter(User.id == new_id).first()
        
        # Generate JWT token
        access_token = create_access_token(
            data={"user_id": new_user.id, "email": new_user.email}
        )
        
        # Create session record
        token_hash = hashlib.sha256(access_token.encode()).hexdigest()
        session_record = UserSession(
            user_id=new_user.id,
            token_hash=token_hash,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
        )
        db.add(session_record)
        db.commit()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": new_user.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"SIGNUP ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return access token.
    
    Args:
        request: Login request with email and password
        db: Database session
        
    Returns:
        Access token and user info
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    # Generate JWT token
    access_token = create_access_token(
        data={"user_id": user.id, "email": user.email}
    )
    
    # Create session record
    token_hash = hashlib.sha256(access_token.encode()).hexdigest()
    session_record = UserSession(
        user_id=user.id,
        token_hash=token_hash,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
    )
    db.add(session_record)
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.to_dict()
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user's profile.
    
    Args:
        current_user: Current user from JWT token
        db: Database session
        
    Returns:
        User profile information
    """
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user.to_dict()


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout current user by invalidating session.
    
    Args:
        current_user: Current user from JWT token
        db: Database session
        
    Returns:
        Success message
    """
    # Get token hash
    token = current_user["token"]
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Delete session
    db.query(UserSession).filter(
        UserSession.user_id == current_user["user_id"],
        UserSession.token_hash == token_hash
    ).delete()
    db.commit()
    
    return {"message": "Successfully logged out"}


@router.put("/update-profile")
async def update_profile(
    display_name: Optional[str] = None,
    preferences: Optional[dict] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile.
    
    Args:
        display_name: New display name
        preferences: User preferences (genres, etc.)
        current_user: Current user from JWT token
        db: Database session
        
    Returns:
        Updated user info
    """
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    if display_name is not None:
        user.display_name = display_name
    
    if preferences is not None:
        user.preferences = preferences
    
    db.commit()
    db.refresh(user)
    
    return user.to_dict()


if __name__ == "__main__":
    print("Authentication API router defined")
    print("Endpoints:")
    print("  POST /auth/signup - Create new account")
    print("  POST /auth/login - Login")
    print("  GET /auth/me - Get current user")
    print("  POST /auth/logout - Logout")
    print("  PUT /auth/update-profile - Update profile")
