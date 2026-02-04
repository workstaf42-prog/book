# После других импортов добавьте:
from admin_panel import AdminPanel

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

# Создаем экземпляр админ-панели
admin_panel = AdminPanel()

# Импортируем расширенные функции
from enhanced_bot import (
    start, show_main_menu, handle_message, button_callback,
    show_schedule, show_current_book, show_voting, show_discussion,
    show_community, show_bonuses, show_premium, show_tools, show_about,
    handle_registration_name, handle_registration_genres, handle_registration_goals,
    handle_book_suggestion, handle_note_adding, handle_voting_callback,
    generate_ai_questions, help_command, get_main_menu, get_user_state, set_user_state,
    UserState  # UserState уже импортирован из enhanced_bot
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

# Дополнительные состояния для совместимости с enhanced_bot
try:
    UserState.REG_GENRES
except AttributeError:
    # Добавляем недостающие состояния динамически
    from enum import Enum
    
    class UserStateExtended(Enum):
        START = "start"
        NORMAL = "normal"
        REGISTERING_NAME = "registering_name"
        REGISTERING_GENRES = "registering_genres"
        REGISTERING_GOALS = "registering_goals"
        SUGGESTING_BOOK = "suggesting_book"
        ADDING_NOTE = "adding_note"
        
        # Состояния из enhanced_bot
        REG_GENRES = "reg_genres"
        REG_GOALS = "reg_goals"
        REG_NAME = "reg_name"
        
        # Другие возможные состояния
        WAITING_FOR_GENRES = "waiting_for_genres"
        WAITING_FOR_GOALS = "waiting_for_goals"
        WAITING_FOR_FEEDBACK = "waiting_for_feedback"
        
        # Состояния работы с книгами
        WAITING_FOR_RECOMMENDATION = "waiting_for_recommendation"
        BROWSE_BOOKS = "browse_books"
        BOOK_DETAILS = "book_details"
    
    # Заменяем старый enum на новый
    UserState = UserStateExtended
    print(f"DEBUG: Extended UserState with new states: {[s.name for s in UserState]}")

async def handle_enhanced_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений для финальной версии"""
    user = update.effective_user
    telegram_id = user.id
    message_text = update.message.text
    
    print(f"DEBUG: Handling message from {telegram_id}, text: {message_text}")
    
    # Проверяем, если это команда /start
    if message_text == "/start":
        await enhanced_start(update, context)
        return
    
    # Получаем состояние пользователя
    state = get_user_state(telegram_id)
    
    # Если состояние None, начинаем регистрацию заново
    if state is None:
        await enhanced_start(update, context)
        return
    
    # Преобразуем состояние в строку для удобства
    state_str = str(state)
    if hasattr(state, 'value'):
        state_str = state.value
    
    print(f"DEBUG: State string: {state_str}")
    
    # Простая логика регистрации
    if "name" in state_str.lower() or "reg_name" in state_str:
        # Шаг 1: Сохраняем имя
        print(f"DEBUG: Saving name: {message_text}")
        
        # Пробуем разные методы для сохранения пользователя
        try:
            # Пробуем метод create_user (если он существует)
            db.create_user(
                telegram_id=telegram_id,
                name=message_text,
                genres="",
                goals="",
                username=user.username or "",
                registration_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            print(f"DEBUG: User {telegram_id} created in database")
        except AttributeError:
            # Если нет create_user, пробуем другой метод
            print(f"DEBUG: create_user not found, trying other methods")
            try:
                # Пробуем add_user
                db.add_user(
                    telegram_id=telegram_id,
                    name=message_text,
                    genres="",
                    goals="",
                    username=user.username or "",
                    registration_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                print(f"DEBUG: User {telegram_id} added to database")
            except Exception as e:
                print(f"DEBUG: Error adding user: {e}")
                # Если не удалось сохранить в БД, сохраняем в контекст
                if 'user_data' not in context.user_data:
                    context.user_data['user_data'] = {}
                context.user_data['user_data'][telegram_id] = {
                    'name': message_text,
                    'genres': '',
                    'goals': ''
                }
        
        # Устанавливаем состояние для следующего шага
        set_user_state(telegram_id, "waiting_for_genres")
        
        # Запрашиваем жанры
        await update.message.reply_text(
            "📚 **ШАГ 2/3: Ваши любимые жанры**\n\n"
            "Расскажите, какие жанры книг вам нравятся?\n\n"
            "Примеры жанров:\n"
            "• Фантастика\n"
            "• Детектив\n"
            "• Саморазвитие\n"
            "• Научная литература\n"
            "• Биография\n"
            "• Классика\n"
            "• Современная проза\n"
            "• Ужасы\n"
            "• Роман\n"
            "• Поэзия\n\n"
            "Перечислите через запятую:"
        )
        
    elif "genre" in state_str.lower() or "genres" in state_str:
        # Шаг 2: Сохраняем жанры
        print(f"DEBUG: Saving genres: {message_text}")
        
        # Пробуем обновить жанры в базе данных
        try:
            # Пробуем update_user
            db.update_user(telegram_id, genres=message_text)
            print(f"DEBUG: User {telegram_id} genres updated in database")
        except AttributeError:
            # Если нет update_user, пробуем другой способ
            print(f"DEBUG: update_user not found, using context")
            if 'user_data' not in context.user_data:
                context.user_data['user_data'] = {}
            if telegram_id not in context.user_data['user_data']:
                context.user_data['user_data'][telegram_id] = {}
            context.user_data['user_data'][telegram_id]['genres'] = message_text
        
        # Устанавливаем состояние для следующего шага
        set_user_state(telegram_id, "waiting_for_goals")
        
        # Запрашиваем цели
        await update.message.reply_text(
            "🎯 **ШАГ 3/3: Ваши цели**\n\n"
            "Зачем вы присоединяетесь к книжному клубе?\n\n"
            "Примеры целей:\n"
            "• Находить интересные книги\n"
            "• Глубже понимать прочитанное\n"
            "• Обсуждать книги с единомышленниками\n"
            "• Регулярно читать\n"
            "• Расширять кругозор\n"
            "• Улучшать навыки чтения\n"
            "• Получать рекомендации\n"
            "• Участвовать в обсуждениях\n"
            "• Отслеживать прогресс\n"
            "• Найти мотивацию для чтения\n\n"
            "Опишите ваши цели:"
        )
        
    elif "goal" in state_str.lower() or "goals" in state_str:
        # Шаг 3: Сохраняем цели и завершаем регистрацию
        print(f"DEBUG: Saving goals: {message_text}")
        
        # Пробуем обновить цели в базе данных
        try:
            # Пробуем update_user
            db.update_user(telegram_id, goals=message_text)
            print(f"DEBUG: User {telegram_id} goals updated in database")
        except AttributeError:
            # Если нет update_user, пробуем другой способ
            print(f"DEBUG: update_user not found, using context")
            if 'user_data' not in context.user_data:
                context.user_data['user_data'] = {}
            if telegram_id not in context.user_data['user_data']:
                context.user_data['user_data'][telegram_id] = {}
            context.user_data['user_data'][telegram_id]['goals'] = message_text
        
        # Устанавливаем состояние "normal" (зарегистрирован)
        set_user_state(telegram_id, "normal")
        
        # Получаем данные пользователя для приветствия
        try:
            user_data = db.get_user(telegram_id)
            welcome_name = user_data['name'] if user_data else user.first_name
        except:
            # Если не удалось получить из БД, пробуем из контекста
            if ('user_data' in context.user_data and 
                telegram_id in context.user_data['user_data'] and
                'name' in context.user_data['user_data'][telegram_id]):
                welcome_name = context.user_data['user_data'][telegram_id]['name']
            else:
                welcome_name = user.first_name
        
        # Приветствуем пользователя
        await update.message.reply_text(
            f"🎉 **Регистрация завершена!**\n\n"
            f"Добро пожаловать в книжный клуб, {welcome_name}! ✨\n\n"
            f"Теперь вы можете:\n"
            f"• 📚 Получать книжные рекомендации\n"
            f"• 🧪 Проходить ИИ-тесты после чтения\n"
            f"• 🤝 Обсуждать книги с сообществом\n"
            f"• 🎯 Отслеживать свой прогресс\n\n"
            f"Используйте меню ниже, чтобы начать:"
        )
        
        # Показываем главное меню
        await enhanced_main_menu(update, context, welcome_name)
        
    elif state_str == "normal":
        # Пользователь зарегистрирован - обрабатываем навигацию по меню
        await handle_enhanced_menu_navigation(update, context, message_text)
        
    else:
        # Неизвестное состояние - начинаем заново
        await update.message.reply_text(
            "📚 **Добро пожаловать в Книжный клуб!**\n\n"
            "Используйте команду /start для регистрации."
        )
        set_user_state(telegram_id, "start")

async def handle_enhanced_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка колбэков для финальной версии"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "back_to_main":
        user = update.effective_user
        existing_user = db.get_user(user.id)
        user_name = existing_user['name'] if existing_user else user.first_name
        await enhanced_main_menu(update, context, user_name)
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
    """Расширенная команда start"""
    user = update.effective_user
    telegram_id = user.id
    
    existing_user = db.get_user(telegram_id)
    
    if existing_user:
        # Если пользователь уже зарегистрирован - показываем главное меню
        await enhanced_main_menu(update, context, existing_user['name'])
    else:
        # Начинаем регистрацию
        await update.message.reply_text(
            "📚 **Добро пожаловать в Книжный клуб с ИИ-тестированием!**\n\n"
            "Я помогу вам:\n"
            "• 📚 Находить интересные книги\n"
            "• 🧠 Глубоко понимать прочитанное\n"
            "• 🧪 Проходить ИИ-тесты после каждой книги\n"
            "• 🤝 Находить единомышленников\n\n"
            "Давайте начнем с регистрации!\n\n"
            "**ШАГ 1/3: Как вас зовут?**"
        )
        set_user_state(telegram_id, "waiting_for_name")

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для принудительного показа меню"""
    user = update.effective_user
    telegram_id = user.id
    
    existing_user = db.get_user(telegram_id)
    
    if existing_user:
        await enhanced_main_menu(update, context, existing_user['name'])
    else:
        await update.message.reply_text(
            "Вы еще не зарегистрированы. Используйте команду /start для регистрации."
        )

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
    application.add_handler(CommandHandler("menu", menu_command))
    
    # ✅ ДОБАВЛЕНО: Команда /admin для админ-панели
    application.add_handler(CommandHandler("admin", admin_panel.admin_start))
    
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
    
    # ✅ ДОБАВЛЕНО: Колбэк для админ-панели
    application.add_handler(CallbackQueryHandler(admin_panel.handle_admin_callback))
    
    # Сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_enhanced_message))
    
    # ✅ ДОБАВЛЕНО: Сообщения для админ-панели (должен быть ПОСЛЕ основного обработчика)
    # Фильтруем только сообщения от админов, чтобы не мешать основному боту
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            admin_panel.handle_admin_message
        )
    )
    
    logger.info("Запуск финальной версии Книжного клуба с ИИ-тестированием...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
