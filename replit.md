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

## Changelog

- June 27, 2025: Initial setup and complete implementation