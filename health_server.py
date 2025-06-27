#!/usr/bin/env python3
"""
Минимальный веб-сервер только для health check.
Для успешного деплоя в Replit Deployments.
"""

from flask import Flask, jsonify
from datetime import datetime
import os

app = Flask(__name__)
start_time = datetime.now()

@app.route('/')
def index():
    """Главная страница"""
    return jsonify({
        'service': 'Telegram Time Tracking Bot',
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': str(datetime.now() - start_time),
        'endpoints': ['/health', '/status']
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/status') 
def status():
    """Status endpoint"""
    return jsonify({
        'service': 'running',
        'uptime': str(datetime.now() - start_time),
        'bot_token_configured': bool(os.getenv('BOT_TOKEN'))
    })

if __name__ == '__main__':
    print("Starting health check server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)