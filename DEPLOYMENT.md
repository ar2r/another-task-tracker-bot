# Deployment Guide

## Overview

This Telegram Time Tracking Bot is now fully configured for deployment with proper health check endpoints and production-ready setup.

## Deployment Features Implemented

### ✅ Health Check Endpoints
- **Root endpoint (`/`)**: Primary health check for deployment platforms
- **Health endpoint (`/health`)**: Alternative health check endpoint
- **Status endpoint (`/status`)**: Detailed application status and environment info

### ✅ Production Configuration
- **Port Configuration**: Configured to run on port 5000 (required for deployment)
- **Gunicorn Support**: Production WSGI server setup included
- **Multi-threading**: Web server and Telegram bot run in separate threads

### ✅ Environment Setup
- **Dependencies**: Flask and Gunicorn installed for web server functionality
- **Database**: PostgreSQL properly configured and initialized
- **Logging**: Comprehensive logging for monitoring and debugging

## Deployment Options

### Option 1: Direct Deployment (Current Setup)
The `Web App` workflow is already running and ready for deployment:
- Runs on port 5000 with health check endpoints active
- Both Telegram bot and web server operational
- Database initialized and configured

### Option 2: Production Deployment with Gunicorn
For production environments, use the gunicorn configuration:

```bash
# Production startup command
python run_gunicorn.py
```

Or directly with gunicorn:
```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 wsgi:application
```

## Health Check Responses

### Root Endpoint Response (`GET /`)
```json
{
    "status": "healthy",
    "service": "telegram-time-tracking-bot",
    "timestamp": "2025-06-27T19:54:05.981908",
    "bot_running": true,
    "web_server_running": true,
    "uptime_seconds": 42.5
}
```

### Status Endpoint Response (`GET /status`)
```json
{
    "app_status": {
        "bot_running": true,
        "last_activity": "Fri, 27 Jun 2025 19:53:23 GMT",
        "start_time": "Fri, 27 Jun 2025 19:53:23 GMT",
        "web_server_running": true
    },
    "environment": {
        "bot_token_configured": true,
        "database_url_configured": true
    },
    "timestamp": "2025-06-27T19:54:05.981908"
}
```

## Environment Variables Required

For deployment, ensure these environment variables are set:
- `BOT_TOKEN`: Telegram bot token (required)
- `DATABASE_URL`: PostgreSQL connection string (required)
- `PORT`: Server port (defaults to 5000)

## File Structure for Deployment

Key files for deployment:
- `app.py`: Main application with integrated web server and bot
- `wsgi.py`: WSGI entry point for production deployment
- `run_gunicorn.py`: Production startup script
- `web_server.py`: Standalone web server module (alternative)

## Architecture

```
┌─────────────────┐    ┌──────────────────┐
│   Web Server    │    │  Telegram Bot    │
│   (Flask)       │    │  (pyTelegramBot) │
│   Port: 5000    │    │                  │
│                 │    │                  │
│ Health Checks   │    │ Message Handler  │
│ Status API      │    │ Task Management  │
└─────────────────┘    └──────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
            ┌────────▼────────┐
            │   PostgreSQL    │
            │    Database     │
            └─────────────────┘
```

## Verification Commands

Test the deployment endpoints:

```bash
# Test root health check
curl http://localhost:5000/

# Test detailed status
curl http://localhost:5000/status

# Test health endpoint
curl http://localhost:5000/health
```

## Troubleshooting

### Common Issues
1. **Port conflicts**: Ensure port 5000 is available
2. **Environment variables**: Verify BOT_TOKEN and DATABASE_URL are set
3. **Database connection**: Check PostgreSQL service is running

### Logs
Monitor application logs through the workflow console or check:
- Web server logs: Available in workflow output
- Bot activity: Logged with user interaction details
- Database operations: Logged during initialization and queries

## Next Steps

1. **Deploy**: Use Replit's deployment feature with the current configuration
2. **Monitor**: Use health check endpoints for monitoring
3. **Scale**: Adjust gunicorn workers as needed for production load

The application is now fully deployment-ready with all required endpoints and proper error handling.