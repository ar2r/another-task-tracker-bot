#!/usr/bin/env python3
"""
Production startup script using Gunicorn for deployment
"""
import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run the application with Gunicorn"""
    port = os.environ.get('PORT', '5000')
    workers = os.environ.get('WEB_CONCURRENCY', '2')
    
    cmd = [
        sys.executable, '-m', 'gunicorn',
        '--bind', f'0.0.0.0:{port}',
        '--workers', str(workers),
        '--worker-class', 'sync',
        '--timeout', '60',
        '--access-logfile', '-',
        '--error-logfile', '-',
        'wsgi:application'
    ]
    
    logger.info(f"Starting Gunicorn server on port {port} with {workers} workers")
    logger.info(f"Command: {' '.join(cmd)}")
    
    # Execute gunicorn
    os.execvp(cmd[0], cmd)

if __name__ == '__main__':
    main()