import logging
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode

from database import Database
from ai_service import AIService
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация сервисов
db = Database()
ai_service = AIService()

# Состояния пользователей
USER_STATES = {}

class UserState:
    REGISTERING_NAME = "registering_name"
    REGISTERING_GENRES = "registering_genres"
    REGISTERING_GOALS = "registering_goals"
    SURVEY_LAST_BOOK = "survey_last_book"
    SURVEY_DEPTH = "survey_depth"
    SURVEY_NONFICTION = "survey_nonfiction"
    DIARY_ENTRY = "diary_entry"
    NORMAL = "normal"

def get_user_state(telegram_id: int) -> str:
    return USER_STATES.get(telegram_id, UserState.NORMAL)

def set_user_state(telegram_id: int, state: str):
    USER_STATES[telegram_id] = state

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - приветствие и регистрация"""
    user = update.effective_user
    telegram_id = user.id
    
    # Проверяем, зарегистрирован ли пользователь
    existing_user = db.get_user(telegram_id)
    
    if existing_user:
        keyboard = [
            [KeyboardButton("📚 Моя анкета")],
            [KeyboardButton("🗳️ Голосование за книгу")],
            [KeyboardButton("📝 Читательский дневник")],
            [KeyboardButton("❓ Вопросы для обсуждения")],
            [KeyboardButton("📅 Ближайшие встречи")],
            [KeyboardButton("💎 Премиум функции")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f"С возвращением в Книжный клуб, {existing_user['name']}! 👋\n\n"
            "Выберите действие в меню:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "📚 Добро пожаловать в Книжный клуб с ИИ-консультантом!\n\n"
            "Я помогу вам найти интересные книги, участвовать в обсуждениях "
            "и найти единомышленников.\n\n"
            "Давайте начнем с регистрации. Как вас зовут?"
        )
        set_user_state(telegram_id, UserState.REGISTERING_NAME)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    user = update.effective_user
    telegram_id = user.id
    message_text = update.message.text
    state = get_user_state(telegram_id)
    
    if state == UserState.REGISTERING_NAME:
        # Сохраняем имя и запрашиваем жанры
        context.user_data['name'] = message_text
        
        await update.message.reply_text(
            f"Приятно познакомиться, {message_text}! 📖\n\n"
            "Какие жанры литературы вам нравятся? "
            "Например: фантастика, детективы, романтика, нон-фикшен, классика..."
        )
        set_user_state(telegram_id, UserState.REGISTERING_GENRES)
    
    elif state == UserState.REGISTERING_GENRES:
        # Сохраняем жанры и запрашиваем цели
        context.user_data['genres'] = message_text
        
        keyboard = [
            [KeyboardButton("Развлечься и отдохнуть")],
            [KeyboardButton("Узнать новое")],
            [KeyboardButton("Найти единомышленников")],
            [KeyboardButton("Саморазвитие")],
            [KeyboardButton("Все перечисленное")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "Отлично! А какова ваша цель чтения? Выберите из вариантов:",
            reply_markup=reply_markup
        )
        set_user_state(telegram_id, UserState.REGISTERING_GOALS)
    
    elif state == UserState.REGISTERING_GOALS:
        # Завершаем регистрацию
        name = context.user_data.get('name', '')
        genres = context.user_data.get('genres', '')
        
        success = db.register_user(telegram_id, name, genres, message_text)
        
        if success:
            keyboard = [
                [KeyboardButton("📚 Моя анкета")],
                [KeyboardButton("🗳️ Голосование за книгу")],
                [KeyboardButton("📝 Читательский дневник")],
                [KeyboardButton("❓ Вопросы для обсуждения")],
                [KeyboardButton("📅 Ближайшие встречи")],
                [KeyboardButton("💎 Премиум функции")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                f"🎉 Поздравляю, {name}! Вы успешно зарегистрированы в Книжном клубе!\n\n"
                "Теперь вы можете:\n"
                "• Голосовать за следующую книгу\n"
                "• Вести читательский дневник\n"
                "• Получать вопросы для обсуждения\n"
                "• Участвовать в встречах клуба\n\n"
                "Выберите действие в меню:",
                reply_markup=reply_markup
            )
            set_user_state(telegram_id, UserState.NORMAL)
        else:
            await update.message.reply_text(
                "😕 Произошла ошибка при регистрации. Попробуйте еще раз."
            )
    
    elif state == UserState.NORMAL:
        # Обработка команд из меню
        if message_text == "📚 Моя анкета":
            await show_profile(update, context)
        elif message_text == "🗳️ Голосование за книгу":
            await start_voting(update, context)
        elif message_text == "📝 Читательский дневник":
            await start_diary(update, context)
        elif message_text == "❓ Вопросы для обсуждения":
            await get_discussion_questions(update, context)
        elif message_text == "📅 Ближайшие встречи":
            await show_meetings(update, context)
        elif message_text == "💎 Премиум функции":
            await show_premium_features(update, context)
        else:
            await update.message.reply_text(
                "Выберите действие из меню 📱 или используйте команду /help"
            )
    
    elif state == UserState.DIARY_ENTRY:
        # Сохраняем запись в дневник
        book_id = context.user_data.get('diary_book_id')
        if book_id:
            success = db.add_diary_entry(telegram_id, book_id, message_text)
            if success:
                await update.message.reply_text(
                    "✅ Запись успешно добавлена в ваш читательский дневник!\n\n"
                    "Продолжайте делиться мыслями о прочитанном."
                )
            else:
                await update.message.reply_text(
                    "😕 Не удалось сохранить запись. Попробуйте еще раз."
                )
        set_user_state(telegram_id, UserState.NORMAL)

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать профиль пользователя"""
    user = db.get_user(update.effective_user.id)
    if user:
        await update.message.reply_text(
            f"📋 Ваша анкета:\n\n"
            f"👤 Имя: {user['name']}\n"
            f"📚 Любимые жанры: {user['favorite_genres']}\n"
            f"🎯 Цели чтения: {user['reading_goals']}\n"
            f"📅 Дата регистрации: {user['registration_date']}\n"
            f"💎 Статус: {'Премиум' if user['is_premium'] else 'Базовый'}"
        )

