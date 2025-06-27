from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from datetime import datetime, time, timedelta
import pytz
import logging
from models import User, Task
from time_utils import (
    parse_time_from_message, format_duration, should_auto_end_task,
    format_time_for_user, create_datetime_from_time
)
from task_parser import parse_task_message, format_task_for_display, get_unique_comments

logger = logging.getLogger(__name__)

# Keyboard markup
def get_main_keyboard():
    """Get main keyboard with buttons"""
    keyboard = [
        [KeyboardButton("Отдых"), KeyboardButton("Сводка")],
        [KeyboardButton("Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    
    # Create or get user
    User.get_or_create(user_id)
    
    welcome_message = """
🚀 **Добро пожаловать в бота для трекинга времени!**

**Основные возможности:**
• Отслеживание времени выполнения задач
• Поддержка Jira-ссылок
• Автоматическое переключение между задачами
• Настройка часового пояса и рабочего дня
• Ежедневная статистика

**Как использовать:**

**1. Запуск задачи:**
`task_name комментарий` - начать задачу
`https://jira.example.com/browse/TASK-123 комментарий` - Jira задача

**2. С указанием времени:**
`14:00 task_name комментарий` - начать задачу в 14:00
`14_00 task_name` - альтернативный формат времени

**3. Кнопки:**
• **Отдых** - завершить текущую задачу и начать отдых
• **Сводка** - показать статистику за день

**4. Настройки:**
`/set_timezone Europe/Moscow` - установить часовой пояс
`/set_workday 09:00 18:00` - установить рабочий день

**Примеры:**
• `coding исправление бага в авторизации`
• `meeting обсуждение архитектуры`
• `https://jira.company.com/browse/TASK-123 реализация новой функции`
• `14:30 review код-ревью PR#456`

Удачной работы! 🚀
    """
    
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def set_timezone_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /set_timezone command"""
    user_id = update.effective_user.id
    user = User.get_or_create(user_id)
    
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите часовой пояс\n\n"
            "**Примеры:**\n"
            "`/set_timezone Europe/Moscow`\n"
            "`/set_timezone America/New_York`\n"
            "`/set_timezone Asia/Tokyo`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    timezone = context.args[0]
    
    if user.update_timezone(timezone):
        local_time = user.get_local_time()
        await update.message.reply_text(
            f"✅ Часовой пояс установлен: `{timezone}`\n"
            f"🕐 Текущее время: `{local_time.strftime('%H:%M')}`",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            "❌ Неверный часовой пояс\n\n"
            "Используйте формат: `Europe/Moscow`, `America/New_York`",
            parse_mode=ParseMode.MARKDOWN
        )

async def set_workday_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /set_workday command"""
    user_id = update.effective_user.id
    user = User.get_or_create(user_id)
    
    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ Укажите время начала и конца рабочего дня\n\n"
            "**Пример:**\n"
            "`/set_workday 09:00 18:00`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        start_str, end_str = context.args
        start_time = datetime.strptime(start_str, "%H:%M").time()
        end_time = datetime.strptime(end_str, "%H:%M").time()
        
        if user.update_workday(start_time, end_time):
            await update.message.reply_text(
                f"✅ Рабочий день установлен: `{start_str} - {end_str}`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text("❌ Ошибка при сохранении настроек")
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат времени\n\n"
            "Используйте формат: `09:00 18:00`",
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_rest_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Отдых' button press"""
    user_id = update.effective_user.id
    user = User.get_or_create(user_id)
    
    # End current active task if exists
    active_task = Task.get_active_task(user_id)
    if active_task:
        active_task.end_task()
        duration = active_task.get_duration()
        task_display = format_task_for_display(active_task.task_name)
        
        await update.message.reply_text(
            f"✅ Задача {task_display} завершена\n"
            f"⏱️ Продолжительность: {format_duration(duration)}",
            parse_mode=ParseMode.MARKDOWN
        )
    
    # Start rest task
    rest_task = Task.create(
        user_id=user_id,
        task_name="отдых",
        is_rest=True
    )
    
    await update.message.reply_text(
        "😴 Начат отдых\n\n"
        "Отправьте новую задачу, чтобы продолжить работу",
        reply_markup=get_main_keyboard()
    )

async def handle_summary_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Сводка' button press"""
    user_id = update.effective_user.id
    user = User.get_or_create(user_id)
    
    # Get current local date
    now_local = user.get_local_time()
    
    # Get active task
    active_task = Task.get_active_task(user_id)
    
    # Get all tasks for today
    today_tasks = Task.get_tasks_for_date(user_id, now_local)
    
    summary_text = f"📊 **Сводка за {now_local.strftime('%d.%m.%Y')}**\n\n"
    
    # Current active task
    if active_task:
        duration = active_task.get_duration()
        task_display = format_task_for_display(active_task.task_name)
        start_time = format_time_for_user(active_task.start_time, user)
        
        summary_text += f"🔄 **Текущая задача:**\n"
        summary_text += f"{task_display}\n"
        summary_text += f"⏰ Начало: {start_time}\n"
        summary_text += f"⏱️ Длительность: {format_duration(duration)}\n\n"
    else:
        summary_text += "💤 Нет активной задачи\n\n"
    
    # Today's tasks summary
    if today_tasks:
        summary_text += "📝 **Задачи за день:**\n\n"
        
        # Group tasks by name
        task_groups = {}
        for task in today_tasks:
            if task.task_name not in task_groups:
                task_groups[task.task_name] = []
            task_groups[task.task_name].append(task)
        
        for task_name, tasks in task_groups.items():
            # Calculate total duration for this task
            total_duration = timedelta()
            for task in tasks:
                total_duration += task.get_duration()
            
            task_display = format_task_for_display(task_name)
            summary_text += f"• {task_display} — {format_duration(total_duration)}\n"
            
            # Get unique comments for this task
            unique_comments = get_unique_comments(tasks)
            for comment in unique_comments:
                summary_text += f"  └ {comment}\n"
            
            summary_text += "\n"
        
        # Calculate total work time
        total_work_time = timedelta()
        for task in today_tasks:
            if not task.is_rest:
                total_work_time += task.get_duration()
        
        summary_text += f"⏱️ **Общее время работы:** {format_duration(total_work_time)}\n"
    else:
        summary_text += "📝 Задач за день пока нет"
    
    await update.message.reply_text(
        summary_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_help_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Помощь' button press"""
    help_text = """
📋 **Список доступных команд:**

**Основные команды:**
• `/start` — Запустить бота и получить приветствие
• `/set_timezone <часовой_пояс>` — Настроить часовой пояс
  Пример: `/set_timezone Europe/Moscow`
• `/set_workday <начало> <конец>` — Настроить рабочий день
  Пример: `/set_workday 09:00 18:00`

**Кнопки:**
• **Отдых** — Завершить текущую задачу и начать отдых
• **Сводка** — Показать отчет за день и активную задачу
• **Помощь** — Показать этот список команд

**Трекинг задач:**
• Просто отправьте название задачи для начала работы
• Поддерживаются Jira-ссылки (автоматически извлекается номер тикета)
• Можно указать время начала: `14:00 Название задачи`
• Добавляйте комментарии через дефис: `Задача - мой комментарий`

**Примеры:**
• `Разработка фичи`
• `14:30 Исправление бага`
• `https://company.atlassian.net/browse/PROJ-123`
• `Совещание - обсуждение планов`

**Автоматические функции:**
• Задачи завершаются автоматически в конце рабочего дня
• Время отображается в вашем часовом поясе
• Поддержка многих часовых поясов мира

❓ **Нужна помощь?** Просто начните писать, и бот поможет!
"""
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def handle_task_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle task messages"""
    user_id = update.effective_user.id
    user = User.get_or_create(user_id)
    message_text = update.message.text.strip()
    
    # Parse time from message if present
    specified_time, remaining_message = parse_time_from_message(message_text)
    
    # Parse task name and comment
    task_name, comment, is_jira = parse_task_message(remaining_message)
    
    # Determine start time
    if specified_time:
        start_time = create_datetime_from_time(user, specified_time)
    else:
        start_time = datetime.utcnow()
    
    # Check if there's an active task with the same time (for overwriting)
    active_task = Task.get_active_task(user_id)
    should_overwrite = False
    
    if active_task and specified_time:
        active_start_local = user.get_local_time(active_task.start_time)
        new_start_local = user.get_local_time(start_time)
        
        # If times are the same (within same minute), overwrite
        if (active_start_local.replace(second=0, microsecond=0) == 
            new_start_local.replace(second=0, microsecond=0)):
            should_overwrite = True
    
    if should_overwrite:
        # Update existing task
        active_task.update_with_same_time(task_name, comment)
        task_display = format_task_for_display(task_name, is_jira)
        
        await update.message.reply_text(
            f"✏️ Задача обновлена: {task_display}\n"
            f"⏰ Время: {format_time_for_user(start_time, user)}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard()
        )
    else:
        # End current active task if exists
        if active_task:
            active_task.end_task(start_time)
            duration = active_task.get_duration()
            old_task_display = format_task_for_display(active_task.task_name)
            
            await update.message.reply_text(
                f"✅ Предыдущая задача завершена: {old_task_display}\n"
                f"⏱️ Продолжительность: {format_duration(duration)}",
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Create new task
        new_task = Task.create(
            user_id=user_id,
            task_name=task_name,
            comment=comment,
            start_time=start_time,
            is_rest=False
        )
        
        task_display = format_task_for_display(task_name, is_jira)
        start_time_str = format_time_for_user(start_time, user)
        
        response_text = f"🚀 Начата задача: {task_display}\n⏰ Время начала: {start_time_str}"
        
        if comment:
            response_text += f"\n💬 Комментарий: {comment}"
        
        await update.message.reply_text(
            response_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard()
        )

async def auto_end_tasks_job(context: ContextTypes.DEFAULT_TYPE):
    """Background job to auto-end tasks that exceed workday"""
    try:
        from models import User, Task
        from database import get_db
        
        # Get all users with active tasks
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT u.user_id, u.timezone, u.workday_start, u.workday_end
                FROM users u
                JOIN tasks t ON u.user_id = t.user_id
                WHERE t.end_time IS NULL
            """)
            
            users_with_active_tasks = cursor.fetchall()
        
        for user_data in users_with_active_tasks:
            user = User(
                user_id=user_data['user_id'],
                timezone=user_data['timezone'],
                workday_start=user_data['workday_start'],
                workday_end=user_data['workday_end']
            )
            
            active_task = Task.get_active_task(user.user_id)
            if active_task:
                # Ensure start_time is timezone-aware
                start_time = active_task.start_time
                if start_time.tzinfo is None:
                    start_time = pytz.utc.localize(start_time)
                
                should_end, end_time = should_auto_end_task(user, start_time)
                
                if should_end and end_time:
                    active_task.end_task(end_time)
                    
                    # Send notification to user
                    duration = active_task.get_duration()
                    task_display = format_task_for_display(active_task.task_name)
                    
                    message = (
                        f"⏰ Задача автоматически завершена: {task_display}\n"
                        f"⏱️ Продолжительность: {format_duration(duration)}\n"
                        f"🔔 Причина: окончание рабочего дня"
                    )
                    
                    await context.bot.send_message(
                        chat_id=user.user_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=get_main_keyboard()
                    )
                    
                    logger.info(f"Auto-ended task for user {user.user_id}")
    
    except Exception as e:
        logger.error(f"Error in auto_end_tasks_job: {e}")
