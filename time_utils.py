from datetime import datetime, time, timedelta
import pytz
import re
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

def parse_time_from_message(message: str) -> Tuple[Optional[time], str]:
    """
    Parse time from message in format '14:00' or '14_00'
    Returns (parsed_time, remaining_message)
    """
    # Pattern to match time formats: 14:00, 14_00, etc.
    time_pattern = r'^(\d{1,2})[:_](\d{2})\s+'
    match = re.match(time_pattern, message.strip())
    
    if match:
        try:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            
            if 0 <= hours <= 23 and 0 <= minutes <= 59:
                parsed_time = time(hours, minutes)
                remaining_message = message[match.end():].strip()
                return parsed_time, remaining_message
        except ValueError:
            pass
    
    return None, message

def format_duration(duration: timedelta) -> str:
    """Format timedelta to human readable string"""
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}ч {minutes}м"
    else:
        return f"{minutes}м"

def get_workday_end_time(user, local_date: datetime) -> datetime:
    """Get workday end time for a specific date in user's timezone"""
    user_tz = pytz.timezone(user.timezone)
    
    # Combine date with workday end time
    workday_end = datetime.combine(local_date.date(), user.workday_end)
    workday_end_local = user_tz.localize(workday_end)
    
    return workday_end_local.astimezone(pytz.utc)

def should_auto_end_task(user, task_start_time: datetime) -> Tuple[bool, datetime]:
    """
    Check if task should be auto-ended and return end time
    Returns (should_end, end_time)
    """
    user_tz = pytz.timezone(user.timezone)
    
    # Convert task start time to user timezone
    if task_start_time.tzinfo is None:
        task_start_time = pytz.utc.localize(task_start_time)
    
    task_start_local = task_start_time.astimezone(user_tz)
    
    # Get workday end for the same date
    workday_end_local = datetime.combine(
        task_start_local.date(), 
        user.workday_end
    )
    workday_end_local = user_tz.localize(workday_end_local)
    
    # Check if task started after workday end
    if task_start_local.time() > user.workday_end:
        # End at 23:59 of the same day
        end_time_local = datetime.combine(
            task_start_local.date(),
            time(23, 59)
        )
        end_time_local = user_tz.localize(end_time_local)
        return True, end_time_local.astimezone(pytz.utc)
    
    # Check if current time is past workday end
    now_local = datetime.now(user_tz)
    if now_local >= workday_end_local:
        return True, workday_end_local.astimezone(pytz.utc)
    
    return False, None

def format_time_for_user(dt: datetime, user) -> str:
    """Format datetime for user's timezone"""
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    
    user_tz = pytz.timezone(user.timezone)
    local_time = dt.astimezone(user_tz)
    return local_time.strftime("%H:%M")

def create_datetime_from_time(user, target_time: time, reference_date: datetime = None) -> datetime:
    """Create datetime from time in user's timezone"""
    if reference_date is None:
        reference_date = datetime.now()
    
    user_tz = pytz.timezone(user.timezone)
    
    # Create datetime in user timezone
    target_datetime = datetime.combine(reference_date.date(), target_time)
    target_datetime_local = user_tz.localize(target_datetime)
    
    # Convert to UTC
    return target_datetime_local.astimezone(pytz.utc)
