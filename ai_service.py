import openai
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class AIService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
            self.active = True
            print("✅ AI Service initialized")
        else:
            self.client = None
            self.active = False
            print("⚠️ OpenAI API key not found. AI features disabled.")
    
    def generate_discussion_questions(self, book_title: str, book_author: str) -> List[str]:
        """Генерирует вопросы для обсуждения книги"""
        if not self.active:
            return [
                "Что вам больше всего запомнилось в книге?",
                "Какой персонаж показался самым интересным и почему?",
                "Изменила ли книга ваше мнение о чем-то важном?"
            ]
        
        try:
            prompt = f"""
            Создай 5 интересных вопросов для обсуждения книги "{book_title}" автора {book_author}.
            
            Вопросы должны быть не стандартными ("понравилась ли книга?"), а заставлять задуматься:
            - Анализ персонажей и их мотивов
            - Сравнение с современностью
            - Анализ второстепенных персонажей
            - Философские темы книги
            - Скрытые смыслы и символы
            
            Верни вопросы в нумерованном списке.
            """
            
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
                    clean_question = line
                    if '. ' in clean_question:
                        clean_question = clean_question.split('. ', 1)[1]
                    elif '- ' in clean_question:
                        clean_question = clean_question.split('- ', 1)[1]
                    elif '• ' in clean_question:
                        clean_question = clean_question.split('• ', 1)[1]
                    
                    questions.append(clean_question.strip())
            
            return questions[:7]
        
        except Exception as e:
            print(f"Error generating questions: {e}")
            return [
                "Что вам больше всего запомнилось в книге?",
                "Какой персонаж показался самым интересным и почему?",
                "Изменила ли книга ваше мнение о чем-то важном?"
            ]
    
    def recommend_books(self, user_preferences: Dict[str, Any]) -> List[str]:
        """Генерирует рекомендации книг на основе предпочтений пользователя"""
        if not self.active:
            return ["Изучите наш каталог книг в меню голосования!"]
        
        try:
            prompt = f"""
            Как книжный консультант, порекомендуй 3-5 книг для пользователя с такими предпочтениями:
            
            Любимые жанры: {user_preferences.get('genres', 'Не указаны')}
            Цели чтения: {user_preferences.get('goals', 'Не указаны')}
            Последняя понравившаяся книга: {user_preferences.get('last_book', 'Не указана')}
            Предпочитает легкое или глубокое: {user_preferences.get('depth', 'Не указано')}
            
            Верни только названия книг и авторов в формате:
            1. "Название книги" - Автор
            2. "Название книги" - Автор
            ...
            """
            
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