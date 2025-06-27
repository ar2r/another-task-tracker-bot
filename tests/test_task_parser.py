import pytest
from task_parser import (
    extract_jira_ticket,
    parse_task_message,
    format_task_for_display,
    get_unique_comments
)


class TestExtractJiraTicket:
    """Тесты извлечения номера Jira тикета"""
    
    def test_extract_from_full_url(self):
        """Тест извлечения из полного URL"""
        url = "https://company.atlassian.net/browse/PROJ-123"
        ticket = extract_jira_ticket(url)
        assert ticket == "PROJ-123"
    
    def test_extract_from_url_with_params(self):
        """Тест извлечения из URL с параметрами"""
        url = "https://jira.example.com/browse/TASK-456?filter=all"
        ticket = extract_jira_ticket(url)
        assert ticket == "TASK-456"
    
    def test_extract_from_ticket_in_text(self):
        """Тест извлечения номера тикета из текста"""
        text = "Работа над PROJ-789 сегодня"
        ticket = extract_jira_ticket(text)
        assert ticket == "PROJ-789"
    
    def test_extract_multiple_tickets_returns_first(self):
        """Тест что возвращается первый найденный тикет"""
        text = "PROJ-123 и TASK-456"
        ticket = extract_jira_ticket(text)
        assert ticket == "PROJ-123"
    
    def test_no_ticket_found(self):
        """Тест когда тикет не найден"""
        text = "Обычная задача без тикета"
        ticket = extract_jira_ticket(text)
        assert ticket is None
    
    def test_invalid_ticket_format(self):
        """Тест невалидного формата тикета"""
        text = "INVALID-FORMAT"
        ticket = extract_jira_ticket(text)
        assert ticket is None


class TestParseTaskMessage:
    """Тесты парсинга сообщений с задачами"""
    
    def test_simple_task_name(self):
        """Тест простого названия задачи"""
        message = "Разработка новой функции"
        task_name, comment, is_jira = parse_task_message(message)
        
        assert task_name == "Разработка новой функции"
        assert comment is None
        assert is_jira is False
    
    def test_task_with_comment(self):
        """Тест задачи с комментарием"""
        message = "Код-ревью - проверка архитектуры"
        task_name, comment, is_jira = parse_task_message(message)
        
        assert task_name == "Код-ревью"
        assert comment == "проверка архитектуры"
        assert is_jira is False
    
    def test_jira_url_parsing(self):
        """Тест парсинга Jira URL"""
        message = "https://company.atlassian.net/browse/PROJ-123 - исправление бага"
        task_name, comment, is_jira = parse_task_message(message)
        
        assert task_name == "PROJ-123"
        assert comment == "исправление бага"
        assert is_jira is True
    
    def test_jira_url_without_comment(self):
        """Тест Jira URL без комментария"""
        message = "https://jira.example.com/browse/TASK-456"
        task_name, comment, is_jira = parse_task_message(message)
        
        assert task_name == "TASK-456"
        assert comment is None
        assert is_jira is True
    
    def test_jira_ticket_in_text(self):
        """Тест тикета Jira в тексте"""
        message = "Работа над PROJ-789 - добавление тестов"
        task_name, comment, is_jira = parse_task_message(message)
        
        assert task_name == "PROJ-789"
        assert comment == "добавление тестов"
        assert is_jira is True
    
    def test_task_with_multiple_dashes(self):
        """Тест задачи с несколькими дефисами"""
        message = "Длинная задача - с - несколькими - дефисами"
        task_name, comment, is_jira = parse_task_message(message)
        
        assert task_name == "Длинная задача"
        assert comment == "с - несколькими - дефисами"
        assert is_jira is False
    
    def test_empty_message(self):
        """Тест пустого сообщения"""
        message = ""
        task_name, comment, is_jira = parse_task_message(message)
        
        assert task_name == ""
        assert comment is None
        assert is_jira is False
    
    def test_whitespace_handling(self):
        """Тест обработки пробелов"""
        message = "  Задача с пробелами  -  комментарий  "
        task_name, comment, is_jira = parse_task_message(message)
        
        assert task_name == "Задача с пробелами"
        assert comment == "комментарий"
        assert is_jira is False


