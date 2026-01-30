import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from telegram.constants import ParseMode

from database import Database
from ai_service import AIService
from dotenv import load_dotenv

load_dotenv()

class NotificationScheduler:
    def __init__(self, bot_token: str):
        self.bot = Bot(token=bot_token)
        self.db = Database()
        self.ai_service = AIService()
        self.scheduler = AsyncIOScheduler()
        self.setup_jobs()
    
    def setup_jobs(self):
        """Настройка регулярных задач"""
        
        # Ежедневная проверка напоминаний о встречах (каждый час)
        self.scheduler.add_job(
            self.check_meeting_reminders,
            trigger=CronTrigger(minute=0),  # Каждый час в 0 минут
            id='meeting_reminders',
            name='Напоминания о встречах'
        )
        
        # Еженедельная генерация вопросов для обсуждения (каждое воскресенье в 10:00)
        self.scheduler.add_job(
            self.generate_weekly_questions,
            trigger=CronTrigger(day_of_week=6, hour=10, minute=0),  # Воскресенье
            id='weekly_questions',
            name='Еженедельные вопросы для обсуждения'
        )
        
        # Ежемесячные персональные рекомендации для премиум-пользователей (1 числа каждого месяца)
        self.scheduler.add_job(
            self.send_monthly_recommendations,
            trigger=CronTrigger(day=1, hour=9, minute=0),
            id='monthly_recommendations',
            name='Ежемесячные рекомендации'
        )
    
    async def check_meeting_reminders(self):
        """Проверка и отправка напоминаний о встречах"""
        print(f"[{datetime.now()}] Проверка напоминаний о встречах...")
        
        # Напоминания за день
        meetings_tomorrow = self.db.get_meeting_reminders(24)
        for meeting in meetings_tomorrow:
            await self.send_meeting_reminder(meeting, "day")
        
        # Напоминания за час (проверяем встречи в ближайший час)
        meetings_soon = self.db.get_meeting_reminders(1)
        for meeting in meetings_soon:
            await self.send_meeting_reminder(meeting, "hour")
    
    async def send_meeting_reminder(self, meeting: dict, reminder_type: str):
        """Отправка напоминания о встрече"""
        try:
            # Получаем всех пользователей для рассылки
            users = self.db.get_all_users()  # Нужно добавить этот метод в Database
            
            if reminder_type == "day":
                message = (
                    f"🔔 **Напоминание о встрече!**\n\n"
                    f"📖 Книга: {meeting['title']}\n"
                    f"📅 Завтра, {meeting['meeting_date']}\n"
                )
                if meeting['meeting_url']:
                    message += f"🔗 Ссылка: {meeting['meeting_url']}\n"
                if meeting['location']:
                    message += f"📍 Место: {meeting['location']}\n"
                message += "\nНе забудьте подготовиться к обсуждению! 📚"
            
            elif reminder_type == "hour":
                message = (
                    f"⏰ **Встреча начинается через час!**\n\n"
                    f"📖 Обсуждаем: {meeting['title']}\n"
                    f"📅 Сегодня, {meeting['meeting_date']}\n"
                )
                if meeting['meeting_url']:
                    message += f"🔗 Присоединяйтесь: {meeting['meeting_url']}\n"
                if meeting['location']:
                    message += f"📍 Ждем вас: {meeting['location']}\n"
                message += "\nДо встречи! 🎉"
            
            # Отправляем сообщение всем пользователям
            for user in users:
                try:
                    await self.bot.send_message(
                        chat_id=user['telegram_id'],
                        text=message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    print(f"Ошибка отправки напоминания пользователю {user['telegram_id']}: {e}")
        
        except Exception as e:
            print(f"Ошибка в отправке напоминания о встрече: {e}")
    
    async def generate_weekly_questions(self):
        """Генерация еженедельных вопросов для обсуждения"""
        print(f"[{datetime.now()}] Генерация еженедельных вопросов...")
        
        try:
            # Получаем текущую книгу для обсуждения (нужно добавить метод)
            current_book = self.db.get_current_book()  # Нужно добавить этот метод
            
            if current_book:
                questions = self.ai_service.generate_discussion_questions(
                    current_book['title'], 
                    current_book['author']
                )
                
                # Сохраняем вопросы в базу
                self.db.save_discussion_questions(current_book['id'], questions)
                
                # Отправляем уведомление о готовности вопросов
                users = self.db.get_all_users()
                message = (
                    f"📝 **Новые вопросы для обсуждения!**\n\n"
                    f"📖 Книга: {current_book['title']}\n"
                    f"❓ Сгенерировано {len(questions)} уникальных вопросов\n\n"
                    "Используйте команду 'Вопросы для обсуждения' в меню бота, "
                    "чтобы получить их и подготовиться к встрече!"
                )
                
                for user in users:
                    try:
                        await self.bot.send_message(
                            chat_id=user['telegram_id'],
                            text=message,
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except Exception as e:
                        print(f"Ошибка отправки уведомления о вопросах пользователю {user['telegram_id']}: {e}")
        
        except Exception as e:
            print(f"Ошибка в генерации еженедельных вопросов: {e}")
    
    async def send_monthly_recommendations(self):
        """Отправка ежемесячных персональных рекомендаций премиум-пользователям"""
        print(f"[{datetime.now()}] Отправка ежемесячных рекомендаций...")
        
        try:
            # Получаем всех премиум-пользователей
            premium_users = self.db.get_premium_users()  # Нужно добавить этот метод
            
            for user in premium_users:
                # Получаем историю чтения пользователя
                user_history = self.db.get_user_diary_entries(user['telegram_id'])
                
                # Получаем предпочтения пользователя
                user_preferences = {
                    'genres': user['favorite_genres'],
                    'goals': user['reading_goals']
                }
                
                # Генерируем персональную рекомендацию
                recommendation = self.ai_service.generate_personal_recommendation(
                    user_history, 
                    user_preferences
                )
                
                message = (
                    f"🎁 **Ваша персональная рекомендация этого месяца**\n\n"
                    f"{recommendation}\n\n"
                    f"💎 _Премиум-функция Книжного Консультанта_"
                )
                
                try:
                    await self.bot.send_message(
                        chat_id=user['telegram_id'],
                        text=message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    print(f"Ошибка отправки рекомендации пользователю {user['telegram_id']}: {e}")
        
        except Exception as e:
            print(f"Ошибка в отправке ежемесячных рекомендаций: {e}")
    
    def start(self):
        """Запуск планировщика"""
        self.scheduler.start()
        print("Планировщик уведомлений запущен")
    
    def stop(self):
        """Остановка планировщика"""
        self.scheduler.shutdown()
        print("Планировщик уведомлений остановлен")

# Дополнительные методы для Database (нужно добавить в database.py)
"""
def get_all_users(self) -> List[Dict[str, Any]]:
    with sqlite3.connect(self.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_current_book(self) -> Optional[Dict[str, Any]]:
    with sqlite3.connect(self.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.* FROM books b
            JOIN meetings m ON b.id = m.book_id
            WHERE m.is_active = 1 AND m.meeting_date > datetime('now')
            ORDER BY m.meeting_date ASC
            LIMIT 1
        """)
        row = cursor.fetchone()
        return dict(row) if row else None

def get_premium_users(self) -> List[Dict[str, Any]]:
    with sqlite3.connect(self.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE is_premium = 1")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
"""
