# Telegram Time Tracking Bot

## Overview

This is a Telegram bot built in Python that helps users track time spent on tasks. The bot supports Jira link integration, timezone management, and provides daily summaries of work activities. Users can start tasks, track time automatically, and get insights into their productivity.

## System Architecture

The application follows a modular architecture with clear separation of concerns:

- **Bot Layer**: Handles Telegram interactions and user commands
- **Business Logic Layer**: Processes task parsing, time calculations, and user preferences
- **Data Layer**: PostgreSQL database with ORM-like model classes
- **Utility Layer**: Time parsing, formatting, and task management utilities

## Key Components

### 1. Bot Handlers (`bot_handlers.py`)
- **Purpose**: Manages all Telegram bot interactions
- **Key Features**:
  - Command handlers for `/start`, timezone, and workday settings
  - Button handlers for "Отдых" (Rest) and "Сводка" (Summary)
  - Task message processing and time tracking
  - Auto-end tasks background job
- **Architecture Decision**: Separates UI logic from business logic for maintainability

### 2. Database Layer (`database.py`)
- **Purpose**: PostgreSQL connection management and schema initialization
- **Key Features**:
  - Connection pooling with context managers
  - Automatic table creation and migration
  - Error handling and transaction management
- **Architecture Decision**: Uses raw PostgreSQL with psycopg2 for direct control over queries

### 3. Models (`models.py`)
- **Purpose**: Data models for Users and Tasks
- **Key Features**:
  - User management with timezone and workday preferences
  - Task tracking with time logging and status management
  - Active task management and statistics calculation
- **Architecture Decision**: ORM-like pattern without heavy framework dependency

### 4. Task Parser (`task_parser.py`)
- **Purpose**: Parses user input to extract task information
- **Key Features**:
  - Jira URL detection and ticket extraction
  - Task name and comment separation
  - Flexible input format support
- **Architecture Decision**: Regex-based parsing for reliability and performance

### 5. Time Utils (`time_utils.py`)
- **Purpose**: Time parsing, formatting, and timezone handling
- **Key Features**:
  - Multiple time format support (14:00, 14_00)
  - Duration formatting for user display
  - Workday boundary calculations
  - Timezone-aware datetime operations
- **Architecture Decision**: Comprehensive time handling to support global users

### 6. Main Application (`main.py`)
- **Purpose**: Application entry point and bot configuration
- **Key Features**:
  - Bot initialization and handler registration
  - Background job scheduling
  - Logging configuration
- **Architecture Decision**: Centralized configuration for easy deployment management

## Data Flow

1. **User Input**: User sends message to Telegram bot
2. **Message Processing**: Bot handlers parse and route the message
3. **Task Parsing**: Extract task information and time data
4. **Database Operations**: Store/update task and user information
5. **Response Generation**: Format and send response back to user
6. **Background Processing**: Auto-end tasks based on workday settings

## External Dependencies

- **python-telegram-bot**: Telegram Bot API wrapper
- **psycopg2**: PostgreSQL database adapter
- **pytz**: Timezone handling
- **logging**: Built-in Python logging
- **re**: Regular expressions for parsing
- **datetime**: Date and time operations

## Deployment Strategy

- **Platform**: Replit hosting
- **Database**: PostgreSQL (external or Replit-provided)
- **Environment Variables**: 
  - `BOT_TOKEN`: Telegram bot token
  - `DATABASE_URL`: PostgreSQL connection string
- **Background Jobs**: Scheduled task auto-ending every 5 minutes
- **Error Handling**: Comprehensive logging and graceful error recovery

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

- June 27, 2025: Полностью создан и настроен Telegram бот для трекинга времени
  - Реализованы все основные функции согласно требованиям
  - База данных PostgreSQL настроена и инициализирована  
  - Бот успешно запущен и готов к использованию
  - Поддержка Jira-ссылок, часовых поясов, рабочего времени
  - Автоматическое завершение задач по окончании рабочего дня
  - Многопользовательская поддержка
  