async def start_voting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать голосование за книгу"""
    books = db.get_books_for_voting(5)
    
    if not books:
        await update.message.reply_text(
            "😕 Пока нет книг для голосования. Администратор скоро их добавит!"
        )
        return
    
    keyboard = []
    for book in books:
        keyboard.append([InlineKeyboardButton(
            f"📖 {book['title']} - {book['author']}", 
            callback_data=f"vote_{book['id']}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🗳️ **Голосование за следующую книгу клуба**\n\n"
        "Выберите книгу, которую хотели бы прочитать вместе:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def start_diary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать работу с читательским дневником"""
    entries = db.get_user_diary_entries(update.effective_user.id)
    
    if entries:
        recent_entries = entries[:3]  # Показываем последние 3 записи
        diary_text = "📝 **Ваши последние записи:**\n\n"
        
        for entry in recent_entries:
            diary_text += f"📖 {entry['title']}\n"
            diary_text += f"📅 {entry['created_date'][:10]}\n"
            diary_text += f"{entry['notes'][:100]}...\n\n"
        
        await update.message.reply_text(diary_text, parse_mode=ParseMode.MARKDOWN)
    
    await update.message.reply_text(
        "✍️ Напишите свои мысли о прочитанной книге, "
        "и я сохраню их в ваш личный дневник:"
    )
    set_user_state(update.effective_user.id, UserState.DIARY_ENTRY)

async def get_discussion_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить вопросы для обсуждения"""
    # Для MVP используем заранее подготовленную книгу
    # В реальном приложении здесь будет текущая книга клуба
    book_title = "Мастер и Маргарита"
    book_author = "Михаил Булгаков"
    
    questions = ai_service.generate_discussion_questions(book_title, book_author)
    
    questions_text = f"❓ **Вопросы для обсуждения книги \"{book_title}\"**\n\n"
    
    for i, question in enumerate(questions, 1):
        questions_text += f"{i}. {question}\n\n"
    
    questions_text += "💡 _Эти вопросы помогут сделать обсуждение более глубоким и интересным!_"
    
    await update.message.reply_text(questions_text, parse_mode=ParseMode.MARKDOWN)

async def show_meetings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать ближайшие встречи"""
    meetings = db.get_meeting_reminders(24)  # Встречи в ближайшие 24 часа
    
    if not meetings:
        await update.message.reply_text(
            "📅 Ближайшие встречи не запланированы.\n\n"
            "Следите за объявлениями в клубе!"
        )
        return
    
    meetings_text = "📅 **Ближайшие встречи:**\n\n"
    
    for meeting in meetings:
        meetings_text += f"📖 Книга: {meeting['title']}\n"
        meetings_text += f"📅 Дата: {meeting['meeting_date']}\n"
        if meeting['meeting_url']:
            meetings_text += f"🔗 Ссылка: {meeting['meeting_url']}\n"
        if meeting['location']:
            meetings_text += f"📍 Место: {meeting['location']}\n"
        meetings_text += "\n"
    
    await update.message.reply_text(meetings_text, parse_mode=ParseMode.MARKDOWN)

async def show_premium_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать премиум функции"""
    premium_text = (
        "💎 **Премиум подписка \"Книжный Консультант\"**\n\n"
        "🎁 **Что входит:**\n\n"
        "📚 Персональная подборка книг каждый месяц\n"
        "📊 Глубокий анализ книг с ИИ-досье\n"
        "👥 Доступ к закрытому сообществу\n"
        "🎫 Эксклюзивные события и мастер-классы\n"
        "🎧 Аудио-конспекты книг\n"
        "⚡ Ранний доступ к голосованиям\n\n"
        "💰 Цена: 299₽/месяц\n\n"
        "Для оформления подписки напишите администратору @admin_username"
    )
    
    await update.message.reply_text(premium_text, parse_mode=ParseMode.MARKDOWN)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    telegram_id = update.effective_user.id
    
    if data.startswith("vote_"):
        book_id = int(data.split("_")[1])
        success = db.add_vote(telegram_id, book_id)
        
        if success:
            await query.edit_message_text(
                "✅ Ваш голос учтен! Спасибо за участие в выборе книги.\n\n"
                "Результаты голосования будут объявлены в ближайшее время."
            )
        else:
            await query.edit_message_text(
                "😕 Не удалось учесть ваш голос. Попробуйте еще раз."
            )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = (
        "📚 **Справка по Книжному клубу**\n\n"
        "🔹 **/start** - Начать работу с ботом\n"
        "🔹 **/help** - Показать эту справку\n\n"
        "📱 **Основные функции:**\n\n"
        "• **Моя анкета** - посмотреть ваш профиль\n"
        "• **Голосование за книгу** - выбрать следующую книгу\n"
        "• **Читательский дневник** - вести записи о прочитанном\n"
        "• **Вопросы для обсуждения** - получить вопросы от ИИ\n"
        "• **Ближайшие встречи** - посмотреть расписание\n"
        "• **Премиум функции** - узнать о платной подписке\n\n"
        "❓ **Нужна помощь?** Напишите администратору @admin_username"
    )
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

def main():
    """Основная функция запуска бота"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
        return
    
    # Создаем приложение
    application = Application.builder().token(token).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    logger.info("Запуск Книжного клуба бота...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
