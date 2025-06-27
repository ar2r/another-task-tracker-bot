import pytest
import pytz
from datetime import datetime, time, timedelta
from unittest.mock import patch, MagicMock

from models import User, Task


class TestUser:
    """Тесты модели пользователя"""
    
    def test_user_init_default_values(self):
        """Тест инициализации пользователя с значениями по умолчанию"""
        user = User(user_id=12345)
        
        assert user.user_id == 12345
        assert user.timezone == 'Europe/Moscow'
        assert user.workday_start == time(9, 0)
        assert user.workday_end == time(18, 0)
    
    def test_user_init_custom_values(self):
        """Тест инициализации пользователя с кастомными значениями"""
        user = User(
            user_id=67890,
            timezone='US/Eastern',
            workday_start=time(8, 30),
            workday_end=time(17, 30)
        )
        
        assert user.user_id == 67890
        assert user.timezone == 'US/Eastern'
        assert user.workday_start == time(8, 30)
        assert user.workday_end == time(17, 30)
    
    @patch('models.get_db')
    def test_get_or_create_existing_user(self, mock_get_db):
        """Тест получения существующего пользователя"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'user_id': 12345,
            'timezone': 'Europe/Moscow',
            'workday_start': time(9, 0),
            'workday_end': time(18, 0)
        }
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        user = User.get_or_create(12345)
        
        assert user.user_id == 12345
        assert user.timezone == 'Europe/Moscow'
        mock_cursor.execute.assert_called_once()
    
    @patch('models.get_db')
    def test_get_or_create_new_user(self, mock_get_db):
        """Тест создания нового пользователя"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            None,  # Пользователь не найден
            {
                'user_id': 12345,
                'timezone': 'Europe/Moscow',
                'workday_start': time(9, 0),
                'workday_end': time(18, 0)
            }
        ]
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        user = User.get_or_create(12345)
        
        assert user.user_id == 12345
        assert mock_cursor.execute.call_count == 2  # SELECT + INSERT
    
    @patch('models.get_db')
    def test_update_timezone_valid(self, mock_get_db):
        """Тест обновления валидного часового пояса"""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        user = User(12345)
        result = user.update_timezone('US/Pacific')
        
        assert result is True
        assert user.timezone == 'US/Pacific'
        mock_cursor.execute.assert_called_once()
    
    def test_update_timezone_invalid(self):
        """Тест обновления невалидного часового пояса"""
        user = User(12345)
        result = user.update_timezone('Invalid/Timezone')
        
        assert result is False
        assert user.timezone == 'Europe/Moscow'  # Должен остаться без изменений
    
    @patch('models.get_db')
    def test_update_workday(self, mock_get_db):
        """Тест обновления рабочего дня"""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        user = User(12345)
        result = user.update_workday(time(8, 0), time(17, 0))
        
        assert result is True
        assert user.workday_start == time(8, 0)
        assert user.workday_end == time(17, 0)
        mock_cursor.execute.assert_called_once()
    
    def test_get_local_time_default(self):
        """Тест получения местного времени (текущее время)"""
        user = User(12345, timezone='Europe/Moscow')
        local_time = user.get_local_time()
        
        assert isinstance(local_time, datetime)
        assert local_time.tzinfo is not None
    
    def test_get_local_time_with_utc_input(self):
        """Тест конвертации UTC времени в местное"""
        user = User(12345, timezone='Europe/Moscow')
        utc_time = pytz.utc.localize(datetime(2025, 6, 27, 15, 30))
        
        local_time = user.get_local_time(utc_time)
        
        # Московское время должно быть UTC+3
        assert local_time.hour == 18
        assert local_time.minute == 30
    
    def test_get_utc_time(self):
        """Тест конвертации местного времени в UTC"""
        user = User(12345, timezone='Europe/Moscow')
        moscow_tz = pytz.timezone('Europe/Moscow')
        local_time = moscow_tz.localize(datetime(2025, 6, 27, 18, 30))
        
        utc_time = user.get_utc_time(local_time)
        
        # UTC время должно быть московское время - 3 часа
        assert utc_time.hour == 15
        assert utc_time.minute == 30


