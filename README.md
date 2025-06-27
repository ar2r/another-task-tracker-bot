# Telegram Time Tracking Bot

Telegram-бот для эффективного трекинга времени задач с интеграцией Jira и расширенной аналитикой производительности.

## Возможности

- ⏰ Автоматический трекинг времени выполнения задач
- 🎯 Интеграция с Jira (распознавание ссылок и тикетов)
- 🌍 Поддержка различных часовых поясов
- 🕐 Настройка рабочего времени (автозавершение задач)
- 📊 Детальная аналитика и дневные отчеты
- 🏖️ Функция отдыха и перерывов
- 👥 Многопользовательская поддержка

## Быстрый старт

### Требования

- Python 3.11+
- PostgreSQL
- Telegram Bot Token

### Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd telegram-time-tracking-bot
```

2. Установите зависимости:
```bash
pip install python-telegram-bot psycopg2-binary pytz
```

3. Настройте переменные окружения:
```bash
export BOT_TOKEN="your_telegram_bot_token"
export DATABASE_URL="postgresql://user:password@localhost:5432/database"
```

4. Инициализируйте базу данных:
```bash
python -c "from database import init_database; init_database()"
```

5. Запустите бота:
```bash
python main.py
```

## Команды бота

- `/start` - Начать работу с ботом
- `/set_timezone <timezone>` - Установить часовой пояс (например, Europe/Moscow)
- `/set_workday <start> <end>` - Установить рабочее время (например, 09:00 18:00)

## Интерфейс

- **Отдых** - Завершить текущую задачу и начать перерыв
- **Сводка** - Показать отчет за текущий день
- **Помощь** - Список всех команд и функций

## Форматы сообщений

### Создание задач

```
Разработка функции
14:30 Код-ревью - проверка архитектуры
https://company.atlassian.net/browse/PROJ-123 - исправление бага
TASK-456 - добавление тестов
```

### Время начала

- `14:30 Название задачи` - задача с указанным временем
- `14_30 Название задачи` - альтернативный формат времени
- `Название задачи` - задача с текущим временем

## Тестирование

### Установка тестовых зависимостей

```bash
pip install pytest pytest-asyncio pytest-mock pytest-cov
```

### Запуск тестов

```bash
# Запуск всех тестов
pytest

# Запуск тестов с покрытием
pytest --cov=. --cov-report=html

# Запуск конкретного модуля
pytest tests/test_time_utils.py -v

# Запуск с подробным выводом
pytest -v --tb=short
```

### Структура тестов

```
tests/
├── __init__.py
├── test_time_utils.py      # Тесты утилит времени
├── test_task_parser.py     # Тесты парсера задач
├── test_models.py          # Тесты моделей данных
└── conftest.py            # Настройки pytest
```

### Покрытие кода

Цель проекта - поддержка покрытия тестами не менее 75%. 

Для просмотра отчета о покрытии:
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

## CI/CD

Проект настроен для автоматического тестирования в GitHub Actions:

### Конфигурации

- **Tests** (`.github/workflows/tests.yml`) - Запуск тестов с PostgreSQL
- **Code Quality** (`.github/workflows/lint.yml`) - Проверка качества кода

### Автоматические проверки

- ✅ Модульные тесты с pytest
- ✅ Покрытие кода (минимум 75%)
- ✅ Форматирование кода (Black)
- ✅ Сортировка импортов (isort)
- ✅ Стиль кода (flake8)
- ✅ Проверка типов (mypy)

### Локальная проверка перед коммитом

```bash
# Форматирование кода
black .

# Сортировка импортов
isort .

# Проверка стиля
flake8 .

# Запуск тестов
pytest
```

## Архитектура

### Модули

- `main.py` - Точка входа и конфигурация бота
- `bot_handlers.py` - Обработчики команд и сообщений Telegram
- `models.py` - Модели данных (User, Task)
- `database.py` - Подключение и управление базой данных
- `task_parser.py` - Парсинг сообщений и извлечение задач
- `time_utils.py` - Утилиты для работы с временем

### База данных

```sql
-- Пользователи
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    timezone VARCHAR(50) DEFAULT 'Europe/Moscow',
    workday_start TIME DEFAULT '09:00',
    workday_end TIME DEFAULT '18:00',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Задачи
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    task_name VARCHAR(255) NOT NULL,
    comment TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    is_rest BOOLEAN DEFAULT FALSE
);
```

## Развертывание

### Replit

1. Импортируйте проект в Replit
2. Установите переменные окружения в Secrets:
   - `BOT_TOKEN` - токен Telegram бота
   - `DATABASE_URL` - строка подключения к PostgreSQL
3. Запустите проект

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

## Лицензия

MIT License - см. LICENSE файл для деталей.

## Поддержка

Для вопросов и предложений создавайте Issues в GitHub репозитории.