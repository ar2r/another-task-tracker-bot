# 🚀 Руководство по деплою Telegram бота в Replit

## Проблема с деплоем

Replit Deployments требует веб-сервер с HTTP endpoints для health check. Telegram бот работает через long polling, поэтому нужен дополнительный веб-сервер.

## Решения

### Вариант 1: Основной (рекомендуемый)

Используйте `health_server.py` - минимальный Flask сервер только для health check:

```bash
# Основной файл для деплоя
python health_server.py
```

**Endpoints:**
- `GET /` - информация о сервисе
- `GET /health` - health check для Replit
- `GET /status` - статус конфигурации

### Вариант 2: Полнофункциональный

Используйте `web_server.py` - полноценный веб-интерфейс с запуском бота:

```bash
# Веб-сервер + Telegram бот
python web_server.py
```

### Вариант 3: Раздельный запуск

Запустите два отдельных процесса:

```bash
# Процесс 1: Telegram бот
python simple_main.py

# Процесс 2: Веб-интерфейс логов  
python log_viewer.py
```

## Конфигурация для деплоя

### Replit Deployment Settings

1. **Main Command**: `python health_server.py`
2. **Port**: 5000
3. **Environment Variables**:
   - `BOT_TOKEN` - токен Telegram бота
   - `DATABASE_URL` - URL базы данных PostgreSQL

### Структура проекта

```
📁 telegram-bot/
├── 📄 health_server.py     # Health check сервер (для деплоя)
├── 📄 web_server.py        # Полный веб-интерфейс
├── 📄 simple_main.py       # Основной Telegram бот
├── 📄 log_viewer.py        # Веб-интерфейс логов
├── 📄 models.py            # Модели данных
├── 📄 database.py          # Работа с БД
├── 📄 task_parser.py       # Парсинг задач
├── 📄 time_utils.py        # Утилиты времени
└── 📁 logs/                # Файлы логов
```

## Пошаговая инструкция деплоя

### Шаг 1: Подготовка
1. Убедитесь, что все файлы загружены в Replit
2. Установите переменные окружения `BOT_TOKEN` и `DATABASE_URL`
3. Проверьте зависимости в `pyproject.toml`

### Шаг 2: Локальное тестирование
```bash
# Тест health сервера
python health_server.py

# Проверка endpoints
curl http://localhost:5000/health
```

### Шаг 3: Деплой
1. Откройте раздел "Deploy" в Replit
2. Выберите "Autoscale deployment"
3. Установите команду: `python health_server.py`
4. Нажмите "Deploy"

### Шаг 4: Проверка
После деплоя проверьте:
- `https://your-app.replit.app/health` - health check
- `https://your-app.replit.app/status` - статус конфигурации

## Запуск Telegram бота после деплоя

После успешного деплоя health сервера запустите бота отдельно:

### Вариант A: Через Replit Console
```bash
python simple_main.py
```

### Вариант B: Через дополнительный воркфлоу
Создайте второй Replit процесс для бота (без wait_for_port).

## Мониторинг и логи

### Просмотр логов бота
1. **Файлы**: логи сохраняются в `logs/telegram_bot.log`
2. **Веб-интерфейс**: запустите `python log_viewer.py` на порту 5001
3. **Консоль**: логи видны при запуске `python simple_main.py`

### Health check endpoints

#### GET /health
```json
{
  "status": "healthy",
  "timestamp": "2025-06-27T19:30:00"
}
```

#### GET /status
```json
{
  "service": "running", 
  "uptime": "0:15:30",
  "bot_token_configured": true
}
```

## Устранение неполадок

### "Health check failure"
**Причина**: Replit не может получить доступ к health endpoint
**Решение**: 
- Убедитесь, что используете `health_server.py`
- Проверьте, что сервер слушает на `0.0.0.0:5000`
- Протестируйте локально: `curl http://localhost:5000/health`

### "No web server is running"
**Причина**: Приложение не отвечает на HTTP запросы
**Решение**:
- Используйте Flask сервер вместо простого Python скрипта
- Проверьте, что порт 5000 открыт и доступен

### "Missing HTTP endpoint implementation"
**Причина**: Отсутствует корневой endpoint
**Решение**:
- Добавьте `@app.route('/')` в Flask приложение
- Убедитесь, что endpoint возвращает HTTP 200

### Бот не отвечает на сообщения
**Причина**: Бот не запущен или нет токена
**Решение**:
- Проверьте переменную окружения `BOT_TOKEN`
- Запустите `python simple_main.py` в отдельном процессе
- Проверьте логи: `tail -f logs/telegram_bot.log`

## Альтернативные платформы

Если деплой в Replit не работает, рассмотрите альтернативы:

1. **Railway**: поддерживает background процессы
2. **Render**: бесплатный tier для веб-сервисов
3. **Heroku**: классическое решение для деплоя
4. **DigitalOcean App Platform**: простой деплой

## Производственная конфигурация

Для production деплоя:

1. **Используйте Gunicorn** вместо development сервера Flask:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 health_server:app
   ```

2. **Переменные окружения**:
   - `FLASK_ENV=production`
   - `PYTHONPATH=.`

3. **Мониторинг**:
   - Настройте алерты на health check
   - Логирование в external сервис (например, Papertrail)

4. **Безопасность**:
   - HTTPS only
   - Ограничение доступа к логам
   - Rate limiting для API endpoints

## Заключение

Самый надежный способ деплоя:
1. Запустите `health_server.py` для health check
2. Запустите `simple_main.py` в background для Telegram бота
3. Используйте `log_viewer.py` для мониторинга

Это обеспечит стабильную работу в Replit Deployments.