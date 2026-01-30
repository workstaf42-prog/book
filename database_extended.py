"""
Расширенные функции для работы с базой данных, включая систему тестирования
"""

import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any

class DatabaseExtended:
    def __init__(self, db_path: str = "bookclub.db"):
        self.db_path = db_path
    
    def get_book_by_id(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Получает книгу по ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def save_test_results(self, user_id: int, book_id: int, total_questions: int, 
                         correct_answers: int, percentage: float, time_spent: int = 0) -> int:
        """Сохраняет результаты теста"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO test_results (user_id, book_id, total_questions, correct_answers, percentage, time_spent)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, book_id, total_questions, correct_answers, percentage, time_spent))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Error saving test results: {e}")
            return -1
    
    def save_test_answers(self, test_result_id: int, answers: List[Dict[str, Any]]) -> bool:
        """Сохраняет подробные ответы на вопросы теста"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for answer in answers:
                    cursor.execute("""
                        INSERT INTO test_answers (test_result_id, question_text, user_answer, correct_answer, is_correct, category, difficulty)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        test_result_id,
                        answer.get('question', ''),
                        answer.get('user_answer', ''),
                        answer.get('correct_answer', ''),
                        1 if answer.get('is_correct', False) else 0,
                        answer.get('category', ''),
                        answer.get('difficulty', '')
                    ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving test answers: {e}")
            return False
    
    def get_user_test_statistics(self, user_id: int) -> Dict[str, Any]:
        """Получает статистику тестов пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Общая статистика
                cursor.execute("""
                    SELECT COUNT(*) as total_tests, 
                           AVG(percentage) as average_score,
                           MAX(percentage) as best_score
                    FROM test_results WHERE user_id = ?
                """, (user_id,))
                
                stats_row = cursor.fetchone()
                
                # Статистика по книгам
                cursor.execute("""
                    SELECT tr.book_id, b.title, b.author, tr.percentage, tr.test_date
                    FROM test_results tr
                    JOIN books b ON tr.book_id = b.id
                    WHERE tr.user_id = ?
                    ORDER BY tr.test_date DESC
                """, (user_id,))
                
                books_tested = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'total_tests': stats_row['total_tests'] or 0,
                    'average_score': round(stats_row['average_score'] or 0, 1),
                    'best_score': stats_row['best_score'] or 0,
                    'books_tested': books_tested
                }
        except Exception as e:
            print(f"Error getting user test statistics: {e}")
            return {
                'total_tests': 0,
                'average_score': 0,
                'best_score': 0,
                'books_tested': []
            }
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получает всех пользователей"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY registration_date DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_premium_users(self) -> List[Dict[str, Any]]:
        """Получает премиум-пользователей"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE is_premium = 1")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_current_book(self) -> Optional[Dict[str, Any]]:
        """Получает текущую книгу клуба"""
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
    
    def get_test_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает историю тестов пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tr.*, b.title, b.author
                FROM test_results tr
                JOIN books b ON tr.book_id = b.id
                WHERE tr.user_id = ?
                ORDER BY tr.test_date DESC
                LIMIT ?
            """, (user_id, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_category_performance(self, user_id: int) -> Dict[str, Dict[str, Any]]:
        """Анализирует производительность пользователя по категориям вопросов"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ta.category, 
                           COUNT(*) as total_questions,
                           SUM(ta.is_correct) as correct_answers,
                           AVG(ta.is_correct) * 100 as percentage
                    FROM test_answers ta
                    JOIN test_results tr ON ta.test_result_id = tr.id
                    WHERE tr.user_id = ? AND ta.category != ''
                    GROUP BY ta.category
                """, (user_id,))
                
                rows = cursor.fetchall()
                performance = {}
                
                for row in rows:
                    performance[row['category']] = {
                        'total_questions': row['total_questions'],
                        'correct_answers': row['correct_answers'],
                        'percentage': round(row['percentage'], 1)
                    }
                
                return performance
        except Exception as e:
            print(f"Error getting category performance: {e}")
            return {}
    
    def get_user_weak_areas(self, user_id: int) -> List[str]:
        """Определяет слабые области пользователя"""
        performance = self.get_category_performance(user_id)
        weak_areas = []
        
        for category, stats in performance.items():
            if stats['percentage'] < 60:  # Меньше 60% считаем слабой областью
                weak_areas.append(category)
        
        return weak_areas
