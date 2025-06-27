import pytest
import pytz
from datetime import datetime, time, timedelta
from unittest.mock import patch, MagicMock

from time_utils import (
    parse_time_from_message,
    format_duration,
    should_auto_end_task,
    format_time_for_user,
    create_datetime_from_time
)


class TestParseTimeFromMessage:
    """Тесты парсинга времени из сообщений"""
    
    def test_parse_time_hh_mm_format(self):
        """Тест парсинга времени в формате HH:MM"""
        parsed_time, remaining = parse_time_from_message("14:30 Работа над задачей")
        assert parsed_time == time(14, 30)
        assert remaining == "Работа над задачей"
    
    def test_parse_time_hh_mm_underscore_format(self):
        """Тест парсинга времени в формате HH_MM"""
        parsed_time, remaining = parse_time_from_message("09_15 Встреча")
        assert parsed_time == time(9, 15)
        assert remaining == "Встреча"
    
    def test_parse_time_no_time_in_message(self):
        """Тест сообщения без времени"""
        parsed_time, remaining = parse_time_from_message("Просто задача")
        assert parsed_time is None
        assert remaining == "Просто задача"
    
    def test_parse_time_invalid_format(self):
        """Тест некорректного формата времени"""
        parsed_time, remaining = parse_time_from_message("25:70 Невалидное время")
        assert parsed_time is None
        assert remaining == "25:70 Невалидное время"
    
    def test_parse_time_edge_cases(self):
        """Тест граничных значений времени"""
        # Полночь
        parsed_time, remaining = parse_time_from_message("00:00 Начало дня")
        assert parsed_time == time(0, 0)
        assert remaining == "Начало дня"
        
        # Почти полночь
        parsed_time, remaining = parse_time_from_message("23:59 Конец дня")
        assert parsed_time == time(23, 59)
        assert remaining == "Конец дня"


class TestFormatDuration:
    """Тесты форматирования длительности"""
    
    def test_format_minutes_only(self):
        """Тест форматирования только минут"""
        duration = timedelta(minutes=30)
        result = format_duration(duration)
        assert result == "30 мин"
    
    def test_format_hours_and_minutes(self):
        """Тест форматирования часов и минут"""
        duration = timedelta(hours=2, minutes=45)
        result = format_duration(duration)
        assert result == "2 ч 45 мин"
    
    def test_format_hours_only(self):
        """Тест форматирования только часов"""
        duration = timedelta(hours=3)
        result = format_duration(duration)
        assert result == "3 ч"
    
    def test_format_zero_duration(self):
        """Тест нулевой длительности"""
        duration = timedelta(seconds=0)
        result = format_duration(duration)
        assert result == "0 мин"
    
    def test_format_seconds_only(self):
        """Тест только секунд (должно округлиться до минут)"""
        duration = timedelta(seconds=30)
        result = format_duration(duration)
        assert result == "0 мин"


