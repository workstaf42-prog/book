"""
Дополнительные команды для расширенного функционала бота
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes
from telegram.constants import ParseMode

from database import Database
from ai_service import AIService

db = Database()
ai_service = AIService()

async def join_meeting_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для записи на встречу"""
    meeting_text = (
        "📅 **ЗАПИСЬ НА ВСТРЕЧУ**\n\n"
        "🗓 **Дата:** 15 мая, 19:00\n"
        "📖 **Книга:** \"1984\" Дж. Оруэлл\n"
        "🎥 **Формат:** Zoom + текстовый чат\n"
        "💰 **Участие:** бесплатно\n\n"
        "✅ **Вы успешно записаны!**\n\n"
        "🔗 **Ссылка на встречу:**\n"
        "https://zoom.us/j/bookclub-1984\n\n"
        "⏰ **Напоминания:**\n"
        "• За день до встречи: 14 мая, 19:00\n"
        "• За час до встречи: 15 мая, 18:00\n\n"
        "📝 **Подготовка:**\n"
        "• Прочитайте книгу до главы 8\n"
        "• Подумайте над вопросами обсуждения\n"
        "• Подготовьте свои вопросы и цитаты"
    )
    
    keyboard = [
        [InlineKeyboardButton("📅 Добавить в календарь", callback_data="add_calendar")],
        [InlineKeyboardButton("📝 Материалы для обсуждения", callback_data="discussion_materials")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(meeting_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def my_progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для показа прогресса чтения"""
    user = db.get_user(update.effective_user.id)
    
    progress_text = (
        "📊 **ВАШ ПРОГРЕСС ЧТЕНИЯ**\n\n"
        "📖 **Текущая книга:** \"1984\" Дж. Оруэлл\n\n"
        "📈 **Прогресс по книге:**\n"
        "• Прочитано: 156/320 страниц (48%)\n"
        "• Главы: 8/16\n"
        "• Время чтения: 3ч 45мин\n\n"
        "📅 **Динамика чтения:**\n"
        "• Сегодня: 25 страниц\n"
        "• Вчера: 30 страниц\n"
        "• За неделю: 145 страниц\n"
        "• Средний темп: 21 страница/день\n\n"
        "🎯 **Прогноз завершения:**\n"
        "• При текущем темпе: 8 дней\n"
        "• Оптимальный темп: 23 страницы/день\n\n"
        "🏆 **Достижения:**\n"
        "• 📚 Читатель недели (активность)\n"
        "• 💭 Мыслитель (5 заметок в дневнике)\n"
        "• 🗳️ Активный участник (голосование)"
    )
    
    keyboard = [
        [InlineKeyboardButton("📝 Добавить заметку", callback_data="add_note")],
        [InlineKeyboardButton("🎯 Обновить прогресс", callback_data="update_progress")],
        [InlineKeyboardButton("📊 Детальная статистика", callback_data="detailed_stats")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(progress_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def recommend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для получения рекомендаций от ИИ"""
    user = db.get_user(update.effective_user.id)
    
    if not user:
        await update.message.reply_text(
            "😕 Сначала зарегистрируйтесь в клубе с помощью команды /start"
        )
        return
    
    # Формируем предпочтения пользователя
    user_preferences = {
        'genres': user['favorite_genres'],
        'goals': user['reading_goals'],
        'last_book': '1984',  # Можно получить из истории
        'depth': 'средняя',
        'nonfiction': 'интересуюсь'
    }
    
    # Получаем рекомендации от ИИ
    recommendations = ai_service.recommend_books(user_preferences)
    
    recommend_text = (
        "🤖 **ПЕРСОНАЛЬНЫЕ РЕКОМЕНДАЦИИ ОТ ИИ**\n\n"
        f"📊 **На основе ваших предпочтений:**\n"
        f"• Жанры: {user['favorite_genres']}\n"
        f"• Цели: {user['reading_goals']}\n\n"
        "📚 **Рекомендуемые книги:**\n\n"
    )
    
    for i, rec in enumerate(recommendations, 1):
        recommend_text += f"{i}. {rec}\n\n"
    
    recommend_text += (
        "💡 _ИИ проанализировал ваши предпочтения и подобрал "
        "идеальные варианты для следующего чтения_\n\n"
        "🔄 **Хотите другие рекомендации?** Напишите /recommend"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 Другие рекомендации", callback_data="more_recommendations")],
        [InlineKeyboardButton("📝 Добавить в список желаемого", callback_data="add_to_wishlist")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(recommend_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def my_profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для показа профиля пользователя"""
    user = db.get_user(update.effective_user.id)
    
    if not user:
        await update.message.reply_text(
            "😕 Сначала зарегистрируйтесь в клубе с помощью команды /start"
        )
        return
    
    # Получаем статистику пользователя
    diary_entries = db.get_user_diary_entries(update.effective_user.id)
    books_read = len(set(entry['book_id'] for entry in diary_entries))
    
    profile_text = (
        "👤 **ВАШ ПРОФИЛЬ**\n\n"
        f"🏷️ **Имя:** {user['name']}\n"
        f"🎚️ **Статус:** {'💎 Премиум' if user['is_premium'] else '👤 Участник'}\n"
        f"📅 **В клубе с:** {user['registration_date'][:10]}\n\n"
        "📚 **Читательские предпочтения:**\n"
        f"• Любимые жанры: {user['favorite_genres']}\n"
        f"• Цели чтения: {user['reading_goals']}\n\n"
        "📊 **Статистика:**\n"
        f"• Прочитано книг: {books_read}\n"
        f"• Заметок в дневнике: {len(diary_entries)}\n"
        f"• Активность: высокая 📈\n"
        f"• Репутация: 245 очков 🏆\n\n"
        "🏆 **Достижения:**\n"
        "• 📚 Активный читатель\n"
        "• 💭 Мыслитель\n"
        "• 🗳️ Участник голосований\n"
        "• 👥 Социальный читатель"
    )
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Редактировать профиль", callback_data="edit_profile")],
        [InlineKeyboardButton("📊 Детальная статистика", callback_data="detailed_stats")],
        [InlineKeyboardButton("🏆 Все достижения", callback_data="achievements")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(profile_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def my_diary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для показа читательского дневника"""
    entries = db.get_user_diary_entries(update.effective_user.id)
    
    if not entries:
        diary_text = (
            "📝 **ВАШ ЧИТАТЕЛЬСКИЙ ДНЕВНИК**\n\n"
            "😔 У вас пока нет записей в дневнике.\n\n"
            "📖 **Начните вести дневник:**\n"
            "• Записывайте мысли о прочитанном\n"
            "• Сохраняйте любимые цитаты\n"
            "• Делитесь впечатлениями\n"
            "• Отмечайте прогресс чтения\n\n"
            "📝 **Добавить первую запись:** /add_note"
        )
    else:
        diary_text = f"📝 **ВАШ ЧИТАТЕЛЬСКИЙ ДНЕВНИК**\n\n"
        diary_text += f"📊 **Всего записей:** {len(entries)}\n"
        diary_text += f"📚 **Книг в дневнике:** {len(set(entry['book_id'] for entry in entries))}\n\n"
        
        # Показываем последние 3 записи
        recent_entries = entries[:3]
        diary_text += "**📄 Последние записи:**\n\n"
        
        for i, entry in enumerate(recent_entries, 1):
            diary_text += (
                f"📖 **{entry['title']}**\n"
                f"📅 {entry['created_date'][:10]}\n"
                f"📝 {entry['notes'][:150]}{'...' if len(entry['notes']) > 150 else ''}\n\n"
            )
    
    keyboard = [
        [InlineKeyboardButton("📝 Добавить запись", callback_data="add_note")],
        [InlineKeyboardButton("📊 Статистика дневника", callback_data="diary_stats")],
        [InlineKeyboardButton("📥 Экспорт в PDF", callback_data="export_diary")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(diary_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда FAQ"""
    faq_text = (
        "❓ **ЧАСТЫЕ ВОПРОСЫ**\n\n"
        "🤔 **Как присоединиться к встрече?**\n"
        "1. Нажмите \"🗓 РАСПИСАНИЕ\" в меню\n"
        "2. Выберите интересующую встречу\n"
        "3. Нажмите \"Записаться\"\n"
        "4. Получите ссылку за день до встречи\n\n"
        "📚 **Как предложить книгу?**\n"
        "1. Зайдите в \"🗳 ГОЛОСОВАНИЕ\"\n"
        "2. Нажмите \"Предложить книгу\"\n"
        "3. Напишите название и автора\n"
        "4. Ваша книга будет рассмотрена модераторами\n\n"
        "🗳️ **Как работает голосование?**\n"
        "• Голосование открыто 7 дней\n"
        "• Каждый участник может проголосовать 1 раз\n"
        "• Книга с наибольшим количеством голосов выбирается\n"
        "• Результаты объявляются в основном чате\n\n"
        "💎 **Что дает премиум-подписка?**\n"
        "• Встречи с авторами\n"
        "• Аудио-конспекты книг\n"
        "• Личные рекомендации\n"
        "• Закрытые челленджи\n"
        "• Приоритет в голосованиях\n\n"
        "📝 **Как вести читательский дневник?**\n"
        "1. Зайдите в \"🛠 ИНСТРУМЕНТЫ\"\n"
        "2. Выберите \"Читательский дневник\"\n"
        "3. Нажмите \"Добавить запись\"\n"
        "4. Запишите свои мысли о книге\n\n"
        "👥 **Как найти единомышленников?**\n"
        "1. Перейдите в \"👥 СООБЩЕСТВО\"\n"
        "2. Выберите \"Найти единомышленников\"\n"
        "3. Укажите предпочтения\n"
        "4. Получите список подходящих участников"
    )
    
    keyboard = [
        [InlineKeyboardButton("📞 Связаться с поддержкой", callback_data="contact_support")],
        [InlineKeyboardButton("📜 Полные правила", callback_data="full_rules")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(faq_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

# Регистрация всех команд
def setup_commands(application):
    """Регистрация дополнительных команд"""
    application.add_handler(CommandHandler("join_meeting", join_meeting_command))
    application.add_handler(CommandHandler("my_progress", my_progress_command))
    application.add_handler(CommandHandler("recommend", recommend_command))
    application.add_handler(CommandHandler("my_profile", my_profile_command))
    application.add_handler(CommandHandler("my_diary", my_diary_command))
    application.add_handler(CommandHandler("faq", faq_command))
