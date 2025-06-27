"""
WSGI entry point for production deployment with gunicorn
"""
import os
import threading
import time
import logging
from app import app, run_telegram_bot
from database import init_database

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_app():
    """Initialize the application"""
    logger.info("Initializing database...")
    init_database()
    logger.info("Database initialized successfully")
    
    # Start Telegram bot in a separate thread
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    logger.info("Telegram bot thread started")

# Initialize when module is imported
initialize_app()

# WSGI application
application = app

if __name__ == "__main__":
    # For local development
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)