"""
Финальная версия бота с интегрированной системой тестирования
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode

from database import Database
from ai_service import AIService
from admin_panel import AdminPanel
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()
ai_service = AIService()
admin_panel = AdminPanel()

# Простые функции для работы с пользователями
user_states = {}

def get_user_state(user_id: int):
    """Получить состояние пользователя"""
    return user_states.get(user_id)

def set_user_state(user_id: int, state: str):
    """Установить состояние пользователя"""
    user_states[user_id] = state

async def enhanced_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Расширенная команда start"""
    user = update.effective_user
    telegram_id = user.id
    
    existing_user = db.get_user(telegram_id)
    
    if existing_user:
        # Если пользователь уже зарегистрирован
        await update.message.reply_text(
            f"👋 Добро пожаловать обратно, {existing_user['name']}!\n\n"
            f"Используйте /menu для доступа к меню или /admin для админ-панели."
        )
        set_user_state(telegram_id, "normal")
    else:
        # Начинаем регистрацию
        await update.message.reply_text(
            "📚 **Добро пожаловать в Книжный клуб!**\n\n"
            "Давайте зарегистрируем вас.\n\n"
            "**ШАГ 1/3: Как вас зовут?**"
        )
        set_user_state(telegram_id, "waiting_for_name")

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для показа меню"""
    user = update.effective_user
    telegram_id = user.id
    
    existing_user = db.get_user(telegram_id)
    
    if existing_user:
        # Показываем главное меню
        keyboard = [
            [KeyboardButton("📚 Мои книги")],
            [KeyboardButton("🗳 Голосование")],
            [KeyboardButton("📖 Читательский дневник")],
            [KeyboardButton("👤 Профиль")],
            [KeyboardButton("🛠 Админ-панель")] if admin_panel.is_admin(telegram_id) else []
        ]
        # Убираем пустые строки
        keyboard = [row for row in keyboard if row]
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f"📚 **Главное меню**\n\n"
            f"Привет, {existing_user['name']}! Выберите действие:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            "Вы еще не зарегистрированы. Используйте команду /start для регистрации."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда помощи"""
    await update.message.reply_text(
        "📚 **Книжный клуб - Помощь**\n\n"
        "Доступные команды:\n"
        "/start - Начать/зарегистрироваться\n"
        "/menu - Показать меню\n"
        "/help - Показать эту справку\n"
        "/admin - Админ-панель (только для администраторов)\n\n"
        "📞 Поддержка: @your_support_contact"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений"""
    user = update.effective_user
    telegram_id = user.id
    message_text = update.message.text
    
    # Сначала проверяем, не является ли это сообщением для админ-панели
    if admin_panel.is_admin(telegram_id):
        # Проверяем, находится ли пользователь в админ-панели
        if hasattr(context, 'user_data') and context.user_data.get('in_admin_panel'):
            await admin_panel.handle_admin_message(update, context)
            return
    
    # Проверяем состояние пользователя
    state = get_user_state(telegram_id)
    
    if message_text == "/start":
        await enhanced_start(update, context)
        return
    
    if message_text == "/menu":
        await menu_command(update, context)
        return
    
    if message_text == "/admin":
        await admin_panel.admin_start(update, context)
        return
    
    if message_text == "🛠 Админ-панель" and admin_panel.is_admin(telegram_id):
        await admin_panel.admin_start(update, context)
        return
    
    # Простая логика регистрации
    if state == "waiting_for_name":
        # Шаг 1: Сохраняем имя
        try:
            db.register_user(
                telegram_id=telegram_id,
                name=message_text,
                favorite_genres="",
                reading_goals=""
            )
            set_user_state(telegram_id, "waiting_for_genres")
            
            await update.message.reply_text(
                "✅ **Имя сохранено!**\n\n"
                "**ШАГ 2/3: Какие жанры книг вам нравятся?**\n\n"
                "Пример: Фантастика, Детектив, Роман, Научная литература"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    elif state == "waiting_for_genres":
        # Шаг 2: Сохраняем жанры
        try:
            db.update_user(telegram_id, favorite_genres=message_text)
            set_user_state(telegram_id, "waiting_for_goals")
            
            await update.message.reply_text(
                "✅ **Жанры сохранены!**\n\n"
                "**ШАГ 3/3: Какие у вас цели чтения?**\n\n"
                "Пример: Узнать новое, Расслабиться, Развиваться, Общаться с единомышленниками"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    elif state == "waiting_for_goals":
        # Шаг 3: Сохраняем цели и завершаем регистрацию
        try:
            db.update_user(telegram_id, reading_goals=message_text)
            set_user_state(telegram_id, "normal")
            
            user_data = db.get_user(telegram_id)
            
            await update.message.reply_text(
                f"🎉 **Регистрация завершена!**\n\n"
                f"Добро пожаловать в книжный клуб, {user_data['name']}!\n\n"
                f"Теперь вы можете использовать все функции клуба.\n"
                f"Напишите /menu для доступа к меню."
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    else:
        # Пользователь зарегистрирован - обрабатываем кнопки меню
        if message_text == "📚 Мои книги":
            await update.message.reply_text("📚 **Мои книги**\n\nЗдесь будут ваши книги...")
        elif message_text == "🗳 Голосование":
            await update.message.reply_text("🗳 **Голосование**\n\nЗдесь будет голосование за книги...")
        elif message_text == "📖 Читательский дневник":
            await update.message.reply_text("📖 **Читательский дневник**\n\nЗдесь будет ваш дневник...")
        elif message_text == "👤 Профиль":
            user_data = db.get_user(telegram_id)
            if user_data:
                await update.message.reply_text(
                    f"👤 **Ваш профиль**\n\n"
                    f"Имя: {user_data['name']}\n"
                    f"Жанры: {user_data.get('favorite_genres', 'Не указаны')}\n"
                    f"Цели: {user_data.get('reading_goals', 'Не указаны')}\n"
                    f"Дата регистрации: {user_data.get('registration_date', 'Неизвестно')}"
                )
        else:
            await update.message.reply_text(
                "Я не понял ваше сообщение. Используйте меню или команды."
            )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка колбэков"""
    query = update.callback_query
    await query.answer()
    
    # Если администратор и есть callback от админ-панели
    if admin_panel.is_admin(update.effective_user.id):
        await admin_panel.handle_admin_callback(update, context)
        return
    
    await query.edit_message_text("Кнопка нажата!")

def main():
    """Основная функция запуска бота"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
        sys.exit(1)
    
    # Проверяем токен
    if not token.startswith('8231248470:'):
        logger.error("Неверный форток токена!")
        sys.exit(1)
    
    logger.info(f"Запуск бота с токеном: {token[:10]}...")
    
    # Создаем приложение
    application = Application.builder().token(token).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", enhanced_start))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_panel.admin_start))
    
    # Добавляем обработчики сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Добавляем обработчики колбэков
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Запускаем бота
    logger.info("Бот запущен и ожидает сообщений...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()