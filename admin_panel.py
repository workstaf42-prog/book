import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode

from database import Database
from ai_service import AIService
from dotenv import load_dotenv

load_dotenv()

class AdminPanel:
    def __init__(self):
        self.db = Database()
        self.ai_service = AIService()
        self.admin_ids = []  # Здесь нужно указать ID администраторов
    
    def is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        return user_id in self.admin_ids
    
    async def admin_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /admin для администраторов"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("⛔ У вас нет доступа к админ-панели")
            return
        
        keyboard = [
            [KeyboardButton("📊 Статистика")],
            [KeyboardButton("📚 Добавить книгу")],
            [KeyboardButton("🗳️ Создать голосование")],
            [KeyboardButton("📅 Запланировать встречу")],
            [KeyboardButton("👥 Управление пользователями")],
            [KeyboardButton("📝 Рассылка")],
            [KeyboardButton("🔙 Выйти из админ-панели")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "🛠️ **Админ-панель Книжного клуба**\n\n"
            "Выберите действие:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_admin_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка сообщений в админ-панели"""
        if not self.is_admin(update.effective_user.id):
            return
        
        message_text = update.message.text
        
        if message_text == "📊 Статистика":
            await self.show_statistics(update, context)
        elif message_text == "📚 Добавить книгу":
            await self.start_add_book(update, context)
        elif message_text == "🗳️ Создать голосование":
            await self.create_voting(update, context)
        elif message_text == "📅 Запланировать встречу":
            await self.schedule_meeting(update, context)
        elif message_text == "👥 Управление пользователями":
            await self.manage_users(update, context)
        elif message_text == "📝 Рассылка":
            await self.start_broadcast(update, context)
        elif message_text == "🔙 Выйти из админ-панели":
            await self.exit_admin_panel(update, context)
    
    async def show_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статистику клуба"""
        try:
            # Получаем статистику (нужно добавить методы в Database)
            total_users = len(self.db.get_all_users())
            premium_users = len(self.db.get_premium_users())
            active_meetings = len(self.db.get_meeting_reminders(24*7))  # На неделю вперед
            
            stats_text = (
                "📊 **Статистика Книжного клуба**\n\n"
                f"👥 Всего пользователей: {total_users}\n"
                f"💎 Премиум-пользователей: {premium_users}\n"
                f"📅 Активных встреч: {active_meetings}\n\n"
                f"📈 Конверсия в премиум: {(premium_users/total_users*100):.1f}%\n"
                f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )
            
            await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
        
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при получении статистики: {e}")
    
    async def start_add_book(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать процесс добавления книги"""
        await update.message.reply_text(
            "📚 **Добавление новой книги**\n\n"
            "Отправьте информацию о книге в формате:\n\n"
            "Название: [название книги]\n"
            "Автор: [имя автора]\n"
            "Жанр: [жанр]\n"
            "Описание: [краткое описание]\n"
            "Обложка: [URL обложки, если есть]"
        )
    
    async def create_voting(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Создать новое голосование"""
        books = self.db.get_books_for_voting(10)
        
        if not books:
            await update.message.reply_text(
                "😕 В базе нет книг для голосования. Сначала добавьте книги."
            )
            return
        
        keyboard = []
        for book in books:
            keyboard.append([InlineKeyboardButton(
                f"📖 {book['title']} - {book['author']}", 
                callback_data=f"admin_select_book_{book['id']}"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🗳️ **Выберите книги для голосования**\n\n"
            "Отметьте книги, которые будут участвовать в голосовании:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def schedule_meeting(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запланировать встречу"""
        await update.message.reply_text(
            "📅 **Планирование встречи**\n\n"
            "Отправьте информацию в формате:\n\n"
            "Книга ID: [ID книги]\n"
            "Дата: [ГГГГ-ММ-ДД ЧЧ:ММ]\n"
            "Ссылка: [URL для онлайн-встречи]\n"
            "Место: [адрес, если офлайн]"
        )
    
    async def manage_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Управление пользователями"""
        users = self.db.get_all_users()[:10]  # Показываем первых 10 пользователей
        
        if not users:
            await update.message.reply_text("😕 Пользователей пока нет")
            return
        
        users_text = "👥 **Последние пользователи:**\n\n"
        
        for user in users:
            status = "💎" if user['is_premium'] else "👤"
            users_text += (
                f"{status} {user['name']} (ID: {user['telegram_id']})\n"
                f"📅 {user['registration_date'][:10]}\n"
                f"📚 {user['favorite_genres']}\n\n"
            )
        
        await update.message.reply_text(users_text, parse_mode=ParseMode.MARKDOWN)
    
    async def start_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать рассылку"""
        keyboard = [
            [KeyboardButton("📢 Всем пользователям")],
            [KeyboardButton("💎 Только премиум")],
            [KeyboardButton("🔙 Отмена")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "📝 **Создание рассылки**\n\n"
            "Выберите аудиторию:",
            reply_markup=reply_markup
        )
    
    async def exit_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Выйти из админ-панели"""
        keyboard = [
            [KeyboardButton("📚 Моя анкета")],
            [KeyboardButton("🗳️ Голосование за книгу")],
            [KeyboardButton("📝 Читательский дневник")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "👋 Вы вышли из админ-панели",
            reply_markup=reply_markup
        )
    
    async def handle_admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка колбэков в админ-панели"""
        query = update.callback_query
        await query.answer()
        
        if not self.is_admin(update.effective_user.id):
            return
        
        data = query.data
        
        if data.startswith("admin_select_book_"):
            book_id = int(data.split("_")[3])
            # Здесь можно добавить логику выбора книг для голосования
            await query.edit_message_text(
                f"✅ Книга с ID {book_id} добавлена в голосование"
            )

# Дополнительные методы для Database (нужно добавить в database.py)
"""
def get_all_users(self) -> List[Dict[str, Any]]:
    with sqlite3.connect(self.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY registration_date DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_premium_users(self) -> List[Dict[str, Any]]:
    with sqlite3.connect(self.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE is_premium = 1")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
"""
