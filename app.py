import os
import logging
import threading
import time as time_module
from datetime import datetime, time, timedelta

# Import Telegram bot
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Import Flask web server
from flask import Flask, jsonify

# Import bot modules
from database import init_database
from models import User, Task
from task_parser import parse_task_message, format_task_for_display
from time_utils import format_duration, format_time_for_user, create_datetime_from_time, parse_time_from_message
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global status tracking
app_status = {
    'bot_running': False,
    'web_server_running': False,
    'start_time': datetime.now(),
    'last_activity': datetime.now()
}

# Flask app for health checks
app = Flask(__name__)

@app.route('/')
def health_check():
    """Root health check endpoint required for deployment"""
    return jsonify({
        'status': 'healthy',
        'service': 'telegram-time-tracking-bot',
        'timestamp': datetime.now().isoformat(),
        'bot_running': app_status['bot_running'],
        'web_server_running': app_status['web_server_running'],
        'uptime_seconds': (datetime.now() - app_status['start_time']).total_seconds()
    })

@app.route('/health')
def health():
    """Additional health endpoint"""
    return health_check()

@app.route('/status')
def status():
    """Detailed status endpoint"""
    return jsonify({
        'app_status': app_status,
        'environment': {
            'bot_token_configured': bool(os.environ.get('BOT_TOKEN')),
            'database_url_configured': bool(os.environ.get('DATABASE_URL')),
        },
        'timestamp': datetime.now().isoformat()
    })

# Telegram Bot Setup
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable is not set")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

def log_user_request(message, action_type="message"):
    """Log user requests"""
    user = message.from_user
    user_info = f"@{user.username}" if user.username else f"ID:{user.id}"
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    if full_name:
        user_info += f" ({full_name})"
    
    message_text = message.text if hasattr(message, 'text') and message.text else "N/A"
    if len(message_text) > 100:
        message_text = message_text[:100] + "..."
    
    logger.info(f"📨 {action_type.upper()} от {user_info}: '{message_text}'")
    app_status['last_activity'] = datetime.now()

def get_main_keyboard():
    """Get main keyboard with buttons"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(KeyboardButton("🏖️ Отдых"), KeyboardButton("📊 Сводка"))
    keyboard.row(KeyboardButton("❓ Помощь"))
    return keyboard

@bot.message_handler(commands=['start'])
def start_command(message):
    """Handle /start command"""
    log_user_request(message, "command")
    user_id = message.from_user.id
    
    # Create or get user
    user = User.get_or_create(user_id)
    
    welcome_message = f"""
🎯 *Добро пожаловать в Telegram-бот для трекинга времени!*

Я помогу вам эффективно отслеживать время работы над задачами.

*Основные возможности:*
• Автоматический учет времени задач
• Интеграция с Jira (поддержка ссылок и тикетов)
• Настройка часового пояса и рабочего времени
• Автоматическое завершение задач
• Детальная аналитика и отчеты

*Быстрый старт:*
1. Настройте часовой пояс: `/set_timezone Europe/Moscow`
2. Установите рабочие часы: `/set_workday 09:00 18:00`
3. Создайте задачу: просто отправьте название задачи

*Текущие настройки:*
• Часовой пояс: {user.timezone}
• Рабочее время: {user.workday_start.strftime('%H:%M')} - {user.workday_end.strftime('%H:%M')}

