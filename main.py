#!/usr/bin/env python3
"""
Минимальный запускаемый бот с админ-панелью для Railway
"""

import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AdminPanel:
    def __init__(self):
        # УКАЖИТЕ СВОЙ ТЕЛЕГРАМ ID ЗДЕСЬ!
        self.admin_ids = [1075942245]  # Замените на ваш реальный ID
    
    def is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        return user_id in self.admin_ids
    
    async def admin_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /admin для администраторов"""
        user_id = update.effective_user.id
        logger.info(f"Пользователь {user_id} запросил админ-панель")
        logger.info(f"Admin IDs: {self.admin_ids}")
        
        if not self.is_admin(user_id):
            await update.message.reply_text("⛔ У вас нет доступа к админ-панели")
            return
        
        # Сохраняем состояние в user_data
        if context.user_data is None:
            context.user_data = {}
        context.user_data['in_admin'] = True
        
        keyboard = [
            [KeyboardButton("📊 Статистика")],
            [KeyboardButton("📚 Добавить книгу")],
            [KeyboardButton("👥 Пользователи")],
            [KeyboardButton("🔙 Выйти из админки")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "🛠️ **Админ-панель**\n\nВыберите действие:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_admin_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка сообщений в админ-панели"""
        if not self.is_admin(update.effective_user.id):
            return
        
        message_text = update.message.text
        
        if message_text == "📊 Статистика":
            await update.message.reply_text(
                "📊 **Статистика:**\n\n"
                "• Пользователей: 150\n"
                "• Активных: 42\n"
                "• Книг в базе: 25"
            )
        elif message_text == "📚 Добавить книгу":
            await update.message.reply_text(
                "📚 **Добавление книги:**\n\n"
                "Отправьте информацию в формате:\n"
                "Название, Автор, Жанр"
            )
        elif message_text == "👥 Пользователи":
            await update.message.reply_text(
                "👥 **Последние пользователи:**\n\n"
                "1. @user1 (ID: 123)\n"
                "2. @user2 (ID: 456)\n"
                "3. @user3 (ID: 789)"
            )
        elif message_text == "🔙 Выйти из админки":
            await self.exit_admin(update, context)
    
    async def exit_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Выйти из админ-панели"""
        if context.user_data is None:
            context.user_data = {}
        context.user_data['in_admin'] = False
        
        keyboard = [
            [KeyboardButton("/start"), KeyboardButton("/help")],
            [KeyboardButton("/admin")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "👋 Вы вышли из админ-панели",
            reply_markup=reply_markup
        )

# Создаем экземпляр админ-панели
admin_panel = AdminPanel()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /start"""
    user = update.effective_user
    
    keyboard = [
        [KeyboardButton("📚 Книги"), KeyboardButton("👤 Профиль")],
        [KeyboardButton("🛠 Админ-панель")] if admin_panel.is_admin(user.id) else [],
        [KeyboardButton("/help")]
    ]
    keyboard = [row for row in keyboard if row]  # Убираем пустые строки
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        f"Добро пожаловать в Книжный клуб!\n\n"
        f"Ваш ID: {user.id}\n"
        f"Админ: {'✅' if admin_panel.is_admin(user.id) else '❌'}",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /help"""
    await update.message.reply_text(
        "📚 **Книжный клуб - Помощь**\n\n"
        "Доступные команды:\n"
        "/start - Начать работу\n"
        "/help - Эта справка\n"
        "/admin - Админ-панель\n\n"
        "Просто нажимайте на кнопки в меню!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка всех текстовых сообщений"""
    user = update.effective_user
    message_text = update.message.text
    
    logger.info(f"Сообщение от {user.id} ({user.username}): {message_text}")
    
    # Проверяем, находится ли пользователь в админ-панели
    is_in_admin = context.user_data.get('in_admin', False) if context.user_data else False
    
    if is_in_admin and admin_panel.is_admin(user.id):
        # Если пользователь администратор и в админ-панели
        await admin_panel.handle_admin_message(update, context)
    elif message_text == "🛠 Админ-панель" and admin_panel.is_admin(user.id):
        # Если нажата кнопка админ-панели
        await admin_panel.admin_start(update, context)
    elif message_text == "📚 Книги":
        await update.message.reply_text("📚 Список книг будет здесь...")
    elif message_text == "👤 Профиль":
        await update.message.reply_text(f"👤 Ваш профиль:\nID: {user.id}\nИмя: {user.first_name}")
    elif message_text == "/admin":
        await admin_panel.admin_start(update, context)
    else:
        await update.message.reply_text(
            f"Вы написали: {message_text}\n\n"
            f"Используйте меню или команды."
        )

def main():
    """Запуск бота"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден!")
        return
    
    logger.info(f"✅ Токен найден: {token[:10]}...")
    logger.info(f"✅ Админы: {admin_panel.admin_ids}")
    
    # Создаем приложение
    application = Application.builder().token(token).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_panel.admin_start))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    logger.info("🚀 Бот запущен и ожидает сообщений...")
    application.run_polling(allowed_updates=['message', 'callback_query'])

if __name__ == "__main__":
    main()