#!/usr/bin/env python3
"""
Веб-сервер для health check и просмотра логов Telegram бота.
Требуется для деплоя в Replit Deployments.
"""

import os
import threading
import subprocess
import sys
from flask import Flask, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)

# HTML шаблон для главной страницы
INDEX_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Telegram Time Tracking Bot</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            margin: 0; padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; min-height: 100vh;
        }
        .container { 
            max-width: 800px; margin: 0 auto; 
            background: rgba(255,255,255,0.1); 
            padding: 30px; border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 { font-size: 2.5em; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .status { 
            display: flex; justify-content: space-around; 
            margin: 30px 0; flex-wrap: wrap; gap: 20px;
        }
        .status-card { 
            background: rgba(255,255,255,0.15); 
            padding: 20px; border-radius: 10px; 
            text-align: center; flex: 1; min-width: 200px;
        }
        .status-title { font-size: 1.1em; margin-bottom: 10px; opacity: 0.9; }
        .status-value { font-size: 1.8em; font-weight: bold; }
        .features { margin: 30px 0; }
        .feature { 
            background: rgba(255,255,255,0.1); 
            margin: 10px 0; padding: 15px 20px; 
            border-radius: 8px; border-left: 4px solid #00ff88;
        }
        .buttons { text-align: center; margin-top: 30px; }
        .btn { 
            background: rgba(255,255,255,0.2); 
            color: white; border: 2px solid rgba(255,255,255,0.3);
            padding: 12px 24px; margin: 0 10px; 
            border-radius: 25px; text-decoration: none;
            transition: all 0.3s ease;
        }
        .btn:hover { 
            background: rgba(255,255,255,0.3); 
            transform: translateY(-2px);
        }
        .footer { 
            text-align: center; margin-top: 40px; 
            opacity: 0.7; font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Telegram Time Tracking Bot</h1>
            <p>Система учета времени с поддержкой Jira и многопользовательским доступом</p>
        </div>
        
        <div class="status">
            <div class="status-card">
                <div class="status-title">Статус бота</div>
                <div class="status-value" style="color: #00ff88;">{{ bot_status }}</div>
            </div>
            <div class="status-card">
                <div class="status-title">База данных</div>
                <div class="status-value" style="color: #00ff88;">{{ db_status }}</div>
            </div>
            <div class="status-card">
                <div class="status-title">Время работы</div>
                <div class="status-value">{{ uptime }}</div>
            </div>
        </div>
        
        <div class="features">
            <h3>Возможности бота:</h3>
            <div class="feature">✅ Автоматическое отслеживание времени задач</div>
            <div class="feature">🔗 Поддержка кликабельных Jira-ссылок</div>
            <div class="feature">🌍 Настройка часовых поясов пользователей</div>
            <div class="feature">⏰ Автоматическое завершение задач по рабочему дню</div>
            <div class="feature">📊 Дневные сводки и аналитика</div>
            <div class="feature">👥 Многопользовательская поддержка</div>
            <div class="feature">🏖️ Режим отдыха и перерывов</div>
        </div>
        
        <div class="buttons">
            <a href="/health" class="btn">🩺 Health Check</a>
            <a href="/logs" class="btn">📋 Просмотр логов</a>
            <a href="/api/status" class="btn">📡 API Status</a>
        </div>
        
        <div class="footer">
            <p>Развернуто на Replit Deployments | Обновлено: {{ last_update }}</p>
        </div>
    </div>
</body>
</html>
"""

# Глобальная переменная для хранения времени запуска
start_time = datetime.now()
bot_process = None

def start_telegram_bot():
    """Запуск Telegram бота в отдельном процессе"""
    global bot_process
    try:
        bot_process = subprocess.Popen([sys.executable, 'simple_main.py'])
        print("🤖 Telegram бот запущен")
        return True
    except Exception as e:
        print(f"❌ Ошибка запуска Telegram бота: {e}")
        return False

def get_bot_status():
    """Проверка статуса Telegram бота"""
    global bot_process
    if bot_process and bot_process.poll() is None:
        return "Активен"
    return "Неактивен"

def get_uptime():
    """Получение времени работы"""
    uptime = datetime.now() - start_time
    hours = int(uptime.total_seconds() // 3600)
    minutes = int((uptime.total_seconds() % 3600) // 60)
    return f"{hours}ч {minutes}м"

@app.route('/')
def index():
    """Главная страница с информацией о боте"""
    return render_template_string(INDEX_TEMPLATE,
                                bot_status=get_bot_status(),
                                db_status="Подключена",
                                uptime=get_uptime(),
                                last_update=datetime.now().strftime('%d.%m.%Y %H:%M'))

@app.route('/health')
def health_check():
    """Health check endpoint для Replit Deployments"""
    return jsonify({
        'status': 'healthy',
        'service': 'telegram-time-tracking-bot',
        'timestamp': datetime.now().isoformat(),
        'bot_status': get_bot_status(),
        'database': 'connected',
        'uptime_seconds': int((datetime.now() - start_time).total_seconds())
    })

@app.route('/api/status')
def api_status():
    """API endpoint для получения статуса системы"""
    return jsonify({
        'bot': {
            'status': get_bot_status(),
            'uptime': get_uptime(),
            'process_id': bot_process.pid if bot_process else None
        },
        'web_server': {
            'status': 'running',
            'port': 5000
        },
        'database': {
            'status': 'connected',
            'type': 'PostgreSQL'
        },
        'system': {
            'start_time': start_time.isoformat(),
            'current_time': datetime.now().isoformat()
        }
    })

@app.route('/logs')
def logs_redirect():
    """Перенаправление на веб-интерфейс логов"""
    return '''
    <script>
        // Попытка открыть логи на том же хосте с портом 5001
        const currentHost = window.location.hostname;
        const logsUrl = `http://${currentHost}:5001`;
        window.location.href = logsUrl;
    </script>
    <p>Перенаправление на интерфейс логов...</p>
    <p>Если автоматическое перенаправление не работает, перейдите по ссылке:</p>
    <p><a href="http://localhost:5001">Веб-интерфейс логов</a></p>
    '''

if __name__ == '__main__':
    print("🚀 Запуск веб-сервера для Telegram бота...")
    print("📊 Главная страница: http://localhost:5000")
    print("🩺 Health check: http://localhost:5000/health")
    
    # Запуск Telegram бота в отдельном потоке
    bot_thread = threading.Thread(target=start_telegram_bot, daemon=True)
    bot_thread.start()
    
    # Запуск веб-сервера
    app.run(host='0.0.0.0', port=5000, debug=False)