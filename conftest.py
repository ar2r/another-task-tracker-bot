import pytest
import os
from unittest.mock import patch, MagicMock

# Настройка тестовой среды
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Настройка переменных окружения для тестов"""
    os.environ['BOT_TOKEN'] = 'test_token'
    os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'

@pytest.fixture
def mock_database():
    """Мок базы данных для тестов"""
    with patch('models.get_db') as mock_get_db:
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value.__enter__.return_value = mock_conn
        yield mock_cursor