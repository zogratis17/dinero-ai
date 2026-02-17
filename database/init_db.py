"""
Database initialization and migration utilities.
Run this script to setup the database.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import init_db, DatabaseConnection
from database.models import create_all_tables
from config.settings import DATABASE_URL, USE_DATABASE
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database with tables"""
    if not USE_DATABASE:
        logger.warning("Database mode is disabled. Set USE_DATABASE=true to enable.")
        return
    
    if not DATABASE_URL:
        logger.error("DATABASE_URL not configured")
        return
    
    logger.info(f"Initializing database...")
    
    try:
        # Initialize connection
        init_db()
        engine = DatabaseConnection.get_engine()
        
        # Create all tables
        logger.info("Creating tables...")
        create_all_tables(engine)
        
        logger.info("✅ Database initialized successfully!")
        logger.info(f"Connected to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'database'}")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise


def run_raw_sql():
    """Run the raw SQL schema (alternative to SQLAlchemy)"""
    import psycopg2
    from urllib.parse import urlparse
    
    if not DATABASE_URL:
        logger.error("DATABASE_URL not configured")
        return
    
    # Parse database URL
    url = urlparse(DATABASE_URL)
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port or 5432,
            database=url.path[1:],  # Remove leading /
            user=url.username,
            password=url.password
        )
        
        # Read schema file
        schema_file = Path(__file__).parent / "schema.sql"
        with open(schema_file, 'r') as f:
            sql = f.read()
        
        # Execute schema
        logger.info("Running SQL schema...")
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ SQL schema executed successfully!")
        
    except Exception as e:
        logger.error(f"❌ SQL execution failed: {str(e)}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database initialization")
    parser.add_argument(
        "--mode",
        choices=["sqlalchemy", "raw_sql"],
        default="sqlalchemy",
        help="Initialization mode"
    )
    
    args = parser.parse_args()
    
    if args.mode == "sqlalchemy":
        init_database()
    else:
        run_raw_sql()