class TestTask:
    """Тесты модели задачи"""
    
    def test_task_init_minimal(self):
        """Тест инициализации задачи с минимальными параметрами"""
        start_time = datetime.utcnow()
        task = Task(
            id=1,
            user_id=12345,
            task_name="Тестовая задача",
            comment=None,
            start_time=start_time
        )
        
        assert task.id == 1
        assert task.user_id == 12345
        assert task.task_name == "Тестовая задача"
        assert task.comment is None
        assert task.start_time == start_time
        assert task.end_time is None
        assert task.is_rest is False
    
    def test_task_init_full(self):
        """Тест инициализации задачи со всеми параметрами"""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)
        
        task = Task(
            id=2,
            user_id=67890,
            task_name="Полная задача",
            comment="Тестовый комментарий",
            start_time=start_time,
            end_time=end_time,
            is_rest=True
        )
        
        assert task.id == 2
        assert task.user_id == 67890
        assert task.task_name == "Полная задача"
        assert task.comment == "Тестовый комментарий"
        assert task.start_time == start_time
        assert task.end_time == end_time
        assert task.is_rest is True
    
    @patch('models.get_db')
    def test_create_task_minimal(self, mock_get_db):
        """Тест создания задачи с минимальными параметрами"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'user_id': 12345,
            'task_name': 'Новая задача',
            'comment': None,
            'start_time': datetime.utcnow(),
            'end_time': None,
            'is_rest': False
        }
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        task = Task.create(
            user_id=12345,
            task_name="Новая задача"
        )
        
        assert task.user_id == 12345
        assert task.task_name == "Новая задача"
        mock_cursor.execute.assert_called()
    
    @patch('models.get_db')
    def test_get_active_task_exists(self, mock_get_db):
        """Тест получения активной задачи, когда она существует"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'user_id': 12345,
            'task_name': 'Активная задача',
            'comment': None,
            'start_time': datetime.utcnow(),
            'end_time': None,
            'is_rest': False
        }
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        task = Task.get_active_task(12345)
        
        assert task is not None
        assert task.task_name == "Активная задача"
        assert task.end_time is None
    
    @patch('models.get_db')
    def test_get_active_task_none(self, mock_get_db):
        """Тест получения активной задачи, когда её нет"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        task = Task.get_active_task(12345)
        
        assert task is None
    
    @patch('models.get_db')
    def test_get_tasks_for_date(self, mock_get_db):
        """Тест получения задач за определенную дату"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'id': 1,
                'user_id': 12345,
                'task_name': 'Задача 1',
                'comment': None,
                'start_time': datetime.utcnow(),
                'end_time': None,
                'is_rest': False
            },
            {
                'id': 2,
                'user_id': 12345,
                'task_name': 'Задача 2',
                'comment': 'Комментарий',
                'start_time': datetime.utcnow(),
                'end_time': datetime.utcnow(),
                'is_rest': True
            }
        ]
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        tasks = Task.get_tasks_for_date(12345, datetime.now())
        
        assert len(tasks) == 2
        assert tasks[0].task_name == "Задача 1"
        assert tasks[1].task_name == "Задача 2"
        assert tasks[1].is_rest is True
    
    @patch('models.get_db')
    def test_end_task(self, mock_get_db):
        """Тест завершения задачи"""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        start_time = datetime.utcnow()
        task = Task(1, 12345, "Задача", None, start_time)
        
        end_time = start_time + timedelta(hours=1)
        result = task.end_task(end_time)
        
        assert result is True
        assert task.end_time == end_time
        mock_cursor.execute.assert_called_once()
    
    def test_get_duration_not_ended(self):
        """Тест получения длительности незавершенной задачи"""
        start_time = datetime.utcnow() - timedelta(minutes=30)
        task = Task(1, 12345, "Задача", None, start_time)
        
        duration = task.get_duration()
        
        # Задача выполняется ~30 минут
        assert duration.total_seconds() >= 30 * 60 - 10  # Небольшая погрешность
        assert duration.total_seconds() <= 30 * 60 + 10
    
    def test_get_duration_ended(self):
        """Тест получения длительности завершенной задачи"""
        start_time = datetime.utcnow() - timedelta(hours=2)
        end_time = start_time + timedelta(hours=1, minutes=30)
        task = Task(1, 12345, "Задача", None, start_time, end_time)
        
        duration = task.get_duration()
        
        # Задача выполнялась 1.5 часа
        assert duration == timedelta(hours=1, minutes=30)
    
    @patch('models.get_db')
    def test_update_with_same_time(self, mock_get_db):
        """Тест обновления задачи с тем же временем"""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        task = Task(1, 12345, "Старая задача", None, datetime.utcnow())
        result = task.update_with_same_time("Новая задача", "Новый комментарий")
        
        assert result is True
        assert task.task_name == "Новая задача"
        assert task.comment == "Новый комментарий"
        mock_cursor.execute.assert_called_once()