Используйте кнопки ниже для быстрого доступа к функциям.
"""
    
    bot.send_message(message.chat.id, welcome_message, parse_mode='Markdown', reply_markup=get_main_keyboard())

@bot.message_handler(commands=['set_timezone'])
def set_timezone_command(message):
    """Handle /set_timezone command"""
    log_user_request(message, "command")
    user_id = message.from_user.id
    
    try:
        # Extract timezone from command
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, 
                           "❌ Неверный формат команды. Используйте: `/set_timezone Europe/Moscow`", 
                           parse_mode='Markdown')
            return
        
        timezone_str = parts[1]
        user = User.get_or_create(user_id)
        
        if user.update_timezone(timezone_str):
            bot.send_message(message.chat.id, 
                           f"✅ Часовой пояс успешно установлен: {timezone_str}")
        else:
            bot.send_message(message.chat.id, 
                           f"❌ Неверный часовой пояс: {timezone_str}\n\n" +
                           "Примеры правильных часовых поясов:\n" +
                           "• Europe/Moscow\n• Europe/London\n• America/New_York\n• Asia/Tokyo")
    except Exception as e:
        logger.error(f"Error in set_timezone: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при установке часового пояса")

@bot.message_handler(commands=['set_workday'])
def set_workday_command(message):
    """Handle /set_workday command"""
    log_user_request(message, "command")
    user_id = message.from_user.id
    
    try:
        # Extract workday hours from command
        parts = message.text.split()
        if len(parts) != 3:
            bot.send_message(message.chat.id, 
                           "❌ Неверный формат команды. Используйте: `/set_workday 09:00 18:00`", 
                           parse_mode='Markdown')
            return
        
        start_str, end_str = parts[1], parts[2]
        
        # Parse times
        try:
            start_time = datetime.strptime(start_str, '%H:%M').time()
            end_time = datetime.strptime(end_str, '%H:%M').time()
        except ValueError:
            bot.send_message(message.chat.id, 
                           "❌ Неверный формат времени. Используйте формат HH:MM (например, 09:00)")
            return
        
        user = User.get_or_create(user_id)
        
        if user.update_workday(start_time, end_time):
            bot.send_message(message.chat.id, 
                           f"✅ Рабочее время успешно установлено: {start_str} - {end_str}")
        else:
            bot.send_message(message.chat.id, 
                           "❌ Произошла ошибка при установке рабочего времени")
    except Exception as e:
        logger.error(f"Error in set_workday: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при установке рабочего времени")

@bot.message_handler(func=lambda message: message.text == "🏖️ Отдых")
def handle_rest_button(message):
    """Handle 'Отдых' button press"""
    log_user_request(message, "button")
    user_id = message.from_user.id
    
    try:
        # Check if there's an active task
        current_task = Task.get_active_task(user_id)
        if current_task:
            # End current task
            current_task.end_task()
            logger.info(f"Task ended for user {user_id}: {current_task.task_name}")
        
        # Create rest task
        user = User.get_or_create(user_id)
        now_utc = datetime.now(pytz.UTC)
        
        rest_task = Task.create(
            user_id=user_id,
            task_name="Отдых",
            comment="Перерыв в работе",
            start_time=now_utc,
            is_rest=True
        )
        
        bot.send_message(message.chat.id, 
                       f"🏖️ Отдых начат в {format_time_for_user(now_utc, user)}\n\n" +
                       "Отправьте любое сообщение с названием задачи, чтобы завершить отдых и начать новую задачу.",
                       reply_markup=get_main_keyboard())
        
    except Exception as e:
        logger.error(f"Error in handle_rest_button: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при начале отдыха")

@bot.message_handler(func=lambda message: message.text == "📊 Сводка")
def handle_summary_button(message):
    """Handle 'Сводка' button press"""
    log_user_request(message, "button")
    user_id = message.from_user.id
    
    try:
        user = User.get_or_create(user_id)
        
        # Get today's date in user's timezone
        user_now = user.get_local_time()
        today = user_now.date()
        
        # Get all tasks for today
        tasks = Task.get_tasks_for_date(user_id, user_now)
        
        if not tasks:
            bot.send_message(message.chat.id, 
                           f"📊 *Сводка за {today.strftime('%d.%m.%Y')}*\n\n" +
                           "❌ За сегодня задач не найдено.",
                           parse_mode='Markdown')
            return
        
        # Calculate statistics
        total_work_time = timedelta()
        total_rest_time = timedelta()
        work_tasks = []
        rest_tasks = []
        
        for task in tasks:
            task_duration = task.get_duration()
            if task.is_rest:
                total_rest_time += task_duration
                rest_tasks.append(task)
            else:
                total_work_time += task_duration
                work_tasks.append(task)
        
        # Format summary
        summary = f"📊 *Сводка за {today.strftime('%d.%m.%Y')}*\n\n"
        
        # Work time summary
        summary += f"⏰ *Рабочее время:* {format_duration(total_work_time)}\n"
        summary += f"🏖️ *Время отдыха:* {format_duration(total_rest_time)}\n"
        summary += f"📈 *Общее время:* {format_duration(total_work_time + total_rest_time)}\n\n"
        
        # Work tasks details
        if work_tasks:
            summary += "*🔧 Рабочие задачи:*\n"
            for task in work_tasks:
                start_time = format_time_for_user(task.start_time, user)
                end_time = format_time_for_user(task.end_time, user) if task.end_time else "не завершена"
                duration = format_duration(task.get_duration())
                
                task_display = format_task_for_display(task.task_name, original_message=task.original_message)
                summary += f"• {task_display}\n"
                summary += f"  ⏰ {start_time} - {end_time} ({duration})\n"
                if task.comment:
                    summary += f"  💬 {task.comment}\n"
                summary += "\n"
        
        # Rest periods
        if rest_tasks:
            summary += "*🏖️ Периоды отдыха:*\n"
            for task in rest_tasks:
                start_time = format_time_for_user(task.start_time, user)
                end_time = format_time_for_user(task.end_time, user) if task.end_time else "не завершен"
                duration = format_duration(task.get_duration())
                summary += f"• {start_time} - {end_time} ({duration})\n"
        
        bot.send_message(message.chat.id, summary, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in handle_summary_button: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при создании сводки")

@bot.message_handler(func=lambda message: message.text == "❓ Помощь")
def handle_help_button(message):
    """Handle 'Помощь' button press"""
    log_user_request(message, "button")
    
    help_text = """
❓ *Справка по использованию бота*

