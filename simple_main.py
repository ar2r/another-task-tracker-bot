import os
import logging
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from database import init_database
from models import User, Task
from task_parser import parse_task_message, format_task_for_display
from time_utils import format_duration, format_time_for_user, create_datetime_from_time, parse_time_from_message
from datetime import datetime, time, timedelta
import pytz

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable is not set")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

def get_main_keyboard():
    """Get main keyboard with buttons"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(KeyboardButton("🏖️ Отдых"), KeyboardButton("📊 Сводка"))
    keyboard.row(KeyboardButton("❓ Помощь"))
    return keyboard

@bot.message_handler(commands=['start'])
def start_command(message):
    """Handle /start command"""
    user_id = message.from_user.id
    
    # Create or get user
    user = User.get_or_create(user_id)
    
    text = f"""
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
3. Создайте задачу: просто отправьте название

*Текущие настройки:*
• Часовой пояс: `{user.timezone}`
• Рабочее время: `{user.workday_start.strftime('%H:%M')} - {user.workday_end.strftime('%H:%M')}`

Используйте кнопки ниже для быстрого доступа к функциям.
    """
    
    bot.reply_to(message, text, parse_mode='Markdown', reply_markup=get_main_keyboard())

@bot.message_handler(commands=['set_timezone'])
def set_timezone_command(message):
    """Handle /set_timezone command"""
    user_id = message.from_user.id
    user = User.get_or_create(user_id)
    
    # Получаем аргументы команды
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if not args:
        text = f"""
⏰ *Настройка часового пояса*

Текущий часовой пояс: `{user.timezone}`

Для изменения используйте:
`/set_timezone Europe/Moscow`
`/set_timezone America/New_York`
`/set_timezone Asia/Tokyo`

Список популярных часовых поясов:
• Europe/Moscow (UTC+3)
• Europe/London (UTC+0)
• America/New_York (UTC-5)
• America/Los_Angeles (UTC-8)
• Asia/Tokyo (UTC+9)
        """
        bot.reply_to(message, text, parse_mode='Markdown')
        return
    
    timezone = args[0]
    
    if user.update_timezone(timezone):
        current_time = user.get_local_time()
        text = f"✅ Часовой пояс успешно изменен на `{timezone}`\nТекущее время: `{current_time.strftime('%H:%M %d.%m.%Y')}`"
    else:
        text = f"❌ Неверный часовой пояс: `{timezone}`\nИспользуйте команду без параметров для просмотра примеров."
    
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['set_workday'])
def set_workday_command(message):
    """Handle /set_workday command"""
    user_id = message.from_user.id
    user = User.get_or_create(user_id)
    
    # Получаем аргументы команды
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if len(args) != 2:
        text = f"""
🕐 *Настройка рабочего времени*

Текущее рабочее время: `{user.workday_start.strftime('%H:%M')} - {user.workday_end.strftime('%H:%M')}`

Для изменения используйте:
`/set_workday 09:00 18:00`
`/set_workday 10:30 19:30`

Задачи будут автоматически завершаться в конце рабочего дня.
        """
        bot.reply_to(message, text, parse_mode='Markdown')
        return
    
    try:
        start_str, end_str = args[0], args[1]
        start_time = datetime.strptime(start_str, '%H:%M').time()
        end_time = datetime.strptime(end_str, '%H:%M').time()
        
        if user.update_workday(start_time, end_time):
            text = f"✅ Рабочее время изменено: `{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}`"
        else:
            text = "❌ Ошибка при сохранении рабочего времени"
    except ValueError:
        text = "❌ Неверный формат времени. Используйте формат HH:MM (например, 09:00 18:00)"
    
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "🏖️ Отдых")
def handle_rest_button(message):
    """Handle 'Отдых' button press"""
    user_id = message.from_user.id
    user = User.get_or_create(user_id)
    
    # End current task
    current_task = Task.get_active_task(user_id)
    if current_task:
        current_task.end_task()
    
    # Start rest task
    rest_task = Task.create(user_id, "🏖️ Отдых", is_rest=True)
    
    if current_task:
        duration = current_task.get_duration()
        previous_message = f"Задача **{format_task_for_display(current_task.task_name)}** завершена (длительность: {format_duration(duration)})"
    else:
        previous_message = "Активных задач не было"
    
    text = f"""
