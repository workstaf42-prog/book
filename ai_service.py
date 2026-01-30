import openai
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class AIService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def recommend_books(self, user_preferences: Dict[str, Any]) -> List[str]:
        """
        Генерирует рекомендации книг на основе предпочтений пользователя
        """
        prompt = f"""
        Как книжный консультант, порекомендуй 3-5 книг для пользователя с такими предпочтениями:
        
        Любимые жанры: {user_preferences.get('genres', 'Не указаны')}
        Цели чтения: {user_preferences.get('goals', 'Не указаны')}
        Последняя понравившаяся книга: {user_preferences.get('last_book', 'Не указана')}
        Предпочитает легкое или глубокое: {user_preferences.get('depth', 'Не указано')}
        Отношение к нон-фикшен: {user_preferences.get('nonfiction', 'Не указано')}
        
        Верни только названия книг и авторов в формате:
        1. "Название книги" - Автор
        2. "Название книги" - Автор
        ...
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            recommendations = response.choices[0].message.content.strip().split('\n')
            return [rec.strip() for rec in recommendations if rec.strip()]
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return ["Извините, не удалось получить рекомендации. Попробуйте позже."]
    
    def generate_discussion_questions(self, book_title: str, book_author: str) -> List[str]:
        """
        Генерирует вопросы для обсуждения книги
        """
        prompt = f"""
        Создай 5-7 глубоких и интересных вопросов для обсуждения книги "{book_title}" автора {book_author}.
        
        Вопросы должны быть не стандартными ("понравилась ли книга?"), а заставлять задуматься:
        - Анализ персонажей и их мотивов
        - Сравнение с современностью
        - Анализ второстепенных персонажей
        - Философские темы книги
        - Скрытые смыслы и символы
        
        Верни вопросы в формате нумерованного списка.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.8
            )
            
            content = response.choices[0].message.content.strip()
            questions = []
            
            for line in content.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # Убираем нумерацию и символы
                    clean_question = line
                    if '. ' in clean_question:
                        clean_question = clean_question.split('. ', 1)[1]
                    elif '- ' in clean_question:
                        clean_question = clean_question.split('- ', 1)[1]
                    elif '• ' in clean_question:
                        clean_question = clean_question.split('• ', 1)[1]
                    
                    questions.append(clean_question.strip())
            
            return questions[:7]  # Возвращаем максимум 7 вопросов
        except Exception as e:
            print(f"Error generating questions: {e}")
            return [
                "Что вам больше всего запомнилось в книге?",
                "Какой персонаж показался самым интересным и почему?",
                "Изменила ли книга ваше мнение о чем-то важном?"
            ]
    
    def analyze_book(self, book_title: str, book_author: str) -> Dict[str, Any]:
        """
        Создает подробный анализ книги для премиум-пользователей
        """
        prompt = f"""
        Проанализируй книгу "{book_title}" автора {book_author} и создай подробное досье:
        
        1. Ключевые темы и идеи
        2. Исторический и культурный контекст
        3. Скрытые смыслы и символы
        4. Основные конфликты и их разрешение
        5. Влияние книги на литературу
        6. Почему эту книгу стоит прочитать именно сейчас
        
        Верни анализ в структурированном формате.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.7
            )
            
            return {
                "title": book_title,
                "author": book_author,
                "analysis": response.choices[0].message.content.strip(),
                "generated_at": "сейчас"
            }
        except Exception as e:
            print(f"Error analyzing book: {e}")
            return {
                "title": book_title,
                "author": book_author,
                "analysis": "К сожалению, не удалось сгенерировать анализ. Попробуйте позже.",
                "generated_at": "сейчас"
            }
    
    def generate_personal_recommendation(self, user_history: List[Dict[str, Any]], user_preferences: Dict[str, Any]) -> str:
        """
        Генерирует персональную рекомендацию для премиум-пользователей
        """
        history_text = "\n".join([f"- {book.get('title', '')} ({book.get('rating', 'без оценки')})" for book in user_history])
        
        prompt = f"""
        На основе истории чтения и предпочтений пользователя создай персональную рекомендацию:
        
        История чтения:
        {history_text}
        
        Текущие предпочтения:
        Жанры: {user_preferences.get('genres', 'Не указаны')}
        Цели: {user_preferences.get('goals', 'Не указаны')}
        
        Рекомендуй 1 книгу с подробным объяснением, почему она идеально подходит именно этому пользователю.
        Учти его историю чтения и текущие интересы.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating personal recommendation: {e}")
            return "К сожалению, не удалось сгенерировать рекомендацию. Попробуйте позже."
