import os
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, JobQueue
from database import init_database
from bot_handlers_v13 import (
    start_command, set_timezone_command, set_workday_command,
    handle_rest_button, handle_summary_button, handle_help_button, handle_task_message,
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
    
    # Create updater
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Add command handlers
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("set_timezone", set_timezone_command))
    dispatcher.add_handler(CommandHandler("set_workday", set_workday_command))
    
    # Add button handlers
    dispatcher.add_handler(MessageHandler(Filters.regex("^Отдых$"), handle_rest_button))
    dispatcher.add_handler(MessageHandler(Filters.regex("^Сводка$"), handle_summary_button))
    dispatcher.add_handler(MessageHandler(Filters.regex("^Помощь$"), handle_help_button))
    
    # Add task message handler (for all other text messages)
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_task_message))
    
    # Add background job for auto-ending tasks  
    # job_queue = updater.job_queue
    # job_queue.run_repeating(auto_end_tasks_job, interval=300, first=60, context=None)  # Check every 5 minutes
    
    logger.info("Bot is starting...")
    
    # Start the bot
    updater.start_polling(drop_pending_updates=True)
    updater.idle()

if __name__ == "__main__":
    main()
