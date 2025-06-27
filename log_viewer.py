#!/usr/bin/env python3
"""
Простой веб-сервер для просмотра логов Telegram бота после деплоя.
Запускается на порту 5000 и позволяет просматривать логи через браузер.
"""

import os
from flask import Flask, render_template_string, jsonify, request
from datetime import datetime
import threading
import time

app = Flask(__name__)

# HTML шаблон для отображения логов
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Telegram Bot Logs</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: 'Courier New', monospace; 
            margin: 20px; 
            background: #1a1a1a; 
            color: #00ff00; 
        }
        .header { 
            background: #333; 
            padding: 10px; 
            border-radius: 5px; 
            margin-bottom: 20px; 
        }
        .log-container { 
            background: #000; 
            padding: 15px; 
            border-radius: 5px; 
            height: 70vh; 
            overflow-y: auto; 
            border: 1px solid #444; 
        }
        .log-line { 
            margin: 2px 0; 
            padding: 2px 5px; 
            border-radius: 3px; 
            font-size: 12px; 
        }
        .log-info { background: rgba(0, 255, 0, 0.1); }
        .log-warning { background: rgba(255, 255, 0, 0.1); color: #ffff00; }
        .log-error { background: rgba(255, 0, 0, 0.1); color: #ff6666; }
        .user-action { background: rgba(0, 255, 255, 0.1); color: #00ffff; font-weight: bold; }
        .controls { 
            margin: 10px 0; 
            text-align: center; 
        }
        button { 
            background: #444; 
            color: #00ff00; 
            border: 1px solid #666; 
            padding: 8px 15px; 
            margin: 0 5px; 
            border-radius: 3px; 
            cursor: pointer; 
        }
        button:hover { background: #555; }
        .stats { 
            display: flex; 
            justify-content: space-between; 
            margin-bottom: 10px; 
            font-size: 14px; 
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Telegram Bot Logs</h1>
        <div class="stats">
            <span>Всего записей: <span id="totalLogs">{{ total_logs }}</span></span>
            <span>Последнее обновление: <span id="lastUpdate">{{ last_update }}</span></span>
        </div>
        <div class="controls">
            <button onclick="refreshLogs()">🔄 Обновить</button>
            <button onclick="clearLogs()">🗑️ Очистить</button>
            <button onclick="downloadLogs()">💾 Скачать</button>
            <label>
                <input type="checkbox" id="autoRefresh" onchange="toggleAutoRefresh()"> 
                Авто-обновление (5с)
            </label>
        </div>
    </div>
    
    <div class="log-container" id="logContainer">
        {% for log in logs %}
        <div class="log-line {{ log.css_class }}">{{ log.text }}</div>
        {% endfor %}
    </div>

    <script>
        let autoRefreshInterval = null;
        
        function refreshLogs() {
            fetch('/api/logs')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('logContainer');
                    container.innerHTML = '';
                    data.logs.forEach(log => {
                        const div = document.createElement('div');
                        div.className = `log-line ${log.css_class}`;
                        div.textContent = log.text;
                        container.appendChild(div);
                    });
                    document.getElementById('totalLogs').textContent = data.total;
                    document.getElementById('lastUpdate').textContent = data.last_update;
                    container.scrollTop = container.scrollHeight;
                })
                .catch(error => console.error('Error:', error));
        }
        
        function clearLogs() {
            if (confirm('Очистить все логи?')) {
                fetch('/api/clear', { method: 'POST' })
                    .then(() => refreshLogs());
            }
        }
        
        function downloadLogs() {
            window.open('/api/download', '_blank');
        }
        
        function toggleAutoRefresh() {
            const checkbox = document.getElementById('autoRefresh');
            if (checkbox.checked) {
                autoRefreshInterval = setInterval(refreshLogs, 5000);
            } else {
                clearInterval(autoRefreshInterval);
            }
        }
        
        // Автоскролл вниз при загрузке
        document.addEventListener('DOMContentLoaded', function() {
            const container = document.getElementById('logContainer');
            container.scrollTop = container.scrollHeight;
        });
    </script>
</body>
</html>
"""

def get_log_files():
    """Получить список файлов логов"""
    log_files = []
    if os.path.exists('logs'):
        for file in os.listdir('logs'):
            if file.endswith('.log'):
                log_files.append(os.path.join('logs', file))
    return sorted(log_files)

def read_logs(lines=1000):
    """Прочитать последние N строк из логов"""
    logs = []
    log_files = get_log_files()
    
    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        css_class = 'log-info'
                        if '📨' in line:
                            css_class = 'user-action'
                        elif 'WARNING' in line:
                            css_class = 'log-warning'
                        elif 'ERROR' in line:
                            css_class = 'log-error'
                        
                        logs.append({
                            'text': line,
                            'css_class': css_class
                        })
        except Exception as e:
            logs.append({
                'text': f'Ошибка чтения файла {log_file}: {e}',
                'css_class': 'log-error'
            })
    
    # Возвращаем последние N записей
    return logs[-lines:] if len(logs) > lines else logs

@app.route('/')
def index():
    """Главная страница с логами"""
    logs = read_logs()
    return render_template_string(HTML_TEMPLATE, 
                                logs=logs, 
                                total_logs=len(logs),
                                last_update=datetime.now().strftime('%H:%M:%S'))

@app.route('/api/logs')
def api_logs():
    """API для получения логов в JSON"""
    logs = read_logs()
    return jsonify({
        'logs': logs,
        'total': len(logs),
        'last_update': datetime.now().strftime('%H:%M:%S')
    })

@app.route('/api/clear', methods=['POST'])
def api_clear():
    """API для очистки логов"""
    try:
        log_files = get_log_files()
        for log_file in log_files:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('')
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/download')
def api_download():
    """API для скачивания логов"""
    from flask import Response
    
    logs = read_logs(lines=10000)  # Больше строк для скачивания
    log_text = '\n'.join([log['text'] for log in logs])
    
    return Response(
        log_text,
        mimetype='text/plain',
        headers={'Content-Disposition': f'attachment; filename=bot_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'}
    )

if __name__ == '__main__':
    print("🚀 Запуск веб-сервера для просмотра логов на порту 5000...")
    print("📊 Откройте http://localhost:5000 для просмотра логов")
    app.run(host='0.0.0.0', port=5000, debug=False)