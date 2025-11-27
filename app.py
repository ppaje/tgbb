from bot import PythonLearningBot
import logging
import os

# Настройка логирования для Render
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Запуск бота"""
    bot = PythonLearningBot()
    
    # Проверяем наличие токена
    if not bot.application.bot.token:
        logging.error("BOT_TOKEN не установлен!")
        return
    
    logging.info("Бот запускается...")
    bot.run()

if __name__ == "__main__":
    main()
