from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ParseMode
from telegram.ext import CallbackContext
from datetime import datetime, time, timedelta
import pytz
import logging
from models import User, Task
from task_parser import parse_task_message, format_task_for_display, get_unique_comments
from time_utils import (
    parse_time_from_message, format_duration, 
    should_auto_end_task, format_time_for_user,
    create_datetime_from_time
)

logger = logging.getLogger(__name__)

def get_main_keyboard():
    """Get main keyboard with buttons"""
    keyboard = [
        [KeyboardButton("🏖️ Отдых"), KeyboardButton("📊 Сводка")],
        [KeyboardButton("❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def start_command(update: Update, context: CallbackContext):
    """Handle /start command"""
    user_id = update.effective_user.id
    
    # Create or get user
    user = User.get_or_create(user_id)
    
    message = f"""
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
    
    # Send welcome message
    update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

def set_timezone_command(update: Update, context: CallbackContext):
    """Handle /set_timezone command"""
    user_id = update.effective_user.id
    user = User.get_or_create(user_id)
    
    if not context.args:
        message = f"""
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
        update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        return
    
    timezone = context.args[0]
    
    if user.update_timezone(timezone):
        current_time = user.get_local_time()
        message = f"✅ Часовой пояс успешно изменен на `{timezone}`\nТекущее время: `{current_time.strftime('%H:%M %d.%m.%Y')}`"
    else:
        message = f"❌ Неверный часовой пояс: `{timezone}`\nИспользуйте команду без параметров для просмотра примеров."
    
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

def set_workday_command(update: Update, context: CallbackContext):
    """Handle /set_workday command"""
    user_id = update.effective_user.id
    user = User.get_or_create(user_id)
    
    if not context.args or len(context.args) != 2:
        message = f"""
🕐 *Настройка рабочего времени*

Текущее рабочее время: `{user.workday_start.strftime('%H:%M')} - {user.workday_end.strftime('%H:%M')}`

Для изменения используйте:
`/set_workday 09:00 18:00`
`/set_workday 10:30 19:30`

Задачи будут автоматически завершаться в конце рабочего дня.
        """
        update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        return
    
    try:
        start_str, end_str = context.args[0], context.args[1]
        start_time = datetime.strptime(start_str, '%H:%M').time()
        end_time = datetime.strptime(end_str, '%H:%M').time()
        
        if user.update_workday(start_time, end_time):
            message = f"✅ Рабочее время изменено: `{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}`"
        else:
            message = "❌ Ошибка при сохранении рабочего времени"
    except ValueError:
        message = "❌ Неверный формат времени. Используйте формат HH:MM (например, 09:00 18:00)"
    
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

def handle_rest_button(update: Update, context: CallbackContext):
    """Handle 'Отдых' button press"""
    user_id = update.effective_user.id
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
    
    message = f"""
🏖️ *Начат отдых*

{previous_message}

Время начала отдыха: `{format_time_for_user(rest_task.start_time, user)}`

Для продолжения работы отправьте название новой задачи или нажмите кнопку "Сводка" для просмотра статистики.
    """
    
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_keyboard())

def handle_summary_button(update: Update, context: CallbackContext):
    """Handle 'Сводка' button press"""
    user_id = update.effective_user.id
    user = User.get_or_create(user_id)
    
    # Get today's date in user's timezone
    today = user.get_local_time().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get all tasks for today
    tasks = Task.get_tasks_for_date(user_id, today)
    
    if not tasks:
        message = f"""
📊 *Сводка за {today.strftime('%d %B %Y')}*

Задач за сегодня не найдено.

Начните отслеживание времени, отправив название задачи!
        """
        update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_keyboard())
        return
    
    # Get current task
    current_task = Task.get_active_task(user_id)
    
    # Build summary
    message_parts = [f"📊 *Сводка за {today.strftime('%d %B %Y')}*"]
    
    if current_task:
        current_duration = current_task.get_duration()
        current_display = format_task_for_display(current_task.task_name, current_task.task_name.startswith(('PROJ-', 'TASK-', 'DEV-', 'BUG-')))
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
                'is_rest': task.is_rest
            }
    
    # Add tasks list
    message_parts.append(f"\n📋 *Задачи за день:*")
    
    for task_name, group in task_groups.items():
        duration_str = format_duration(group['duration'])
        task_display = format_task_for_display(task_name)
        
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
    
    # Add unique comments
    all_comments = []
    for task in tasks:
        if task.comment:
            all_comments.append(task.comment)
    
    unique_comments = list(set(all_comments))
    if unique_comments:
        message_parts.append(f"\n💬 *Комментарии:*")
        for comment in unique_comments[:5]:  # Limit to 5 comments to avoid long messages
            message_parts.append(f"• {comment}")
    
    message = "\n".join(message_parts)
    
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_keyboard())

def handle_help_button(update: Update, context: CallbackContext):
    """Handle 'Помощь' button press"""
    message = """
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
    
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_keyboard())

def handle_task_message(update: Update, context: CallbackContext):
    """Handle task messages"""
    user_id = update.effective_user.id
    user = User.get_or_create(user_id)
    message_text = update.message.text
    
    # Parse task message
    task_name, comment, is_jira = parse_task_message(message_text)
    
    if not task_name:
        update.message.reply_text(
            "❌ Не удалось распознать название задачи. Попробуйте еще раз.",
            reply_markup=get_main_keyboard()
        )
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
        time_diff = abs((start_time - current_task.start_time).total_seconds())
        if time_diff < 60:
            # Update existing task
            if current_task.update_with_same_time(task_name, comment):
                task_display = format_task_for_display(task_name, is_jira)
                message = f"✏️ Задача **{task_display}** обновлена"
                if comment:
                    message += f" с комментарием: _{comment}_"
                
                update.message.reply_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_main_keyboard()
                )
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
    new_task = Task.create(user_id, task_name, comment, start_time)
    
    if new_task:
        task_display = format_task_for_display(task_name, is_jira)
        start_time_str = format_time_for_user(start_time, user)
        
        message = f"{previous_info}✅ Начата задача **{task_display}**"
        
        if comment:
            message += f"\n💬 Комментарий: _{comment}_"
        
        if specified_time:
            message += f"\n⏰ Время начала: `{start_time_str}`"
        else:
            message += f"\n⏰ Начата в: `{start_time_str}`"
        
        update.message.reply_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard()
        )
    else:
        update.message.reply_text(
            "❌ Ошибка при создании задачи. Попробуйте еще раз.",
            reply_markup=get_main_keyboard()
        )

def auto_end_tasks_job(context: CallbackContext):
    """Background job to auto-end tasks that exceed workday"""
    logger.info("Running auto-end tasks job")
    
    try:
        # Get all users with active tasks (this would need to be implemented in models)
        # For now, we'll handle this differently since we don't have a way to get all users
        # This is a simplified version - in production you'd query all users
        pass
        
    except Exception as e:
        logger.error(f"Error in auto_end_tasks_job: {e}")