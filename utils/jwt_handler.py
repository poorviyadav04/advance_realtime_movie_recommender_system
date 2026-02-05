"""
JWT token generation and validation utilities.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
import jwt
from pathlib import Path
import os

# Load SECRET_KEY from environment or use default for development
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-please-make-it-secure-and-random")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload data to encode (should include user_id)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict]:
    """
    Decode and validate a JWT access token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Decoded payload if valid, None if invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Token has expired
        return None
    except jwt.JWTError:
        # Invalid token
        return None


def verify_token(token: str) -> tuple[bool, Optional[int], Optional[str]]:
    """
    Verify a JWT token and extract user_id.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Tuple of (is_valid, user_id, error_message)
    """
    payload = decode_access_token(token)
    
    if payload is None:
        return False, None, "Invalid or expired token"
    
    user_id = payload.get("user_id")
    if user_id is None:
        return False, None, "Token missing user_id"
    
    return True, user_id, None


def generate_secret_key() -> str:
    """
    Generate a secure random secret key for JWT signing.
    
    Returns:
        Random hex string suitable for SECRET_KEY
    """
    import secrets
    return secrets.token_hex(32)


if __name__ == "__main__":
    # Test JWT utilities
    print("Testing JWT utilities...")
    
    # Generate a secret key
    secret = generate_secret_key()
    print(f"\nGenerated SECRET_KEY: {secret}")
    print("(Add this to your .env file as SECRET_KEY=...)")
    
    # Create a token
    test_data = {"user_id": 1000001, "email": "test@example.com"}
    token = create_access_token(test_data)
    print(f"\nGenerated token: {token[:50]}...")
    
    # Decode the token
    decoded = decode_access_token(token)
    print(f"Decoded payload: {decoded}")
    
    # Verify the token
    is_valid, user_id, error = verify_token(token)
    print(f"\nToken verification: valid={is_valid}, user_id={user_id}, error={error}")
    
    # Test expired token (custom short expiration)
    short_token = create_access_token(test_data, expires_delta=timedelta(seconds=-1))
    is_valid, user_id, error = verify_token(short_token)
    print(f"Expired token verification: valid={is_valid}, error={error}")
