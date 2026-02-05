"""
Database configuration and connection management for Phase 5.
"""
import os
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import redis
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URLs
POSTGRES_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:password@localhost:5432/recommender_db"
)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# For development, we'll use SQLite if PostgreSQL is not available
SQLITE_URL = f"sqlite:///{Path('data/recommender.db').absolute()}"

class DatabaseConfig:
    """Database configuration and connection management."""
    
    def __init__(self):
        self.postgres_engine = None
        self.sqlite_engine = None
        self.redis_client = None
        self.SessionLocal = None
        self.use_postgres = False
        self.use_redis = False
        
        self._setup_databases()
    
    def _setup_databases(self):
        """Setup database connections."""
        
        # Try PostgreSQL first
        try:
            self.postgres_engine = create_engine(POSTGRES_URL)
            # Test connection
            with self.postgres_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.postgres_engine)
            self.use_postgres = True
            print("✅ PostgreSQL connection established")
        except Exception as e:
            print(f"⚠️ PostgreSQL not available: {e}")
            print("📝 Using SQLite for development")
            
            # Fallback to SQLite
            Path("data").mkdir(exist_ok=True)
            db_path = Path('data/recommender.db').absolute()
            print(f"📝 DEBUG: SQLite Path: {db_path}")
            self.sqlite_engine = create_engine(
                SQLITE_URL,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False}
            )
            # Enable WAL mode for better concurrency
            with self.sqlite_engine.connect() as conn:
                conn.execute(text("PRAGMA journal_mode=WAL;"))
                print("📝 DEBUG: Enabled SQLite WAL mode")
            
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.sqlite_engine)
        
        # Try Redis
        try:
            self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            self.use_redis = True
            print("✅ Redis connection established")
        except Exception as e:
            print(f"⚠️ Redis not available: {e}")
            print("📝 Will use in-memory cache for development")
    
    def get_engine(self):
        """Get the active database engine."""
        return self.postgres_engine if self.use_postgres else self.sqlite_engine
    
    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()
    
    def get_redis(self):
        """Get Redis client."""
        return self.redis_client if self.use_redis else None

# Global database instance
db_config = DatabaseConfig()

# SQLAlchemy Base
Base = declarative_base()

def get_db():
    """Dependency to get database session."""
    db = db_config.get_session()
    try:
        yield db
    finally:
        db.close()

def get_redis():
    """Dependency to get Redis client."""
    return db_config.get_redis()

def create_all_tables():
    """Create all database tables including auth tables."""
    from models.user import Base as UserBase
    
    engine = db_config.get_engine()
    
    # Create auth tables
    UserBase.metadata.create_all(engine)
    
    print("✅ Authentication tables created/verified")