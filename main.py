#!/usr/bin/env python3
"""
Главный файл запуска Книжного клуба бота
"""

import asyncio
import logging
import os
from telegram.ext import Application

from bot import main as bot_main
from scheduler import NotificationScheduler
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def run_bot_with_scheduler():
    """Запуск бота вместе с планировщиком уведомлений"""
    
    # Получаем токен бота
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
        return
    
    # Создаем планировщик
    scheduler = NotificationScheduler(bot_token)
    scheduler.start()
    
    try:
        logger.info("Запуск Книжного клуба бота с планировщиком...")
        
        # Создаем приложение
        application = Application.builder().token(bot_token).build()
        
        # Здесь можно добавить дополнительные обработчики из bot.py
        # Для простоты запускаем основную функцию из bot.py
        await asyncio.get_event_loop().run_in_executor(None, bot_main)
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки...")
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
    finally:
        # Останавливаем планировщик
        scheduler.stop()
        logger.info("Бот и планировщик остановлены")

if __name__ == '__main__':
    # Запускаем бота с планировщиком
    asyncio.run(run_bot_with_scheduler())
