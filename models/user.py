"""
User database models for authentication.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

Base = declarative_base()


class User(Base):
    """
    User model for authenticated users.
    
    User IDs start at 1,000,000 to avoid conflicts with MovieLens demo users (1-610).
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    preferences = Column(JSON, default=dict)  # Store genre preferences, settings, etc.
    
    def to_dict(self):
        """Convert user to dictionary (excluding password)."""
        return {
            "user_id": self.id,
            "email": self.email,
            "display_name": self.display_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active,
            "preferences": self.preferences or {}
        }


class UserSession(Base):
    """
    User session model for tracking active sessions.
    """
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False)  # Hashed JWT token
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)
    device_info = Column(Text)  # Optional: store user agent, IP, etc.
    
    def is_expired(self):
        """Check if session is expired."""
        return datetime.now(timezone.utc) > self.expires_at


# Function to create tables
def create_auth_tables(engine):
    """Create authentication tables."""
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    # Test user model
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Create in-memory database for testing
    engine = create_engine("sqlite:///:memory:", echo=True)
    create_auth_tables(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create a test user
    test_user = User(
        email="test@example.com",
        password_hash="$2b$12$dummy_hash",
        display_name="Test User",
        preferences={"favorite_genres": ["Action", "Sci-Fi"]}
    )
    
    session.add(test_user)
    session.commit()
    
    # Query the user
    user = session.query(User).filter_by(email="test@example.com").first()
    print(f"\nCreated user: {user.to_dict()}")
    
    session.close()