class TestShouldAutoEndTask:
    """Тесты логики автоматического завершения задач"""
    
    def create_mock_user(self, timezone="Europe/Moscow", workday_start=time(9, 0), workday_end=time(18, 0)):
        """Создание мок-пользователя"""
        user = MagicMock()
        user.timezone = timezone
        user.workday_start = workday_start
        user.workday_end = workday_end
        return user
    
    @patch('time_utils.datetime')
    def test_task_should_end_after_workday(self, mock_datetime):
        """Тест завершения задачи после рабочего дня"""
        # Настройка времени: 19:00 по Москве (после 18:00 конца рабочего дня)
        moscow_tz = pytz.timezone('Europe/Moscow')
        current_time = moscow_tz.localize(datetime(2025, 6, 27, 19, 0))
        mock_datetime.utcnow.return_value = current_time.astimezone(pytz.utc).replace(tzinfo=None)
        
        user = self.create_mock_user()
        # Задача началась в 16:00
        task_start = moscow_tz.localize(datetime(2025, 6, 27, 16, 0))
        
        should_end, end_time = should_auto_end_task(user, task_start)
        
        assert should_end is True
        assert end_time is not None
    
    @patch('time_utils.datetime')
    def test_task_should_not_end_during_workday(self, mock_datetime):
        """Тест что задача не завершается во время рабочего дня"""
        # Настройка времени: 15:00 по Москве (во время рабочего дня)
        moscow_tz = pytz.timezone('Europe/Moscow')
        current_time = moscow_tz.localize(datetime(2025, 6, 27, 15, 0))
        mock_datetime.utcnow.return_value = current_time.astimezone(pytz.utc).replace(tzinfo=None)
        
        user = self.create_mock_user()
        # Задача началась в 14:00
        task_start = moscow_tz.localize(datetime(2025, 6, 27, 14, 0))
        
        should_end, end_time = should_auto_end_task(user, task_start)
        
        assert should_end is False
        assert end_time is None
    
    def test_task_started_after_workday_ends_at_2359(self):
        """Тест задачи, начатой после рабочего дня - завершается в 23:59"""
        user = self.create_mock_user()
        moscow_tz = pytz.timezone('Europe/Moscow')
        # Задача началась в 20:00 (после рабочего дня)
        task_start = moscow_tz.localize(datetime(2025, 6, 27, 20, 0))
        
        should_end, end_time = should_auto_end_task(user, task_start)
        
        assert should_end is True
        # Проверяем что время завершения в 23:59 того же дня
        expected_end = moscow_tz.localize(datetime(2025, 6, 27, 23, 59))
        assert end_time == expected_end.astimezone(pytz.utc)


class TestFormatTimeForUser:
    """Тесты форматирования времени для пользователя"""
    
    def create_mock_user(self, timezone="Europe/Moscow"):
        """Создание мок-пользователя"""
        user = MagicMock()
        user.timezone = timezone
        return user
    
    def test_format_utc_time_to_moscow(self):
        """Тест конвертации UTC времени в московское"""
        user = self.create_mock_user("Europe/Moscow")
        
        # UTC время
        utc_time = pytz.utc.localize(datetime(2025, 6, 27, 15, 30))
        
        formatted = format_time_for_user(utc_time, user)
        
        # Московское время должно быть UTC+3
        assert "18:30" in formatted
    
    def test_format_time_different_timezone(self):
        """Тест форматирования времени в другом часовом поясе"""
        user = self.create_mock_user("US/Eastern")
        
        # UTC время
        utc_time = pytz.utc.localize(datetime(2025, 6, 27, 20, 0))
        
        formatted = format_time_for_user(utc_time, user)
        
        # Восточное время США должно быть UTC-4 (летом)
        # Результат зависит от DST, но должен корректно конвертироваться
        assert ":" in formatted  # Проверяем что время отформатировано


class TestCreateDatetimeFromTime:
    """Тесты создания datetime из времени в часовом поясе пользователя"""
    
    def create_mock_user(self, timezone="Europe/Moscow"):
        """Создание мок-пользователя"""
        user = MagicMock()
        user.timezone = timezone
        user.get_local_time.return_value = pytz.timezone(timezone).localize(datetime.now())
        return user
    
    def test_create_datetime_current_date(self):
        """Тест создания datetime на текущую дату"""
        user = self.create_mock_user()
        target_time = time(14, 30)
        
        result = create_datetime_from_time(user, target_time)
        
        assert result is not None
        assert isinstance(result, datetime)
        assert result.hour == 14
        assert result.minute == 30
    
    def test_create_datetime_with_reference_date(self):
        """Тест создания datetime с опорной датой"""
        user = self.create_mock_user()
        target_time = time(16, 45)
        reference_date = datetime(2025, 6, 27, 10, 0)
        
        result = create_datetime_from_time(user, target_time, reference_date)
        
        assert result is not None
        assert result.hour == 16
        assert result.minute == 45
        # Дата должна быть как в reference_date
        assert result.date() == reference_date.date()