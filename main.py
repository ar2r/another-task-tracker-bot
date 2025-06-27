import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.ext import JobQueue
from database import init_database
from bot_handlers import (
    start_command, set_timezone_command, set_workday_command,
    handle_rest_button, handle_summary_button, handle_task_message,
    auto_end_tasks_job
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")

def main():
    """Start the bot"""
    # Initialize database
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("set_timezone", set_timezone_command))
    application.add_handler(CommandHandler("set_workday", set_workday_command))
    
    # Add button handlers
    application.add_handler(MessageHandler(filters.Regex("^Отдых$"), handle_rest_button))
    application.add_handler(MessageHandler(filters.Regex("^Сводка$"), handle_summary_button))
    
    # Add task message handler (for all other text messages)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task_message))
    
    # Add background job for auto-ending tasks
    job_queue = application.job_queue
    job_queue.run_repeating(auto_end_tasks_job, interval=300, first=60)  # Check every 5 minutes
    
    logger.info("Bot is starting...")
    
    # Start the bot
    application.run_polling(
        allowed_updates=["message"],
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
