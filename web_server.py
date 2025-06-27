import os
from flask import Flask, jsonify
import logging
from datetime import datetime
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Global variable to track bot status
bot_status = {
    'running': False,
    'start_time': None,
    'last_activity': None
}

@app.route('/')
def health_check():
    """Root health check endpoint required for deployment"""
    return jsonify({
        'status': 'healthy',
        'service': 'telegram-time-tracking-bot',
        'timestamp': datetime.now().isoformat(),
        'bot_running': bot_status['running'],
        'uptime_seconds': (datetime.now() - bot_status['start_time']).total_seconds() if bot_status['start_time'] else 0
    })

@app.route('/health')
def health():
    """Additional health endpoint"""
    return health_check()

@app.route('/status')
def status():
    """Detailed status endpoint"""
    return jsonify({
        'bot_status': bot_status,
        'environment': {
            'bot_token_configured': bool(os.environ.get('BOT_TOKEN')),
            'database_url_configured': bool(os.environ.get('DATABASE_URL')),
        },
        'timestamp': datetime.now().isoformat()
    })

def update_bot_status(running=True):
    """Update bot status for health checks"""
    global bot_status
    bot_status['running'] = running
    bot_status['last_activity'] = datetime.now()
    if running and not bot_status['start_time']:
        bot_status['start_time'] = datetime.now()

def run_web_server():
    """Run the web server"""
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    run_web_server()