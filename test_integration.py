"""
Интеграция системы тестирования в основной бот
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

from database import Database
from database_extended import DatabaseExtended
from testing_system import TestingSystem
class TestIntegration:
    def __init__(self):
        try:
            self.ai_service = EnhancedAIService()
            if not self.ai_service.is_available():
                print("⚠️ AI-сервис недоступен, приложение работает в ограниченном режиме")
        except Exception as e:
            print(f"⚠️ Не удалось инициализировать AI-сервис: {e}")
            self.ai_service = None
    
    # Пример метода, который использует AI-сервис
    def use_ai_feature(self, prompt):
        if self.ai_service and self.ai_service.is_available():
            return self.ai_service.generate_response(prompt)
        else:
            return "AI-функции в данный момент недоступны"
    
    async def start_test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для начала тестирования по текущей книге"""
        user = update.effective_user
        
        # Получаем текущую книгу клуба
        current_book = self.db_ext.get_current_book()
        if not current_book:
            await update.message.reply_text(
                "😕 Сейчас нет активной книги для тестирования.\n"
                "Попробуйте позже или выберите книгу из меню."
            )
            return
        
        # Проверяем, не проходил ли пользователь уже тест
        test_history = self.db_ext.get_test_history(user.id, 1)
        if test_history and test_history[0]['book_id'] == current_book['id']:
            last_test_date = test_history[0]['test_date']
            await update.message.reply_text(
                f"📊 **Вы уже проходили тест по этой книге!**\n\n"
                f"📖 Книга: {current_book['title']}\n"
                f"📅 Дата теста: {last_test_date}\n"
                f"🎯 Результат: {test_history[0]['percentage']:.1f}%\n\n"
                "Хотите пройти тест еще раз?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Пройти еще раз", callback_data=f"retake_test_{current_book['id']}")],
                    [InlineKeyboardButton("📊 Посмотреть статистику", callback_data="test_stats")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
                ]),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Начинаем тест
        await self.testing_system.start_book_test(update, context, current_book['id'])
    
    async def test_menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает меню тестирования"""
        user = update.effective_user
        
        # Получаем статистику пользователя
        stats = self.db_ext.get_user_test_statistics(user.id)
        
        menu_text = (
            "🧠 **ЦЕНТР ТЕСТИРОВАНИЯ**\n\n"
            "📊 **Ваша статистика:**\n"
            f"• Пройдено тестов: {stats['total_tests']}\n"
            f"• Средний балл: {stats['average_score']}%\n"
            f"• Лучший результат: {stats['best_score']}%\n\n"
            "📚 **Доступные тесты:**\n"
            "• Тест по текущей книге клуба\n"
            "• Адаптивные тесты\n"
            "• Тесты по пройденным книгам\n\n"
            "Выберите действие:"
        )
        
        keyboard = []
        
        # Текущая книга
        current_book = self.db_ext.get_current_book()
        if current_book:
            keyboard.append([InlineKeyboardButton(
                f"📖 Тест: {current_book['title']}", 
                callback_data=f"test_book_{current_book['id']}"
            )])
        
        # Адаптивный тест
        if stats['total_tests'] > 0:
            keyboard.append([InlineKeyboardButton(
                "🎯 Адаптивный тест", 
                callback_data="adaptive_test"
            )])
        
        # История тестов
        if stats['total_tests'] > 0:
            keyboard.append([InlineKeyboardButton(
                "📊 История тестов", 
                callback_data="test_history"
            )])
        
        # Общие кнопки
        keyboard.extend([
            [InlineKeyboardButton("📈 Анализ слабых мест", callback_data="weak_areas_analysis")],
            [InlineKeyboardButton("🎓 Рекомендации по обучению", callback_data="learning_recommendations")],
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def adaptive_test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запускает адаптивный тест"""
        user = update.effective_user
        
        # Получаем статистику и слабые места
        stats = self.db_ext.get_user_test_statistics(user.id)
        weak_areas = self.db_ext.get_user_weak_areas(user.id)
        
        if stats['total_tests'] == 0:
            await update.message.reply_text(
                "😕 Для адаптивного теста нужно сначала пройти обычный тест.\n"
                "Начните с теста по текущей книге клуба."
            )
            return
        
        # Получаем текущую книгу
        current_book = self.db_ext.get_current_book()
        if not current_book:
            await update.message.reply_text(
                "😕 Нет активной книги для адаптивного тестирования."
            )
            return
        
        # Формируем информацию о производительности
        user_performance = {
            'average_score': stats['average_score'],
            'weak_categories': weak_areas,
            'total_tests': stats['total_tests']
        }
        
        # Генерируем адаптивные вопросы
        questions = await self.ai_service.generate_adaptive_questions(
            current_book['title'], 
            current_book['author'], 
            user_performance
        )
        
        if not questions:
            await update.message.reply_text(
                "😕 Не удалось сгенерировать адаптивные вопросы. Попробуйте позже."
            )
            return
        
        # Создаем адаптивный тест
        await self.testing_system.start_adaptive_test(update, context, current_book, questions, user_performance)
    
    async def test_history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает историю тестов"""
        user = update.effective_user
        test_history = self.db_ext.get_test_history(user.id, 10)
        
        if not test_history:
            await update.message.reply_text(
                "📊 **ИСТОРИЯ ТЕСТОВ**\n\n"
                "У вас пока нет пройденных тестов.\n\n"
                "Начните с теста по текущей книге клуба!"
            )
            return
        
        history_text = "📊 **ИСТОРИЯ ТЕСТОВ**\n\n"
        
        for i, test in enumerate(test_history, 1):
            # Определяем уровень
            percentage = test['percentage']
            if percentage >= 90:
                level = "🏆 Отлично"
            elif percentage >= 70:
                level = "🥈 Хорошо"
            elif percentage >= 50:
                level = "🥉 Удовлетворительно"
            else:
                level = "📚 Нужно улучшить"
            
            history_text += (
                f"{i}. **{test['title']}**\n"
                f"   📅 {test['test_date'][:10]}\n"
                f"   🎯 {test['percentage']:.1f}% - {level}\n\n"
            )
        
        history_text += "💡 Нажмите на тест для подробного анализа"
        
        keyboard = []
        for test in test_history:
            keyboard.append([InlineKeyboardButton(
                f"📊 {test['title']} ({test['percentage']:.0f}%)",
                callback_data=f"test_detail_{test['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(history_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def weak_areas_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Анализ слабых мест пользователя"""
        user = update.effective_user
        
        # Получаем производительность по категориям
        performance = self.db_ext.get_category_performance(user.id)
        weak_areas = self.db_ext.get_user_weak_areas(user.id)
        
        if not performance:
            await update.message.reply_text(
                "📈 **АНАЛИЗ СЛАБЫХ МЕСТ**\n\n"
                "Недостаточно данных для анализа.\n"
                "Пройдите несколько тестов для получения рекомендаций."
            )
            return
        
        analysis_text = "📈 **АНАЛИЗ СЛАБЫХ МЕСТ**\n\n"
        
        # Сильные стороны
        strong_areas = [cat for cat, stats in performance.items() if stats['percentage'] >= 80]
        if strong_areas:
            analysis_text += "💪 **Ваши сильные стороны:**\n"
            for area in strong_areas:
                analysis_text += f"• {area}: {performance[area]['percentage']}%\n"
            analysis_text += "\n"
        
        # Слабые места
        if weak_areas:
            analysis_text += "🎯 **Требуют внимания:**\n"
            for area in weak_areas:
                analysis_text += f"• {area}: {performance[area]['percentage']}%\n"
            analysis_text += "\n"
        
        # Рекомендации
        analysis_text += "💡 **Рекомендации:**\n"
        
        if 'plot' in weak_areas:
            analysis_text += "• Перечитывайте ключевые сцены внимательно\n"
        if 'character' in weak_areas:
            analysis_text += "• Анализируйте мотивацию персонажей\n"
        if 'theme' in weak_areas:
            analysis_text += "• Ищите скрытые смыслы и символы\n"
        if 'quote' in weak_areas:
            analysis_text += "• Запоминайте цитаты и их авторов\n"
        
        keyboard = [
            [InlineKeyboardButton("🎯 Адаптивный тест", callback_data="adaptive_test")],
            [InlineKeyboardButton("📚 Учебные материалы", callback_data="learning_materials")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(analysis_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_test_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает колбэки тестирования"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith("test_book_"):
            book_id = int(data.split("_")[2])
            await self.testing_system.start_book_test(update, context, book_id)
        elif data == "adaptive_test":
            await self.adaptive_test_command(update, context)
        elif data == "test_history":
            await self.test_history_command(update, context)
        elif data == "weak_areas_analysis":
            await self.weak_areas_analysis(update, context)
        elif data.startswith("test_detail_"):
            test_id = int(data.split("_")[2])
            await self.show_test_detail(update, context, test_id)
        elif data.startswith("retake_test_"):
            book_id = int(data.split("_")[2])
            await self.testing_system.start_book_test(update, context, book_id)
    
    async def show_test_detail(self, update: Update, context: ContextTypes.DEFAULT_TYPE, test_id: int):
        """Показывает детальную информацию о тесте"""
        # Здесь можно добавить детальный анализ конкретного теста
        await query.edit_message_text(
            "📊 **ДЕТАЛЬНЫЙ АНАЛИЗ ТЕСТА**\n\n"
            "Функция в разработке...",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
            ]])
        )

# Создаем экземпляр интеграции
test_integration = TestIntegration()

# Регистрация обработчиков
def setup_test_integration(application):
    """Регистрирует обработчики для интеграции тестирования"""
    application.add_handler(CommandHandler("test", test_integration.test_menu_command))
    application.add_handler(CommandHandler("start_test", test_integration.start_test_command))
    application.add_handler(CommandHandler("adaptive_test", test_integration.adaptive_test_command))
    application.add_handler(CommandHandler("test_history", test_integration.test_history_command))
    
    # Колбэки
    application.add_handler(CallbackQueryHandler(
        test_integration.handle_test_callback, 
        pattern=r'^(test_book_|adaptive_test|test_history|weak_areas_analysis|test_detail_|retake_test_)'
    ))
