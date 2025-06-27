from datetime import datetime, time, timedelta
from typing import Optional, List, Dict, Any
import pytz
from database import get_db
import logging

logger = logging.getLogger(__name__)

class User:
    def __init__(self, user_id: int, timezone: str = 'Europe/Moscow', 
                 workday_start: time = time(9, 0), workday_end: time = time(18, 0)):
        self.user_id = user_id
        self.timezone = timezone
        self.workday_start = workday_start
        self.workday_end = workday_end
    
    @classmethod
    def get_or_create(cls, user_id: int) -> 'User':
        """Get existing user or create new one"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Try to get existing user
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            user_data = cursor.fetchone()
            
            if user_data:
                return cls(
                    user_id=user_data['user_id'],
                    timezone=user_data['timezone'],
                    workday_start=user_data['workday_start'],
                    workday_end=user_data['workday_end']
                )
            else:
                # Create new user
                cursor.execute("""
                    INSERT INTO users (user_id) VALUES (%s)
                    RETURNING user_id, timezone, workday_start, workday_end
                """, (user_id,))
                user_data = cursor.fetchone()
                
                return cls(
                    user_id=user_data['user_id'],
                    timezone=user_data['timezone'],
                    workday_start=user_data['workday_start'],
                    workday_end=user_data['workday_end']
                )
    
    def update_timezone(self, timezone: str) -> bool:
        """Update user timezone"""
        try:
            # Validate timezone
            pytz.timezone(timezone)
            
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users SET timezone = %s WHERE user_id = %s
                """, (timezone, self.user_id))
                
                self.timezone = timezone
                return True
        except Exception as e:
            logger.error(f"Error updating timezone: {e}")
            return False
    
    def update_workday(self, start_time: time, end_time: time) -> bool:
        """Update user workday hours"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users SET workday_start = %s, workday_end = %s 
                    WHERE user_id = %s
                """, (start_time, end_time, self.user_id))
                
                self.workday_start = start_time
                self.workday_end = end_time
                return True
        except Exception as e:
            logger.error(f"Error updating workday: {e}")
            return False
    
    def get_local_time(self, utc_time: datetime = None) -> datetime:
        """Convert UTC time to user's local time"""
        if utc_time is None:
            utc_time = datetime.utcnow()
        
        user_tz = pytz.timezone(self.timezone)
        utc_time = pytz.utc.localize(utc_time) if utc_time.tzinfo is None else utc_time
        return utc_time.astimezone(user_tz)
    
    def get_utc_time(self, local_time: datetime) -> datetime:
        """Convert user's local time to UTC"""
        user_tz = pytz.timezone(self.timezone)
        if local_time.tzinfo is None:
            local_time = user_tz.localize(local_time)
        return local_time.astimezone(pytz.utc)

class Task:
    def __init__(self, id: Optional[int], user_id: int, task_name: str, 
                 comment: Optional[str], start_time: datetime, 
                 end_time: Optional[datetime] = None, is_rest: bool = False,
                 original_message: Optional[str] = None):
        self.id = id
        self.user_id = user_id
        self.task_name = task_name
        self.comment = comment
        self.start_time = start_time
        self.end_time = end_time
        self.is_rest = is_rest
        self.original_message = original_message
    
    @classmethod
    def create(cls, user_id: int, task_name: str, comment: Optional[str] = None,
               start_time: datetime = None, is_rest: bool = False, 
               original_message: Optional[str] = None) -> 'Task':
        """Create new task"""
        if start_time is None:
            start_time = datetime.utcnow()
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (user_id, task_name, comment, original_message, start_time, is_rest)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (user_id, task_name, comment, original_message, start_time, is_rest))
            
            task_id = cursor.fetchone()['id']
            return cls(task_id, user_id, task_name, comment, start_time, None, is_rest, original_message)
    
    @classmethod
    def get_active_task(cls, user_id: int) -> Optional['Task']:
        """Get current active task for user"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, task_name, comment, original_message, start_time, end_time, is_rest
                FROM tasks 
                WHERE user_id = %s AND end_time IS NULL 
                ORDER BY start_time DESC LIMIT 1
            """, (user_id,))
            
            task_data = cursor.fetchone()
            if task_data:
                return cls(
                    id=task_data['id'],
                    user_id=task_data['user_id'],
                    task_name=task_data['task_name'],
                    comment=task_data['comment'],
                    start_time=task_data['start_time'],
                    end_time=task_data['end_time'],
                    is_rest=task_data['is_rest'],
                    original_message=task_data.get('original_message')
                )
            return None
    
    @classmethod
    def get_tasks_for_date(cls, user_id: int, date: datetime) -> List['Task']:
        """Get all tasks for a specific date (local time)"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get user timezone
            user = User.get_or_create(user_id)
            user_tz = pytz.timezone(user.timezone)
            
            # Convert date to user timezone range
            start_local = user_tz.localize(datetime.combine(date.date(), time.min))
            end_local = user_tz.localize(datetime.combine(date.date(), time.max))
            
            # Convert to UTC for database query
            start_utc = start_local.astimezone(pytz.utc)
            end_utc = end_local.astimezone(pytz.utc)
            
            cursor.execute("""
                SELECT id, user_id, task_name, comment, original_message, start_time, end_time, is_rest
                FROM tasks 
                WHERE user_id = %s 
                AND start_time >= %s 
                AND start_time <= %s
                ORDER BY start_time
            """, (user_id, start_utc, end_utc))
            
            tasks = []
            for task_data in cursor.fetchall():
                tasks.append(cls(
                    id=task_data['id'],
                    user_id=task_data['user_id'],
                    task_name=task_data['task_name'],
                    comment=task_data['comment'],
                    start_time=task_data['start_time'],
                    end_time=task_data['end_time'],
                    is_rest=task_data['is_rest'],
                    original_message=task_data.get('original_message')
                ))
            
            return tasks
    
    def end_task(self, end_time: datetime = None) -> bool:
        """End the task"""
        if end_time is None:
            end_time = datetime.utcnow()
        
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE tasks SET end_time = %s WHERE id = %s
                """, (end_time, self.id))
                
                self.end_time = end_time
                return True
        except Exception as e:
            logger.error(f"Error ending task: {e}")
            return False
    
    def get_duration(self) -> timedelta:
        """Get task duration"""
        end = self.end_time or datetime.utcnow()
        return end - self.start_time
    
    def update_with_same_time(self, task_name: str, comment: Optional[str] = None, 
                            original_message: Optional[str] = None) -> bool:
        """Update task when time is the same (overwrite previous)"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE tasks 
                    SET task_name = %s, comment = %s, original_message = %s 
                    WHERE id = %s
                """, (task_name, comment, original_message, self.id))
                
                self.task_name = task_name
                self.comment = comment
                self.original_message = original_message
                return True
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return False