*📋 Основные команды:*
• `/start` - Запуск бота и показ настроек
• `/set_timezone Europe/Moscow` - Установка часового пояса
• `/set_workday 09:00 18:00` - Установка рабочих часов

*🔥 Быстрые действия:*
• 🏖️ *Отдых* - Начать перерыв
• 📊 *Сводка* - Показать отчет за день
• ❓ *Помощь* - Эта справка

*📝 Создание задач:*
Просто отправьте сообщение с названием задачи:
• `Разработка нового функционала`
• `Встреча с командой`
• `Код-ревью`

*🕐 Указание времени:*
• `14:30 Важная встреча` - Задача с определенным временем
• `14_30 Код-ревью` - Альтернативный формат времени

*🔗 Jira интеграция:*
• `PROJ-123 Исправление бага` - Автоматическая ссылка на тикет
• `https://jira.company.com/browse/TASK-456` - Прямая ссылка

*💬 Комментарии к задачам:*
• `Разработка API - добавить новые методы`
• `Встреча - обсуждение планов на спринт`

*🤖 Автоматические функции:*
• Автоматическое завершение предыдущей задачи при создании новой
• Завершение задач по окончании рабочего дня
• Обновление задачи, если отправлено то же название в то же время

*📊 Аналитика:*
• Подсчет рабочего времени и времени отдыха
• Детальная статистика по задачам
• Сводки за день с разбивкой по времени

Бот поддерживает многопользовательский режим и сохраняет все данные в базе данных.
"""
    
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_task_message(message):
    """Handle task messages"""
    log_user_request(message, "task")
    user_id = message.from_user.id
    
    try:
        # Parse task message
        task_name, comment, is_jira = parse_task_message(message.text)
        
        if not task_name:
            bot.send_message(message.chat.id, "❌ Не удалось распознать название задачи")
            return
        
        user = User.get_or_create(user_id)
        
        # Parse time from message
        parsed_time, remaining_message = parse_time_from_message(message.text)
        
        if parsed_time:
            # Use specified time
            start_time = create_datetime_from_time(user, parsed_time)
        else:
            # Use current time
            start_time = datetime.now(pytz.UTC)
        
        # Check for active task
        current_task = Task.get_active_task(user_id)
        
        # Check if it's the same task at the same time (update scenario)
        if current_task and current_task.task_name == task_name:
            # Check if start time is very close (within 1 minute)
            current_start = current_task.start_time
            if current_start.tzinfo is None:
                current_start = pytz.UTC.localize(current_start)
            if start_time.tzinfo is None:
                start_time = pytz.UTC.localize(start_time)
            
            time_diff = abs((start_time - current_start).total_seconds())
            if time_diff <= 60:  # Within 1 minute
                # Update existing task
                if current_task.update_with_same_time(task_name, comment, message.text):
                    formatted_task = format_task_for_display(task_name, is_jira, message.text)
                    bot.send_message(message.chat.id, 
                                   f"✏️ *Задача обновлена:*\n{formatted_task}\n\n" +
                                   f"🕐 Время: {format_time_for_user(start_time, user)}" +
                                   (f"\n💬 {comment}" if comment else ""),
                                   parse_mode='Markdown',
                                   reply_markup=get_main_keyboard())
                    return
        
        # End current task if exists
        if current_task:
            current_task.end_task(start_time)
            logger.info(f"Previous task ended for user {user_id}: {current_task.task_name}")
        
        # Create new task
        new_task = Task.create(
            user_id=user_id,
            task_name=task_name,
            comment=comment,
            start_time=start_time,
            is_rest=False,
            original_message=message.text
        )
        
        # Send confirmation
        formatted_task = format_task_for_display(task_name, is_jira, message.text)
        confirmation_message = f"✅ *Задача создана:*\n{formatted_task}\n\n" + \
                             f"🕐 Время начала: {format_time_for_user(start_time, user)}"
        
        if comment:
            confirmation_message += f"\n💬 {comment}"
        
        bot.send_message(message.chat.id, confirmation_message, 
                       parse_mode='Markdown', reply_markup=get_main_keyboard())
        
    except Exception as e:
        logger.error(f"Error in handle_task_message: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при создании задачи")

def run_telegram_bot():
    """Run the Telegram bot"""
    try:
        logger.info("Starting Telegram bot...")
        app_status['bot_running'] = True
        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(f"Telegram bot error: {e}")
        app_status['bot_running'] = False

def run_web_server():
    """Run the web server"""
    try:
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"Starting web server on port {port}")
        app_status['web_server_running'] = True
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Web server error: {e}")
        app_status['web_server_running'] = False

def main():
    """Main function"""
    logger.info("Initializing database...")
    init_database()
    logger.info("Database initialized successfully")
    
    # Start web server in a separate thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Give web server time to start
    time_module.sleep(2)
    
    # Start Telegram bot in main thread
    run_telegram_bot()

if __name__ == "__main__":
    main()