🏖️ *Начат отдых*

{previous_message}

Время начала отдыха: `{format_time_for_user(rest_task.start_time, user)}`

Для продолжения работы отправьте название новой задачи или нажмите кнопку "Сводка" для просмотра статистики.
    """
    
    bot.reply_to(message, text, parse_mode='Markdown', reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "📊 Сводка")
def handle_summary_button(message):
    """Handle 'Сводка' button press"""
    user_id = message.from_user.id
    user = User.get_or_create(user_id)
    
    # Get today's date in user's timezone
    today = user.get_local_time().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get all tasks for today
    tasks = Task.get_tasks_for_date(user_id, today)
    
    if not tasks:
        text = f"""
📊 *Сводка за {today.strftime('%d %B %Y')}*

Задач за сегодня не найдено.

Начните отслеживание времени, отправив название задачи!
        """
        bot.reply_to(message, text, parse_mode='Markdown', reply_markup=get_main_keyboard())
        return
    
    # Get current task
    current_task = Task.get_active_task(user_id)
    
    # Build summary
    message_parts = [f"📊 *Сводка за {today.strftime('%d %B %Y')}*"]
    
    if current_task:
        current_duration = current_task.get_duration()
        current_display = format_task_for_display(current_task.task_name, original_message=current_task.original_message)
        message_parts.append(f"\n🔄 *Текущая задача:*")
        message_parts.append(f"**{current_display}** (начата в {format_time_for_user(current_task.start_time, user)}, выполняется {format_duration(current_duration)})")
    
    # Group tasks by name and calculate totals
    task_groups = {}
    total_work_time = timedelta()
    
    for task in tasks:
        duration = task.get_duration()
        
        if not task.is_rest:
            total_work_time += duration
        
        if task.task_name in task_groups:
            task_groups[task.task_name]['duration'] += duration
            task_groups[task.task_name]['tasks'].append(task)
        else:
            task_groups[task.task_name] = {
                'duration': duration,
                'tasks': [task],
                'is_rest': task.is_rest,
                'original_message': task.original_message
            }
    
    # Add tasks list
    message_parts.append(f"\n📋 *Задачи за день:*")
    
    for task_name, group in task_groups.items():
        duration_str = format_duration(group['duration'])
        task_display = format_task_for_display(task_name, original_message=group.get('original_message'))
        
        if group['is_rest']:
            message_parts.append(f"• **{task_display}** — {duration_str}")
        else:
            if task_name == current_task.task_name if current_task else False:
                message_parts.append(f"• **{task_display}** — {duration_str} (текущая)")
            else:
                message_parts.append(f"• **{task_display}** — {duration_str}")
    
    # Add total work time
    if total_work_time.total_seconds() > 0:
        message_parts.append(f"\n⏱️ *Общее рабочее время:* {format_duration(total_work_time)}")
    
    text = "\n".join(message_parts)
    
    bot.reply_to(message, text, parse_mode='Markdown', reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "❓ Помощь")
def handle_help_button(message):
    """Handle 'Помощь' button press"""
    text = """
❓ *Справка по использованию бота*

*🎯 Основные команды:*
• `/start` — начать работу с ботом
• `/set_timezone <timezone>` — установить часовой пояс
• `/set_workday <start> <end>` — настроить рабочее время

*📝 Создание задач:*
• `Разработка функции` — простая задача
• `14:30 Планерка` — задача с указанием времени
• `Код-ревью - проверка PR` — задача с комментарием

*🔗 Поддержка Jira:*
• `https://jira.company.com/PROJ-123`
• `TASK-456 - исправление бага`
• Автоматическое распознавание тикетов