- June 27, 2025: Исправлены ошибки с часовыми поясами и установлены настройки по умолчанию
  - Исправлена ошибка "can't subtract offset-naive and offset-aware datetimes" 
  - Установлен часовой пояс Europe/Moscow по умолчанию для новых пользователей
  - Установлено рабочее время 9:00-18:00 по умолчанию
  - Функция format_time_for_user теперь корректно работает с часовыми поясами
  - Планировщик автоматического завершения задач работает без ошибок
  - Добавлена кнопка "Помощь" со списком всех доступных команд и функций бота

- June 27, 2025: Создано подробное техническое задание и система автотестов
  - Создан TZ.md с 80+ детализированными требованиями для системы
  - Разработан полный набор автотестов с pytest для всех ключевых модулей
  - Настроен CI/CD pipeline в GitHub Actions для автоматического тестирования
  - Добавлена проверка качества кода с Black, isort, flake8, mypy
  - Созданы тесты для time_utils, task_parser, models с мокированием БД
  - Настроено покрытие кода с целевым показателем 75%
  - Добавлен README.md с инструкциями по запуску и тестированию

- June 27, 2025: Создана полная русскоязычная документация проекта
  - Написан исчерпывающий README.md на русском языке с разделами:
    - Подробное описание возможностей бота с эмодзи и примерами
    - Пошаговые инструкции по установке и настройке
    - Руководство пользователя с примерами команд и форматов
    - Техническая документация для разработчиков 
    - Информация о тестировании и CI/CD
    - Схема базы данных и архитектура проекта
    - Инструкции по развертыванию и поддержке
  - Документация содержит практические примеры использования
  - Добавлены реальные примеры дневных отчетов и взаимодействия с ботом

- June 27, 2025: Решена проблема с зависимостями и успешно запущен Telegram бот
  - Устранен конфликт зависимостей между пакетами python-telegram-bot и telegram
  - Переход на pyTelegramBotAPI (telebot) для стабильной работы без конфликтов
  - Создан simple_main.py - упрощенная и стабильная версия бота
  - Бот успешно запущен и готов к работе с пользователями
  - Все основные функции реализованы: создание задач, отдых, сводки, настройки
  - База данных PostgreSQL инициализирована и работает корректно
  - Многопользовательская система с поддержкой часовых поясов активна

- June 27, 2025: Завершена реализация кликабельных Jira-ссылок в Telegram боте
  - Добавлено поле original_message в таблицу tasks для сохранения оригинального текста
  - Обновлены все SQL-запросы и модели для работы с новым полем
  - Реализована функция format_task_for_display с поддержкой кликабельных ссылок
  - Jira URL автоматически конвертируются в формат [TASK-123](https://jira.../TASK-123)
  - Номера задач (PROJ-123) автоматически становятся кликабельными ссылками
  - Функциональность протестирована и работает корректно в сводках и текущих задачах
  - Бот стабильно работает, база данных инициализирована, все тесты проходят

- June 27, 2025: Добавлено полное логирование активности пользователей
  - Создана centralized функция log_user_request для единообразного логирования
  - Добавлено логирование во все команды: /start, /set_timezone, /set_workday
  - Добавлено логирование во все кнопки: "Отдых", "Сводка", "Помощь"  
  - Добавлено логирование при создании задач через текстовые сообщения
  - Логи включают полную информацию о пользователе: ID, имя, username, тип действия
  - Вся активность пользователей теперь отслеживается в консоли для мониторинга
  - Система логирования помогает анализировать использование бота и выявлять проблемы

- June 27, 2025: Настроена система логирования для деплоя с веб-интерфейсом
  - Добавлено файловое логирование с ротацией в папку logs/telegram_bot.log
  - Создан веб-интерфейс log_viewer.py для просмотра логов через браузер на порту 5000
  - Логи сохраняются в UTF-8 с автоматической ротацией файлов (10MB, 5 копий)
  - Веб-интерфейс поддерживает автообновление, фильтрацию, скачивание и очистку логов
  - Создан комбинированный скрипт main_with_logs.py для запуска бота и веб-сервера
  - Добавлена подробная документация DEPLOYMENT_LOGS.md с инструкциями
  - Настроены два воркфлоу: Telegram Bot и Log Viewer для полного мониторинга

## Changelog

- June 27, 2025: Initial setup and complete implementation