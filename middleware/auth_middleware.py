"""
Authentication middleware for FastAPI.
Provides dependency injection for authenticated routes.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.jwt_handler import verify_token

# Security scheme for bearer token
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Authorization header with Bearer token
        
    Returns:
        Dictionary with user information
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    is_valid, user_id, error = verify_token(token)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error or "Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "user_id": user_id,
        "token": token
    }


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict]:
    """
    Optional authentication dependency.
    Returns user if authenticated, None if not.
    Useful for endpoints that work both with and without authentication.
    
    Args:
        credentials: Optional HTTP Authorization header
        
    Returns:
        Dictionary with user info if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    is_valid, user_id, error = verify_token(token)
    
    if not is_valid:
        return None
    
    return {
        "user_id": user_id,
        "token": token
    }


if __name__ == "__main__":
    print("Authentication middleware loaded successfully")
    print("Use as dependency in FastAPI routes:")
    print("  @app.get('/protected')")
    print("  async def protected_route(current_user: dict = Depends(get_current_user)):")
    print("      user_id = current_user['user_id']")
