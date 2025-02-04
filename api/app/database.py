# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import get_settings
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)
settings = get_settings()

# Create PostgreSQL engine with connection pooling
try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=5,               # Number of permanent connections
        max_overflow=10,           # Number of connections that can be created beyond pool_size
        pool_timeout=30,           # Seconds to wait before giving up on getting a connection
        pool_recycle=1800,         # Recycle connections after 30 minutes
        pool_pre_ping=True,        # Enable automatic connection testing
        echo=False                 # Set to True to log all SQL queries (development only)
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {str(e)}")
    raise

# Create SessionLocal class with connection pooling
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create declarative base for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Context manager for database sessions (useful for scripts)
@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database health check function
def check_database_connection():
    try:
        with get_db_session() as db:
            # Try to execute a simple query
            db.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False