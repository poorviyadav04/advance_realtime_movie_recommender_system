"""
Password hashing and verification utilities using bcrypt.
"""
import bcrypt
import re

# Removed passlib context due to compatibility issues with bcrypt 4.0+


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password (as string)
    """
    # bcrypt.hashpw requires bytes, returns bytes
    # Generate salt and hash
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    
    # Return as string for storage
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        # bcrypt.checkpw requires bytes
        pwd_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    
    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    
    return True, ""


if __name__ == "__main__":
    # Test password utilities
    test_password = "SecurePass123"
    
    # Hash password
    hashed = hash_password(test_password)
    print(f"Hashed password: {hashed}")
    
    # Verify correct password
    is_valid = verify_password(test_password, hashed)
    print(f"Correct password verification: {is_valid}")
    
    # Verify incorrect password
    is_valid = verify_password("WrongPassword", hashed)
    print(f"Incorrect password verification: {is_valid}")
    
    # Test password strength
    valid, msg = validate_password_strength("weak")
    print(f"Weak password: valid={valid}, message={msg}")
    
    valid, msg = validate_password_strength("StrongPass123")
    print(f"Strong password: valid={valid}, message={msg}")
