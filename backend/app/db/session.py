from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.exc import OperationalError
import os
from app.core.config import settings
import logging
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

# Create engine with proper configuration for PostgreSQL
logger.info("Creating database engine...")
engine = create_engine(
    settings.DATABASE_URL,
    echo=True,
    poolclass=QueuePool,
    pool_size=5,  # Maximum number of connections to keep
    max_overflow=10,  # Maximum number of connections that can be created beyond pool_size
    pool_timeout=30,  # Seconds to wait before giving up on getting a connection from the pool
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=3600,  # Recycle connections after 1 hour
)
logger.info("Database engine created successfully")

def get_session():
    logger.debug("Creating new database session...")
    session = Session(engine)
    try:
        yield session
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        session.rollback()
        raise
    finally:
        logger.debug("Closing database session...")
        session.close()

def create_db_and_tables():
    try:
        logger.info("Creating database tables...")
        SQLModel.metadata.create_all(engine)
        logger.info("Database and tables created successfully")
    except OperationalError as e:
        logger.error(f"Error creating database and tables: {str(e)}")
        raise