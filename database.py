import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/telegram_bot")

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = None
    try:
        conn = get_db_connection()
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def init_database():
    """Initialize database tables"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                timezone VARCHAR(50) DEFAULT 'Europe/Moscow',
                workday_start TIME DEFAULT '09:00',
                workday_end TIME DEFAULT '18:00',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                task_name VARCHAR(500) NOT NULL,
                comment TEXT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                is_rest BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # Index for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_user_date 
            ON tasks(user_id, DATE(start_time))
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_active 
            ON tasks(user_id, end_time) 
            WHERE end_time IS NULL
        """)
        
        logger.info("Database initialized successfully")
