"""
Database Connection Management for Dinero AI.
Provides connection pooling, session management, and transaction support.
"""
import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

from config.settings import (
    DATABASE_URL,
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW,
    DB_POOL_TIMEOUT,
    DB_ECHO,
    USE_DATABASE
)

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Singleton database connection manager.
    Handles connection pooling and session lifecycle.
    """
    
    _engine: Optional[Engine] = None
    _session_factory: Optional[sessionmaker] = None
    
    @classmethod
    def initialize(cls, url: Optional[str] = None) -> None:
        """
        Initialize database connection.
        
        Args:
            url: Database URL (uses config if not provided)
            
        Raises:
            ValueError: If database URL is not configured
            Exception: If database connection fails
        """
        if not USE_DATABASE:
            logger.info("Database mode disabled. Using JSON storage.")
            return
        
        if cls._engine is not None:
            logger.warning("Database already initialized")
            return
        
        connection_url = url or DATABASE_URL
        
        if not connection_url:
            raise ValueError(
                "DATABASE_URL not configured. Please set DATABASE_URL in your .env file. "
                "Example: DATABASE_URL=postgresql://user:pass@localhost:5432/dinero_ai"
            )
        
        try:
            # Create engine with connection pooling
            cls._engine = create_engine(
                connection_url,
                poolclass=pool.QueuePool,
                pool_size=DB_POOL_SIZE,
                max_overflow=DB_MAX_OVERFLOW,
                pool_timeout=DB_POOL_TIMEOUT,
                pool_pre_ping=True,  # Test connections before using
                echo=DB_ECHO,
                future=True  # Use SQLAlchemy 2.0 style
            )
            
            # Add event listeners
            cls._setup_event_listeners()
            
            # Create session factory
            cls._session_factory = sessionmaker(
                bind=cls._engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
            
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    @classmethod
    def _setup_event_listeners(cls):
        """Setup SQLAlchemy event listeners for monitoring"""
        
        @event.listens_for(cls._engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Execute on new connection"""
            logger.debug("New database connection established")
        
        @event.listens_for(cls._engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Execute when connection checked out from pool"""
            logger.debug("Connection checked out from pool")
        
        @event.listens_for(cls._engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Execute when connection returned to pool"""
            logger.debug("Connection returned to pool")
    
    @classmethod
    def get_engine(cls) -> Engine:
        """
        Get database engine.
        
        Returns:
            SQLAlchemy Engine instance
            
        Raises:
            RuntimeError: If engine is not initialized
        """
        if cls._engine is None:
            cls.initialize()
        return cls._engine
    
    @classmethod
    def get_session(cls) -> Session:
        """
        Get a new database session.
        
        Returns:
            SQLAlchemy Session instance
        """
        if cls._session_factory is None:
            cls.initialize()
        
        return cls._session_factory()
    
    @classmethod
    @contextmanager
    def session_scope(cls) -> Generator[Session, None, None]:
        """
        Context manager for database sessions with automatic commit/rollback.
        
        Usage:
            with DatabaseConnection.session_scope() as session:
                session.add(obj)
                # Automatically commits on success, rolls back on error
        
        Yields:
            Database session
        """
        session = cls.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction failed: {str(e)}")
            raise
        finally:
            session.close()
    
    @classmethod
    def dispose(cls):
        """
        Dispose of all connections in the pool.
        Should be called on application shutdown.
        """
        if cls._engine:
            cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None
            logger.info("Database connections disposed")
    
    @classmethod
    def health_check(cls) -> bool:
        """
        Check database connectivity.
        
        Returns:
            True if database is accessible
        """
        if not USE_DATABASE:
            return True
        
        try:
            with cls.session_scope() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def init_db(url: Optional[str] = None):
    """Initialize database connection"""
    DatabaseConnection.initialize(url)


def get_db_session() -> Session:
    """Get a new database session"""
    return DatabaseConnection.get_session()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Usage:
        from database.connection import db_session
        
        with db_session() as session:
            business = session.query(Business).first()
    """
    with DatabaseConnection.session_scope() as session:
        yield session


def dispose_db():
    """Dispose database connections"""
    DatabaseConnection.dispose()


def db_health_check() -> bool:
    """Check database health"""
    return DatabaseConnection.health_check()


# ============================================================================
# SESSION DEPENDENCY (for dependency injection)
# ============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI/Flask.
    
    Usage:
        def my_view(db: Session = Depends(get_db)):
            # Use db session
    """
    session = get_db_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
