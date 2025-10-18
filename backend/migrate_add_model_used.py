"""
Migration script to add model_used column to chat_history table
Run this once to update your existing database
"""
from sqlalchemy import create_engine, text
from database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """Add model_used column to chat_history table"""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if we're using SQLite or MySQL/PostgreSQL
            is_sqlite = 'sqlite' in DATABASE_URL.lower()
            
            if is_sqlite:
                # For SQLite, check if column exists using pragma
                try:
                    result = conn.execute(text("PRAGMA table_info(chat_history)"))
                    columns = [row[1] for row in result]
                    if 'model_used' in columns:
                        logger.info("Column 'model_used' already exists in chat_history table")
                        return
                except Exception as e:
                    logger.info(f"Checking column existence: {e}")
            else:
                # For MySQL/PostgreSQL, use information_schema
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='chat_history' AND column_name='model_used'
                """))
                
                if result.fetchone():
                    logger.info("Column 'model_used' already exists in chat_history table")
                    return
            
            # Add the column
            logger.info("Adding 'model_used' column to chat_history table...")
            conn.execute(text("""
                ALTER TABLE chat_history 
                ADD COLUMN model_used VARCHAR(20) DEFAULT 'advanced'
            """))
            conn.commit()
            
            logger.info("Migration completed successfully!")
            logger.info("Column 'model_used' added to chat_history table")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate()