*🎛️ Кнопки управления:*
• **🏖️ Отдых** — завершить задачу и начать перерыв
• **📊 Сводка** — отчет за текущий день
• **❓ Помощь** — эта справка

*⚙️ Автоматические функции:*
• Завершение задач в конце рабочего дня
• Группировка одинаковых задач в отчетах
• Поддержка часовых поясов
• Сохранение истории работы

*💡 Советы:*
• Указывайте время в формате `14:30` или `14_30`
• Используйте тире для отделения комментариев
• Задачи автоматически завершаются при создании новой
• Вся статистика сохраняется и доступна в сводках
    """
    
    bot.reply_to(message, text, parse_mode='Markdown', reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_task_message(message):
    """Handle task messages"""
    user_id = message.from_user.id
    user = User.get_or_create(user_id)
    message_text = message.text
    
    # Parse task message
    task_name, comment, is_jira = parse_task_message(message_text)
    
    if not task_name:
        bot.reply_to(message, "❌ Не удалось распознать название задачи. Попробуйте еще раз.", reply_markup=get_main_keyboard())
        return
    
    # Parse time from message
    specified_time, remaining_message = parse_time_from_message(message_text)
    
    # Get current task to end it
    current_task = Task.get_active_task(user_id)
    
    # Determine start time
    if specified_time:
        # Create datetime from specified time
        try:
            start_time = create_datetime_from_time(user, specified_time)
        except Exception:
            start_time = user.get_utc_time(user.get_local_time())
    else:
        start_time = user.get_utc_time(user.get_local_time())
    
    # Check if this is the same task at the same time (update scenario)
    if current_task and current_task.task_name == task_name:
        # Check if start time is very close (within 1 minute)
        # Ensure both datetimes have timezone info for comparison
        current_start = current_task.start_time
        if current_start.tzinfo is None:
            current_start = pytz.UTC.localize(current_start)
        if start_time.tzinfo is None:
            start_time = pytz.UTC.localize(start_time)
        time_diff = abs((start_time - current_start).total_seconds())
        if time_diff < 60:
            # Update existing task
            if current_task.update_with_same_time(task_name, comment, message_text):
                task_display = format_task_for_display(task_name, is_jira, message_text)
                text = f"✏️ Задача **{task_display}** обновлена"
                if comment:
                    text += f" с комментарием: _{comment}_"
                
                bot.reply_to(message, text, parse_mode='Markdown', reply_markup=get_main_keyboard())
                return
    
    # End current task if exists
    if current_task:
        current_task.end_task()
        previous_duration = current_task.get_duration()
        previous_display = format_task_for_display(current_task.task_name)
        previous_info = f"Предыдущая задача **{previous_display}** завершена (длительность: {format_duration(previous_duration)})\n\n"
    else:
        previous_info = ""
    
    # Create new task
    new_task = Task.create(user_id, task_name, comment, start_time, original_message=message_text)
    
    if new_task:
        task_display = format_task_for_display(task_name, is_jira, message_text)
        start_time_str = format_time_for_user(start_time, user)
        
        text = f"{previous_info}✅ Начата задача **{task_display}**"
        
        if comment:
            text += f"\n💬 Комментарий: _{comment}_"
        
        if specified_time:
            text += f"\n⏰ Время начала: `{start_time_str}`"
        else:
            text += f"\n⏰ Начата в: `{start_time_str}`"
        
        bot.reply_to(message, text, parse_mode='Markdown', reply_markup=get_main_keyboard())
    else:
        bot.reply_to(message, "❌ Ошибка при создании задачи. Попробуйте еще раз.", reply_markup=get_main_keyboard())

def main():
    """Start the bot"""
    logger.info("Initializing database...")
    
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return
    
    logger.info("Bot is starting...")
    
    # Start the bot
    bot.infinity_polling()

if __name__ == "__main__":
    main()