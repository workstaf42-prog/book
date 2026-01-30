"""
Расширенный ИИ-сервис с функциями генерации тестов
"""

import openai
import os
from typing import List, Dict, Any
import asyncio
from dotenv import load_dotenv

load_dotenv()

class EnhancedAIService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def generate_comprehensive_test(self, book_title: str, book_author: str, user_level: str = "intermediate") -> Dict[str, Any]:
        """
        Генерирует комплексный тест по книге с разными типами вопросов
        """
        level_descriptions = {
            "beginner": "для начинающих читателей, проверяет базовое понимание сюжета",
            "intermediate": "для средний уровень, включает анализ персонажей и тем",
            "advanced": "для продвинутых, глубокий анализ символов и философских идей"
        }
        
        level_desc = level_descriptions.get(user_level, level_descriptions["intermediate"])
        
        prompt = f"""
        Создай комплексный тест по книге "{book_title}" автора {book_author}.
        Уровень сложности: {level_desc}.
        
        Тест должен включать 15 вопросов разных типов:
        
        1. **Вопросы на знание сюжета (5 вопросов):**
           - Что произошло в ключевых моментах?
           - В какой последовательности развивались события?
        
        2. **Вопросы на понимание персонажей (4 вопроса):**
           - Мотивация героев
           - Развитие персонажей
           - Отношения между персонажами
        
        3. **Вопросы на анализ тем и идей (3 вопроса):**
           - Основные темы книги
           - Скрытые смыслы
           - Философские идеи
        
        4. **Вопросы на знание цитат (2 вопроса):**
           - Узнавание цитат
           - Атрибутация цитат персонажам
        
        5. **Вопросы на контекст (1 вопрос):**
           - Исторический или культурный контекст
        
        Формат каждого вопроса:
        Q: [текст вопроса]
        TYPE: [multiple_choice|true_false|short_answer]
        A: [правильный ответ]
        W1: [неправильный вариант 1]
        W2: [неправильный вариант 2]
        W3: [неправильный вариант 3]
        DIFFICULTY: [easy|medium|hard]
        CATEGORY: [plot|character|theme|quote|context]
        EXPLANATION: [пояснение правильного ответа]
        
        Сделай вопросы интересными и глубокими.
        """
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=3000,
                    temperature=0.7
                )
            )
            
            content = response.choices[0].message.content.strip()
            return self.parse_comprehensive_test(content, book_title, book_author)
        
        except Exception as e:
            print(f"Error generating comprehensive test: {e}")
            return {}
    
    def parse_comprehensive_test(self, content: str, book_title: str, book_author: str) -> Dict[str, Any]:
        """Парсит комплексный тест"""
        questions = []
        current_question = {}
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('Q:'):
                if current_question:
                    questions.append(current_question)
                current_question = {
                    'question': line[2:].strip(),
                    'type': 'multiple_choice',
                    'correct_answer': '',
                    'wrong_answers': [],
                    'difficulty': 'medium',
                    'category': 'plot',
                    'explanation': ''
                }
            elif line.startswith('TYPE:'):
                current_question['type'] = line[5:].strip()
            elif line.startswith('A:'):
                current_question['correct_answer'] = line[2:].strip()
            elif line.startswith('W1:'):
                current_question['wrong_answers'].append(line[3:].strip())
            elif line.startswith('W2:'):
                current_question['wrong_answers'].append(line[3:].strip())
            elif line.startswith('W3:'):
                current_question['wrong_answers'].append(line[3:].strip())
            elif line.startswith('DIFFICULTY:'):
                current_question['difficulty'] = line[11:].strip()
            elif line.startswith('CATEGORY:'):
                current_question['category'] = line[9:].strip()
            elif line.startswith('EXPLANATION:'):
                current_question['explanation'] = line[12:].strip()
        
        if current_question:
            questions.append(current_question)
        
        return {
            'book_title': book_title,
            'book_author': book_author,
            'questions': questions,
            'total_questions': len(questions),
            'categories': list(set(q['category'] for q in questions)),
            'difficulties': list(set(q['difficulty'] for q in questions))
        }
    
    async def generate_adaptive_questions(self, book_title: str, book_author: str, 
                                         user_performance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Генерирует адаптивные вопросы на основе производительности пользователя
        """
        # Анализируем слабые места пользователя
        weak_categories = user_performance.get('weak_categories', [])
        average_score = user_performance.get('average_score', 70)
        
        if average_score < 50:
            difficulty = "easy"
            focus = "basic understanding"
        elif average_score < 80:
            difficulty = "medium"
            focus = "deeper analysis"
        else:
            difficulty = "hard"
            focus = "advanced themes"
        
        prompt = f"""
        Создай 5 адаптивных вопросов для книги "{book_title}" автора {book_author}.
        
        Параметры адаптации:
        - Уровень сложности: {difficulty}
        - Фокус: {focus}
        - Слабые категории пользователя: {', '.join(weak_categories) if weak_categories else 'нет'}
        
        Создай вопросы, которые помогут пользователю улучшить понимание в слабых областях.
        Используй тот же формат, что и в основном тесте.
        
        Сделай вопросы более сфокусированными на областях, где пользователь испытывает трудности.
        """
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1500,
                    temperature=0.7
                )
            )
            
            content = response.choices[0].message.content.strip()
            parsed = self.parse_comprehensive_test(content, book_title, book_author)
            return parsed.get('questions', [])
        
        except Exception as e:
            print(f"Error generating adaptive questions: {e}")
            return []
    
    async def generate_book_analysis_report(self, book_title: str, book_author: str, 
                                          test_results: Dict[str, Any]) -> str:
        """
        Генерирует подробный отчет на основе результатов теста
        """
        correct_answers = test_results.get('correct_answers', 0)
        total_questions = test_results.get('total_questions', 1)
        percentage = (correct_answers / total_questions) * 100
        
        # Анализируем категории
        category_performance = test_results.get('category_performance', {})
        
        prompt = f"""
        Проанализируй результаты теста по книге "{book_title}" и создай подробный отчет.
        
        Результаты:
        - Общий балл: {percentage:.1f}% ({correct_answers}/{total_questions})
        - Производительность по категориям: {category_performance}
        
        Создай отчет, включающий:
        1. Общую оценку понимания книги
        2. Анализ сильных и слабых сторон
        3. Рекомендации по дальнейшему чтению
        4. Какие аспекты книги стоит изучить глубже
        5. Предложения по дополнительным материалам
        
        Сделай отчет мотивирующим и конструктивным.
        """
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000,
                    temperature=0.7
                )
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Error generating analysis report: {e}")
            return "Не удалось сгенерировать отчет. Попробуйте позже."
    
    async def generate_personalized_recommendations(self, book_title: str, 
                                                   test_results: Dict[str, Any]) -> List[str]:
        """
        Генерирует персонализированные рекомендации на основе результатов теста
        """
        percentage = test_results.get('percentage', 0)
        weak_areas = test_results.get('weak_areas', [])
        
        if percentage >= 80:
            level = "advanced"
            focus = "complex themes and similar authors"
        elif percentage >= 60:
            level = "intermediate"
            focus = "deeper understanding of similar genres"
        else:
            level = "beginner"
            focus = "more accessible books in similar themes"
        
        prompt = f"""
        Пользователь прошел тест по книге "{book_title}" с результатом {percentage}%.
        Слабые области: {', '.join(weak_areas) if weak_areas else 'нет'}
        
        Рекомендуй 3-5 книг для дальнейшего чтения.
        Уровень сложности: {level}
        Фокус: {focus}
        
        Каждая рекомендация должна включать:
        - Название книги и автор
        - Почему эта книга подойдет именно этому пользователю
        - Как она поможет улучшить слабые области
        
        Формат:
        1. "Название книги" - Автор
           Почему: [объяснение]
           Поможет: [как поможет]
        """
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,
                    temperature=0.7
                )
            )
            
            content = response.choices[0].message.content.strip()
            recommendations = content.split('\n')
            return [rec.strip() for rec in recommendations if rec.strip()]
        
        except Exception as e:
            print(f"Error generating personalized recommendations: {e}")
            return ["Попробуйте перечитать книгу через некоторое время для лучшего понимания."]
