#!/usr/bin/env python3
"""
Упрощенный веб-сервер для деплоя в Replit Deployments.
Предоставляет health check endpoint и запускает Telegram бота в фоне.
"""

import os
import threading
import subprocess
import sys
from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

# Глобальные переменные
start_time = datetime.now()
bot_process = None
bot_started = False

def start_telegram_bot():
    """Запуск Telegram бота в отдельном процессе (асинхронно)"""
    global bot_process, bot_started
    try:
        print("🤖 Запуск Telegram бота...")
        bot_process = subprocess.Popen([sys.executable, 'simple_main.py'], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)
        bot_started = True
        print("✅ Telegram бот запущен в фоне")
    except Exception as e:
        print(f"❌ Ошибка запуска Telegram бота: {e}")
        bot_started = False

@app.route('/')
def index():
    """Главная страница"""
    return {
        'service': 'Telegram Time Tracking Bot',
        'status': 'running',
        'bot_status': 'active' if bot_started else 'starting',
        'uptime': str(datetime.now() - start_time),
        'endpoints': {
            'health': '/health',
            'status': '/api/status'
        }
    }

@app.route('/health')
def health_check():
    """Health check endpoint для Replit Deployments"""
    return jsonify({
        'status': 'healthy',
        'service': 'telegram-time-tracking-bot',
        'timestamp': datetime.now().isoformat(),
        'uptime_seconds': int((datetime.now() - start_time).total_seconds())
    })

@app.route('/api/status')
def api_status():
    """Детальный статус системы"""
    return jsonify({
        'web_server': 'running',
        'telegram_bot': 'active' if bot_started else 'starting',
        'database': 'connected',
        'start_time': start_time.isoformat(),
        'current_time': datetime.now().isoformat(),
        'process_id': bot_process.pid if bot_process else None
    })

if __name__ == '__main__':
    print("🚀 Запуск веб-сервера для деплоя...")
    print("🩺 Health check: http://localhost:5000/health")
    
    # Запуск Telegram бота в отдельном потоке (не блокирующий)
    bot_thread = threading.Thread(target=start_telegram_bot, daemon=True)
    bot_thread.start()
    
    # Немедленный запуск веб-сервера
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)