import time
import os

# Подождать, если обнаружен конфликт
time.sleep(5)  # Подождать 5 секунд перед запуском

# Или использовать переменную окружения для уникального идентификатора
unique_id = os.getenv("CONTAINER_ID", "default")
print(f"Starting bot instance: {unique_id}")

"""
Финальная версия бота с интегрированной системой тестирования
"""

import logging
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode

from database import Database
from ai_service import AIService
from commands import setup_commands
from test_integration import setup_test_integration
from testing_system import setup_testing_handlers
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()
ai_service = AIService()

# Импортируем расширенные функции
from enhanced_bot import (
    start, show_main_menu, handle_message, button_callback,
    show_schedule, show_current_book, show_voting, show_discussion,
    show_community, show_bonuses, show_premium, show_tools, show_about,
    handle_registration_name, handle_registration_genres, handle_registration_goals,
    handle_book_suggestion, handle_note_adding, handle_voting_callback,
    generate_ai_questions, help_command, get_main_menu, get_user_state, set_user_state,
    UserState
)

async def enhanced_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user_name: str = None):
    """Расширенное главное меню с тестированием"""
    user = update.effective_user
    if not user_name:
        existing_user = db.get_user(user.id)
        user_name = existing_user['name'] if existing_user else user.first_name
    
    main_menu_text = (
        f"📚 **КНИЖНЫЙ КЛУБ С ИИ-ТЕСТИРОВАНИЕМ**\n\n"
        f"Добро пожаловать, {user_name}! 👋\n\n"
        "Выберите раздел:"
    )
    
    # Расширенное меню с тестированием
    keyboard = [
        [KeyboardButton("🗓 РАСПИСАНИЕ")],
        [KeyboardButton("📖 ТЕКУЩАЯ КНИГА")],
        [KeyboardButton("🗳 ГОЛОСОВАНИЕ")],
        [KeyboardButton("🧠 ОБСУЖДЕНИЕ")],
        [KeyboardButton("🧪 ТЕСТИРОВАНИЕ")],  # Новый раздел
        [KeyboardButton("👥 СООБЩЕСТВО")],
        [KeyboardButton("🎁 БОНУСЫ")],
        [KeyboardButton("🌟 ПРЕМИУМ")],
        [KeyboardButton("🛠 ИНСТРУМЕНТЫ")],
        [KeyboardButton("ℹ️ О КЛУБЕ")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    if update.message:
        await update.message.reply_text(main_menu_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.callback_query.message.reply_text(main_menu_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def handle_enhanced_menu_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
    """Обработка расширенной навигации по меню"""
    if message_text == "🗓 РАСПИСАНИЕ":
        await show_schedule(update, context)
    elif message_text == "📖 ТЕКУЩАЯ КНИГА":
        await show_current_book(update, context)
    elif message_text == "🗳 ГОЛОСОВАНИЕ":
        await show_voting(update, context)
    elif message_text == "🧠 ОБСУЖДЕНИЕ":
        await show_discussion(update, context)
    elif message_text == "🧪 ТЕСТИРОВАНИЕ":
        await show_testing_menu(update, context)
    elif message_text == "👥 СООБЩЕСТВО":
        await show_community(update, context)
    elif message_text == "🎁 БОНУСЫ":
        await show_bonuses(update, context)
    elif message_text == "🌟 ПРЕМИУМ":
        await show_premium(update, context)
    elif message_text == "🛠 ИНСТРУМЕНТЫ":
        await show_tools(update, context)
    elif message_text == "ℹ️ О КЛУБЕ":
        await show_about(update, context)
    else:
        await update.message.reply_text("Выберите раздел из меню 📱 или используйте команду /help")

async def show_testing_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню тестирования"""
    user = update.effective_user
    
    # Получаем статистику пользователя
    from database_extended import DatabaseExtended
    db_ext = DatabaseExtended()
    stats = db_ext.get_user_test_statistics(user.id)
    
    testing_text = (
        "🧪 **ЦЕНТР ТЕСТИРОВАНИЯ**\n\n"
        "🤖 **ИИ-тестирование после прочтения книг**\n\n"
        "📊 **Ваша статистика:**\n"
        f"• Пройдено тестов: {stats['total_tests']}\n"
        f"• Средний балл: {stats['average_score']}%\n"
        f"• Лучший результат: {stats['best_score']}%\n\n"
        "🎯 **Доступные тесты:**\n"
        "• 📖 Тест по текущей книге\n"
        "• 🎯 Адаптивный тест (по слабым местам)\n"
        "• 📊 История результатов\n"
        "• 📈 Анализ прогресса\n\n"
        "Выберите действие:"
    )
    
    keyboard = [
        [InlineKeyboardButton("📖 Тест по текущей книге", callback_data="start_current_test")],
        [InlineKeyboardButton("🎯 Адаптивный тест", callback_data="adaptive_test")],
        [InlineKeyboardButton("📊 История тестов", callback_data="test_history")],
        [InlineKeyboardButton("📈 Анализ прогресса", callback_data="progress_analysis")],
        [InlineKeyboardButton("❓ Как работает тестирование", callback_data="test_help")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(testing_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

   async def handle_enhanced_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message_text = update.message.text
        telegram_id = update.effective_user.id
        state = get_user_state(str(telegram_id))  # Убедитесь, что передаем строку
        
        print(f"DEBUG: Handling message from {telegram_id}, state: {state}, text: {message_text}")
        
        if state == UserState.REGISTERING_NAME:
            # Обработка имени
            result = handle_registration_name(update, context, message_text)
            if result and 'message' in result:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=result['message']
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Что-то пошло не так. Пожалуйста, введите ваше имя еще раз."
                )
            return
        
        elif state == UserState.REG_GENRES:
            # Обработка жанров - пользователь вводит жанры через запятую
            print(f"DEBUG: Processing genres for user {telegram_id}")
            genres = [g.strip() for g in message_text.split(',')]
            result = handle_registration_genres(update, context, genres)
            if result and 'message' in result:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=result['message']
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Пожалуйста, введите жанры через запятую, например: Фантастика, Детектив, Роман"
                )
            return
        
        elif state == UserState.REG_GOALS:
            # Обработка целей
            goals = [g.strip() for g in message_text.split(',')]
            result = handle_registration_goals(update, context, goals)
            if result and 'message' in result:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=result['message']
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Пожалуйста, введите цели через запятую"
                )
            return
        
        # Если состояние не соответствует вышеуказанным, обрабатываем как обычное сообщение
        result = handle_message(str(telegram_id), message_text)
        if result and 'response' in result:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=result['response']
            )
            
    except Exception as e:
        print(f"ERROR in handle_enhanced_message: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Произошла ошибка при обработке сообщения. Попробуйте еще раз."
            )
        except:
            pass
    
    # Обработка состояний регистрации
    if state == UserState.REGISTERING_NAME:
        result = handle_registration_name(update, context, message_text)
    elif state == UserState.REGISTERING_GENRES:
        result = handle_registration_genres(update, context, message_text)
    elif state == UserState.REGISTERING_GOALS:
        result = handle_registration_goals(update, context, message_text)
    elif state == UserState.SUGGESTING_BOOK:
        result = handle_book_suggestion(update, context, message_text)
    elif state == UserState.ADDING_NOTE:
        result = handle_note_adding(update, context, message_text)
    elif state == UserState.NORMAL:
        result = handle_enhanced_menu_navigation(update, context, message_text)

async def handle_enhanced_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка колбэков для финальной версии"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "back_to_main":
        await enhanced_main_menu(update, context)
    elif data == "start_current_test":
        # Запускаем тест по текущей книге
        from test_integration import test_integration
        await test_integration.start_test_command(update, context)
    elif data == "adaptive_test":
        from test_integration import test_integration
        await test_integration.adaptive_test_command(update, context)
    elif data == "test_history":
        from test_integration import test_integration
        await test_integration.test_history_command(update, context)
    elif data == "progress_analysis":
        await show_progress_analysis(update, context)
    elif data == "test_help":
        await show_test_help(update, context)
    else:
        # Передаем другим обработчикам
        await button_callback(update, context)

async def show_progress_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает анализ прогресса"""
    from database_extended import DatabaseExtended
    db_ext = DatabaseExtended()
    
    user = update.effective_user
    stats = db_ext.get_user_test_statistics(user.id)
    performance = db_ext.get_category_performance(user.id)
    
    if stats['total_tests'] == 0:
        await update.callback_query.edit_message_text(
            "📈 **АНАЛИЗ ПРОГРЕССА**\n\n"
            "Недостаточно данных для анализа.\n"
            "Пройдите несколько тестов для отслеживания прогресса.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📖 Начать тест", callback_data="start_current_test"),
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
            ]])
        )
        return
    
    analysis_text = "📈 **АНАЛИЗ ПРОГРЕССА**\n\n"
    
    # Общая статистика
    analysis_text += (
        f"📊 **Общая статистика:**\n"
        f"• Тестов пройдено: {stats['total_tests']}\n"
        f"• Средний балл: {stats['average_score']}%\n"
        f"• Лучший результат: {stats['best_score']}%\n\n"
    )
    
    # Анализ по категориям
    if performance:
        analysis_text += "🎯 **Производительность по категориям:**\n"
        for category, stats_cat in performance.items():
            progress_icon = "📈" if stats_cat['percentage'] >= 70 else "📉" if stats_cat['percentage'] < 50 else "➡️"
            analysis_text += f"{progress_icon} {category}: {stats_cat['percentage']}%\n"
        
        analysis_text += "\n"
    
    # Рекомендации
    analysis_text += "💡 **Рекомендации:**\n"
    if stats['average_score'] >= 80:
        analysis_text += "• Отличный прогресс! Попробуйте более сложные книги\n"
    elif stats['average_score'] >= 60:
        analysis_text += "• Хороший прогресс! Фокусируйтесь на слабых категориях\n"
    else:
        analysis_text += "• Продолжайте практиковаться и перечитывайте книги\n"
    
    keyboard = [
        [InlineKeyboardButton("🎯 Адаптивный тест", callback_data="adaptive_test")],
        [InlineKeyboardButton("📊 Детальная статистика", callback_data="detailed_stats")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(analysis_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def show_test_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает справку по тестированию"""
    help_text = (
        "❓ **КАК РАБОТАЕТ ТЕСТИРОВАНИЕ**\n\n"
        "🤖 **ИИ-генерация вопросов:**\n"
        "• Искусственный интеллект создает уникальные вопросы по каждой книге\n"
        "• Вопросы проверяют глубокое понимание сюжета, персонажей и тем\n"
        "• Адаптируются под ваш уровень знаний\n\n"
        "📊 **Типы вопросов:**\n"
        "• 🎯 Сюжетные вопросы (что, когда, как)\n"
        "• 👥 Анализ персонажей (мотивация, развитие)\n"
        "• 💭 Тематические вопросы (смыслы, символы)\n"
        "• 💬 Узнавание цитат\n"
        "• 🌍 Контекстные вопросы\n\n"
        "🎯 **Адаптивное тестирование:**\n"
        "• Анализирует ваши слабые места\n"
        "• Создает вопросы для улучшения конкретных навыков\n"
        "• Помогает сфокусироваться на сложных аспектах\n\n"
        "📈 **Результаты и прогресс:**\n"
        "• Детальная статистика по категориям\n"
        "• Отслеживание прогресса во времени\n"
        "• Персональные рекомендации\n\n"
        "💡 **Советы:**\n"
        "• Проходите тесты сразу после прочтения\n"
        "• Анализируйте ошибки и перечитывайте сложные места\n"
        "• Используйте адаптивные тесты для улучшения"
    )
    
    keyboard = [
        [InlineKeyboardButton("📖 Начать тест", callback_data="start_current_test")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def enhanced_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    user_id_str = str(telegram_id)
    
    # Устанавливаем начальное состояние
    set_user_state(user_id_str, UserState.REGISTERING_NAME)
    
    print(f"DEBUG: Starting registration for user {user_id_str}")
    
    # Отправляем приветственное сообщение
    await update.message.reply_text(
            "📚 Добро пожаловать в Книжный клуб с ИИ-тестированием!\n\n"
            "Я помогу вам:\n"
            "• 📚 Находить интересные книги\n"
            "• 🧠 Глубоко понимать прочитанное\n"
            "• 🧪 Проходить ИИ-тесты после каждой книги\n"
            "• 🤝 Находить единомышленников\n\n"
            "Давайте начнем с регистрации. Как вас зовут?"
        )
        set_user_state(telegram_id, UserState.REGISTERING_NAME)

def main():
    """Основная функция запуска финального бота"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
        return
    
    application = Application.builder().token(token).build()
    
    # Основные команды
    application.add_handler(CommandHandler("start", enhanced_start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Команды тестирования
    from test_integration import test_integration
    application.add_handler(CommandHandler("test", test_integration.test_menu_command))
    application.add_handler(CommandHandler("start_test", test_integration.start_test_command))
    application.add_handler(CommandHandler("adaptive_test", test_integration.adaptive_test_command))
    
    # Дополнительные команды
    setup_commands(application)
    
    # Интеграция тестирования
    setup_test_integration(application)
    
    # Обработчики тестирования
    setup_testing_handlers(application)
    
    # Колбэки
    application.add_handler(CallbackQueryHandler(handle_enhanced_callback))
    
    # Сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_enhanced_message))
    
    logger.info("Запуск финальной версии Книжного клуба с ИИ-тестированием...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
