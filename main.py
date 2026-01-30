#!/usr/bin/env python3
"""
Главный файл запуска Книжного клуба бота
"""

import logging
import os
from dotenv import load_dotenv

from bot import main as bot_main

load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Запуск бота"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
        return

    logger.info("Запуск Книжного клуба бота...")
    
    # Запускаем основную функцию бота
    bot_main()

if __name__ == '__main__':
    main()