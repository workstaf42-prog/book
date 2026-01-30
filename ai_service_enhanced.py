import os
import openai
from typing import Optional

class EnhancedAIService:
    def __init__(self):
        self.client = None
        api_key = os.getenv("OPENAI_API_KEY")
        
        if api_key:
            try:
                self.client = openai.OpenAI(api_key=api_key)
                print("✓ AI service initialized successfully")
            except Exception as e:
                print(f"⚠️ Failed to initialize AI service: {e}")
                self.client = None
        else:
            print("⚠️ OpenAI API key not found. AI features disabled.")
            self.client = None
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def generate_response(self, prompt: str) -> Optional[str]:
        """Генерация ответа через AI"""
        if not self.is_available():
            return "AI сервис временно недоступен. Пожалуйста, попробуйте позже."
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return None