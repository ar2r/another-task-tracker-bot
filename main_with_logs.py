#!/usr/bin/env python3
"""
Главный скрипт для запуска Telegram бота с веб-сервером для просмотра логов.
Запускает два процесса одновременно:
1. Telegram бот (simple_main.py)
2. Веб-сервер для логов (log_viewer.py) на порту 5000
"""

import os
import threading
import time
import subprocess
import signal
import sys

def run_telegram_bot():
    """Запуск Telegram бота"""
    print("🤖 Запуск Telegram бота...")
    try:
        subprocess.run([sys.executable, 'simple_main.py'], check=True)
    except KeyboardInterrupt:
        print("🛑 Telegram бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка Telegram бота: {e}")

def run_log_viewer():
    """Запуск веб-сервера для логов"""
    print("🌐 Запуск веб-сервера для просмотра логов на порту 5000...")
    try:
        subprocess.run([sys.executable, 'log_viewer.py'], check=True)
    except KeyboardInterrupt:
        print("🛑 Веб-сервер логов остановлен")
    except Exception as e:
        print(f"❌ Ошибка веб-сервера логов: {e}")

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    print("\n🛑 Получен сигнал завершения, останавливаем все процессы...")
    os._exit(0)

def main():
    """Главная функция для запуска всех сервисов"""
    print("🚀 Запуск Telegram бота с веб-интерфейсом для логов...")
    print("📊 Логи будут доступны по адресу: http://localhost:5000")
    print("📝 Файлы логов сохраняются в папку: logs/")
    print()
    
    # Настройка обработчика сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Создание потоков для каждого сервиса
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    log_viewer_thread = threading.Thread(target=run_log_viewer, daemon=True)
    
    try:
        # Запуск потоков
        bot_thread.start()
        time.sleep(2)  # Небольшая задержка перед запуском веб-сервера
        log_viewer_thread.start()
        
        print("✅ Все сервисы запущены!")
        print("   - Telegram бот: работает")
        print("   - Веб-интерфейс логов: http://localhost:5000")
        print("\n⚠️  Нажмите Ctrl+C для остановки всех сервисов")
        
        # Ожидание завершения потоков
        while bot_thread.is_alive() or log_viewer_thread.is_alive():
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Завершение работы...")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        print("👋 Все сервисы остановлены")

if __name__ == "__main__":
    main()