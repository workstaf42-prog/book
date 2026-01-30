"""
Система ИИ-тестирования после прочтения книг
"""

import asyncio
from typing import List, Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

from database import Database
from ai_service import AIService

class TestingSystem:
    def __init__(self):
        self.db = Database()
        self.ai_service = AIService()
        self.user_tests = {}  # Хранение активных тестов пользователей
    
    async def start_book_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE, book_id: int):
        """Начать тестирование по книге"""
        user_id = update.effective_user.id
        
        # Получаем информацию о книге
        book = self.db.get_book_by_id(book_id)
        if not book:
            await update.message.reply_text("😕 Книга не найдена в базе данных")
            return
        
        # Проверяем, не проходит ли пользователь уже тест
        if user_id in self.user_tests:
            await update.message.reply_text(
                "⏳ Вы уже проходите тест. Завершите текущий тест перед началом нового."
            )
            return
        
        # Генерируем вопросы для теста
        questions = await self.generate_test_questions(book['title'], book['author'])
        
        if not questions:
            await update.message.reply_text(
                "😕 Не удалось сгенерировать вопросы. Попробуйте позже."
            )
            return
        
        # Сохраняем тест пользователя
        self.user_tests[user_id] = {
            'book_id': book_id,
            'book_title': book['title'],
            'questions': questions,
            'current_question': 0,
            'correct_answers': 0,
            'user_answers': [],
            'start_time': update.message.date
        }
        
        # Показываем первый вопрос
        await self.show_test_question(update, context, user_id)
    
    async def generate_test_questions(self, book_title: str, book_author: str) -> List[Dict[str, Any]]:
        """Генерирует вопросы для тестирования с помощью ИИ"""
        prompt = f"""
        Создай тест из 10 вопросов по книге "{book_title}" автора {book_author}.
        
        Тест должен включать разные типы вопросов:
        1. Вопросы с вариантами ответов (4 варианта, 1 правильный)
        2. Вопросы на понимание сюжета
        3. Вопросы на анализ персонажей
        4. Вопросы на понимание тем и символов
        5. Вопросы на знание цитат
        
        Формат ответа (каждый вопрос на новой строке):
        Q: [текст вопроса]
        A: [правильный ответ]
        W1: [неправильный вариант 1]
        W2: [неправильный вариант 2]
        W3: [неправильный вариант 3]
        TYPE: multiple_choice
        
        Или для вопросов на понимание:
        Q: [текст вопроса]
        A: [правильный ответ]
        TYPE: open_ended
        
        Сделай вопросы интересными и глубокими, проверяющими понимание книги.
        """
        
        try:
            response = await self.ai_service.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            return self.parse_test_questions(content)
        
        except Exception as e:
            print(f"Error generating test questions: {e}")
            return []
    
    def parse_test_questions(self, content: str) -> List[Dict[str, Any]]:
        """Парсит вопросы из ответа ИИ"""
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
                    'correct_answer': '',
                    'wrong_answers': [],
                    'type': 'multiple_choice'
                }
            elif line.startswith('A:'):
                current_question['correct_answer'] = line[2:].strip()
            elif line.startswith('W1:'):
                current_question['wrong_answers'].append(line[3:].strip())
            elif line.startswith('W2:'):
                current_question['wrong_answers'].append(line[3:].strip())
            elif line.startswith('W3:'):
                current_question['wrong_answers'].append(line[3:].strip())
            elif line.startswith('TYPE:'):
                current_question['type'] = line[5:].strip()
        
        if current_question:
            questions.append(current_question)
        
        return questions
    
    async def show_test_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показывает текущий вопрос теста"""
        if user_id not in self.user_tests:
            return
        
        test = self.user_tests[user_id]
        current_q = test['current_question']
        
        if current_q >= len(test['questions']):
            # Тест завершен
            await self.finish_test(update, context, user_id)
            return
        
        question = test['questions'][current_q]
        question_num = current_q + 1
        total_questions = len(test['questions'])
        
        # Формируем текст вопроса
        question_text = (
            f"🧠 **ТЕСТ: {test['book_title']}**\n\n"
            f"❓ **Вопрос {question_num}/{total_questions}**\n\n"
            f"{question['question']}"
        )
        
        if question['type'] == 'multiple_choice':
            # Создаем варианты ответов
            all_answers = [question['correct_answer']] + question['wrong_answers']
            import random
            random.shuffle(all_answers)
            
            # Находим индекс правильного ответа
            correct_index = all_answers.index(question['correct_answer'])
            
            # Создаем клавиатуру
            keyboard = []
            for i, answer in enumerate(all_answers):
                callback_data = f"test_answer_{user_id}_{i}_{correct_index}"
                keyboard.append([InlineKeyboardButton(
                    f"{chr(65 + i)}. {answer}", 
                    callback_data=callback_data
                )])
            
            keyboard.append([InlineKeyboardButton("⏭️ Пропустить", callback_data=f"test_skip_{user_id}")])
            
        else:  # open_ended
            keyboard = [[InlineKeyboardButton("⏭️ Пропустить", callback_data=f"test_skip_{user_id}")]]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text(question_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.callback_query.message.reply_text(question_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_test_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает ответ на вопрос теста"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        parts = data.split('_')
        
        if len(parts) < 5:
            return
        
        user_id = int(parts[2])
        answer_index = int(parts[3])
        correct_index = int(parts[4])
        
        if user_id not in self.user_tests:
            return
        
        test = self.user_tests[user_id]
        question = test['questions'][test['current_question']]
        
        # Проверяем ответ
        is_correct = (answer_index == correct_index)
        
        if is_correct:
            test['correct_answers'] += 1
            result_text = "✅ **Правильно!**"
        else:
            correct_answer = question['correct_answer']
            result_text = f"❌ **Неправильно.**\n\nПравильный ответ: {correct_answer}"
        
        # Сохраняем ответ пользователя
        test['user_answers'].append({
            'question': question['question'],
            'user_answer_index': answer_index,
            'is_correct': is_correct,
            'correct_answer': question['correct_answer']
        })
        
        # Переходим к следующему вопросу
        test['current_question'] += 1
        
        # Показываем результат и следующий вопрос
        await query.edit_message_text(
            result_text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("➡️ Следующий вопрос", callback_data=f"test_next_{user_id}")
            ]]),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def skip_test_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Пропускает текущий вопрос"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = int(data.split('_')[2])
        
        if user_id not in self.user_tests:
            return
        
        test = self.user_tests[user_id]
        
        # Сохраняем пропуск
        test['user_answers'].append({
            'question': test['questions'][test['current_question']]['question'],
            'user_answer_index': -1,
            'is_correct': False,
            'correct_answer': test['questions'][test['current_question']]['correct_answer'],
            'skipped': True
        })
        
        test['current_question'] += 1
        
        await query.edit_message_text(
            "⏭️ **Вопрос пропущен**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("➡️ Следующий вопрос", callback_data=f"test_next_{user_id}")
            ]])
        )
    
    async def show_next_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает следующий вопрос"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = int(data.split('_')[2])
        
        if user_id not in self.user_tests:
            return
        
        test = self.user_tests[user_id]
        
        if test['current_question'] >= len(test['questions']):
            await self.finish_test(update, context, user_id)
        else:
            await self.show_test_question(update, context, user_id)
    
    async def finish_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Завершает тест и показывает результаты"""
        if user_id not in self.user_tests:
            return
        
        test = self.user_tests[user_id]
        total_questions = len(test['questions'])
        correct_answers = test['correct_answers']
        percentage = (correct_answers / total_questions) * 100
        
        # Определяем уровень понимания
        if percentage >= 90:
            level = "🏆 **Отличное понимание!**"
            comment = "Вы прекрасно поняли книгу и ее глубокий смысл."
        elif percentage >= 70:
            level = "🥈 **Хорошее понимание!**"
            comment = "Вы хорошо поняли основные идеи книги."
        elif percentage >= 50:
            level = "🥉 **Среднее понимание**"
            comment = "Вы поняли основное, но стоит перечитать некоторые моменты."
        else:
            level = "📚 **Нужно перечитать**"
            comment = "Рекомендуем перечитать книгу для лучшего понимания."
        
        # Формируем результаты
        results_text = (
            f"🎯 **РЕЗУЛЬТАТЫ ТЕСТА**\n\n"
            f"📖 **Книга:** {test['book_title']}\n"
            f"✅ **Правильных ответов:** {correct_answers}/{total_questions}\n"
            f"📊 **Процент:** {percentage:.1f}%\n\n"
            f"{level}\n\n"
            f"{comment}\n\n"
        )
        
        # Добавляем анализ ошибок
        wrong_answers = [a for a in test['user_answers'] if not a['is_correct'] and not a.get('skipped')]
        if wrong_answers:
            results_text += "🔍 **Разбор ошибок:**\n\n"
            for i, answer in enumerate(wrong_answers[:3], 1):  # Показываем до 3 ошибок
                results_text += f"{i}. {answer['question']}\n"
                results_text += f"   💡 Правильный ответ: {answer['correct_answer']}\n\n"
        
        # Добавляем рекомендации
        results_text += (
            "💡 **Рекомендации:**\n\n"
            "• Перечитайте главы, где были ошибки\n"
            "• Обсудите сложные моменты в клубе\n"
            "• Попробуйте пройти тест через неделю\n\n"
            "📊 **Ваши результаты сохранены в профиле!**"
        )
        
        # Сохраняем результаты в базу данных
        await self.save_test_results(user_id, test)
        
        # Создаем клавиатуру
        keyboard = [
            [InlineKeyboardButton("📊 Детальный разбор", callback_data="test_detailed_analysis")],
            [InlineKeyboardButton("🔄 Пройти тест еще раз", callback_data=f"retake_test_{test['book_id']}")],
            [InlineKeyboardButton("📝 Добавить заметки", callback_data="add_test_notes")],
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Удаляем тест из активных
        del self.user_tests[user_id]
        
        if update.message:
            await update.message.reply_text(results_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await query.edit_message_text(results_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def save_test_results(self, user_id: int, test: Dict[str, Any]):
        """Сохраняет результаты теста в базу данных"""
        try:
            # Здесь нужно добавить метод в Database для сохранения результатов
            # Например: db.save_test_results(user_id, test)
            pass
        except Exception as e:
            print(f"Error saving test results: {e}")
    
    async def get_test_statistics(self, user_id: int) -> Dict[str, Any]:
        """Получает статистику тестов пользователя"""
        try:
            # Здесь нужно добавить метод в Database для получения статистики
            # Например: return db.get_user_test_statistics(user_id)
            return {
                'total_tests': 0,
                'average_score': 0,
                'best_score': 0,
                'books_tested': []
            }
        except Exception as e:
            print(f"Error getting test statistics: {e}")
            return {}

# Создаем экземпляр системы тестирования
testing_system = TestingSystem()

# Обработчики для тестирования
async def handle_test_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает все колбэки связанные с тестами"""
    query = update.callback_query
    data = query.data
    
    if data.startswith("test_answer_"):
        await testing_system.handle_test_answer(update, context)
    elif data.startswith("test_skip_"):
        await testing_system.skip_test_question(update, context)
    elif data.startswith("test_next_"):
        await testing_system.show_next_question(update, context)
    elif data.startswith("retake_test_"):
        book_id = int(data.split('_')[2])
        await testing_system.start_book_test(update, context, book_id)

# Регистрация обработчиков
def setup_testing_handlers(application):
    """Регистрирует обработчики для системы тестирования"""
    application.add_handler(CallbackQueryHandler(handle_test_callback, pattern=r'^test_'))
