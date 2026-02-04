import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any

class Database:
    def __init__(self, db_path: str = "bookclub.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,
                    name TEXT,
                    favorite_genres TEXT,
                    reading_goals TEXT,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_premium INTEGER DEFAULT 0
                )
            """)
            
            # Таблица книг
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    author TEXT,
                    genre TEXT,
                    description TEXT,
                    cover_url TEXT,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица голосований
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS votes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER,
                    user_id INTEGER,
                    vote_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (book_id) REFERENCES books (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Таблица встреч
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meetings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER,
                    meeting_date TIMESTAMP,
                    meeting_url TEXT,
                    location TEXT,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (book_id) REFERENCES books (id)
                )
            """)
            
            # Таблица вопросов для обсуждения
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS discussion_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER,
                    question TEXT,
                    generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (book_id) REFERENCES books (id)
                )
            """)
            
            # Таблица читательских дневников
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reading_diaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    book_id INTEGER,
                    notes TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (book_id) REFERENCES books (id)
                )
            """)
            
            # Таблица результатов тестов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    book_id INTEGER,
                    total_questions INTEGER,
                    correct_answers INTEGER,
                    percentage REAL,
                    test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    time_spent INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (book_id) REFERENCES books (id)
                )
            """)
            
            # Таблица ответов на вопросы теста
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_result_id INTEGER,
                    question_text TEXT,
                    user_answer TEXT,
                    correct_answer TEXT,
                    is_correct INTEGER,
                    category TEXT,
                    difficulty TEXT,
                    FOREIGN KEY (test_result_id) REFERENCES test_results (id)
                )
            """)
            
            conn.commit()
    
    def register_user(self, telegram_id: int, name: str, favorite_genres: str, reading_goals: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO users (telegram_id, name, favorite_genres, reading_goals)
                    VALUES (?, ?, ?, ?)
                """, (telegram_id, name, favorite_genres, reading_goals))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error registering user: {e}")
            return False
    
    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def add_book(self, title: str, author: str, genre: str, description: str = "", cover_url: str = "") -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO books (title, author, genre, description, cover_url)
                VALUES (?, ?, ?, ?, ?)
            """, (title, author, genre, description, cover_url))
            conn.commit()
            return cursor.lastrowid
    
    def get_books_for_voting(self, limit: int = 5) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM books ORDER BY RANDOM() LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def add_vote(self, telegram_id: int, book_id: int) -> bool:
        user = self.get_user(telegram_id)
        if not user:
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO votes (book_id, user_id)
                    VALUES (?, ?)
                """, (book_id, user['id']))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding vote: {e}")
            return False
    
    def get_meeting_reminders(self, hours_ahead: int = 24) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.*, b.title, b.author 
                FROM meetings m
                JOIN books b ON m.book_id = b.id
                WHERE m.is_active = 1 
                AND datetime(m.meeting_date) BETWEEN datetime('now') 
                AND datetime('now', '+{} hours')
            """.format(hours_ahead))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def save_discussion_questions(self, book_id: int, questions: List[str]) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for question in questions:
                    cursor.execute("""
                        INSERT INTO discussion_questions (book_id, question)
                        VALUES (?, ?)
                    """, (book_id, question))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving questions: {e}")
            return False
    
    def add_diary_entry(self, telegram_id: int, book_id: int, notes: str) -> bool:
        user = self.get_user(telegram_id)
        if not user:
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO reading_diaries (user_id, book_id, notes)
                    VALUES (?, ?, ?)
                """, (user['id'], book_id, notes))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding diary entry: {e}")
            return False
    
    def get_user_diary_entries(self, telegram_id: int, book_id: Optional[int] = None) -> List[Dict[str, Any]]:
        user = self.get_user(telegram_id)
        if not user:
            return []
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if book_id:
                cursor.execute("""
                    SELECT rd.*, b.title, b.author 
                    FROM reading_diaries rd
                    JOIN books b ON rd.book_id = b.id
                    WHERE rd.user_id = ? AND rd.book_id = ?
                    ORDER BY rd.created_date DESC
                """, (user['id'], book_id))
            else:
                cursor.execute("""
                    SELECT rd.*, b.title, b.author 
                    FROM reading_diaries rd
                    JOIN books b ON rd.book_id = b.id
                    WHERE rd.user_id = ?
                    ORDER BY rd.created_date DESC
                """, (user['id'],))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    # Добавьте эти методы в конец класса Database
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получить всех пользователей"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY registration_date DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_premium_users(self) -> List[Dict[str, Any]]:
        """Получить премиум пользователей"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE is_premium = 1")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_meeting_reminders(self, hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """Получить встречи на ближайшие N часов"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.*, b.title, b.author 
                FROM meetings m
                JOIN books b ON m.book_id = b.id
                WHERE m.is_active = 1 
                AND datetime(m.meeting_date) BETWEEN datetime('now')
                AND datetime('now', ?)
            """, (f'+{hours_ahead} hours',))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_books_for_voting(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить книги для голосования"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM books 
                ORDER BY added_date DESC 
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def update_user(self, telegram_id: int, **kwargs) -> bool:
        """Обновить данные пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
                values = list(kwargs.values())
                values.append(telegram_id)
                cursor.execute(f"""
                    UPDATE users 
                    SET {set_clause}
                    WHERE telegram_id = ?
                """, values)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