class TestFormatTaskForDisplay:
    """Тесты форматирования задач для отображения"""
    
    def test_format_regular_task(self):
        """Тест форматирования обычной задачи"""
        task_name = "Разработка функции"
        formatted = format_task_for_display(task_name)
        assert formatted == "**Разработка функции**"
    
    def test_format_jira_task_explicit(self):
        """Тест форматирования Jira задачи (явное указание)"""
        task_name = "PROJ-123"
        formatted = format_task_for_display(task_name, is_jira=True)
        assert formatted == "**PROJ-123**"
    
    def test_format_jira_task_auto_detect(self):
        """Тест автоопределения Jira задачи"""
        task_name = "TASK-456"
        formatted = format_task_for_display(task_name)
        # Должно автоматически определить как Jira по формату
        assert "TASK-456" in formatted
    
    def test_format_long_task_name(self):
        """Тест форматирования длинного названия задачи"""
        task_name = "Очень длинное название задачи которое может не поместиться"
        formatted = format_task_for_display(task_name)
        assert task_name in formatted
        assert "**" in formatted  # Проверяем что форматирование применилось
    
    def test_format_task_with_special_characters(self):
        """Тест форматирования задачи со спецсимволами"""
        task_name = "Задача с символами: !@#$%^&*()"
        formatted = format_task_for_display(task_name)
        assert task_name in formatted


class TestGetUniqueComments:
    """Тесты получения уникальных комментариев"""
    
    def create_mock_task(self, comment):
        """Создание мок-задачи с комментарием"""
        class MockTask:
            def __init__(self, comment):
                self.comment = comment
        return MockTask(comment)
    
    def test_unique_comments_no_duplicates(self):
        """Тест уникальных комментариев без дубликатов"""
        tasks = [
            self.create_mock_task("Комментарий 1"),
            self.create_mock_task("Комментарий 2"),
            self.create_mock_task("Комментарий 3")
        ]
        
        unique_comments = get_unique_comments(tasks)
        
        assert len(unique_comments) == 3
        assert "Комментарий 1" in unique_comments
        assert "Комментарий 2" in unique_comments
        assert "Комментарий 3" in unique_comments
    
    def test_unique_comments_with_duplicates(self):
        """Тест уникальных комментариев с дубликатами"""
        tasks = [
            self.create_mock_task("Комментарий 1"),
            self.create_mock_task("Комментарий 2"),
            self.create_mock_task("Комментарий 1"),  # Дубликат
            self.create_mock_task("Комментарий 3")
        ]
        
        unique_comments = get_unique_comments(tasks)
        
        assert len(unique_comments) == 3
        assert unique_comments.count("Комментарий 1") == 1
    
    def test_unique_comments_with_none_values(self):
        """Тест уникальных комментариев с None значениями"""
        tasks = [
            self.create_mock_task("Комментарий 1"),
            self.create_mock_task(None),
            self.create_mock_task("Комментарий 2"),
            self.create_mock_task(None)
        ]
        
        unique_comments = get_unique_comments(tasks)
        
        # None значения должны быть отфильтрованы
        assert len(unique_comments) == 2
        assert "Комментарий 1" in unique_comments
        assert "Комментарий 2" in unique_comments
        assert None not in unique_comments
    
    def test_unique_comments_empty_list(self):
        """Тест пустого списка задач"""
        tasks = []
        unique_comments = get_unique_comments(tasks)
        assert unique_comments == []
    
    def test_unique_comments_all_none(self):
        """Тест когда все комментарии None"""
        tasks = [
            self.create_mock_task(None),
            self.create_mock_task(None),
            self.create_mock_task(None)
        ]
        
        unique_comments = get_unique_comments(tasks)
        assert unique_comments == []
    
    def test_unique_comments_case_sensitivity(self):
        """Тест чувствительности к регистру"""
        tasks = [
            self.create_mock_task("комментарий"),
            self.create_mock_task("Комментарий"),
            self.create_mock_task("КОММЕНТАРИЙ")
        ]
        
        unique_comments = get_unique_comments(tasks)
        
        # Должны рассматриваться как разные комментарии
        assert len(unique_comments) == 3