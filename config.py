import os

# Токен бота из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Настройки безопасности
MAX_CODE_LENGTH = 1000
MAX_OUTPUT_LENGTH = 2000
MAX_EXECUTION_TIME = 5

# Настройки Webhook для Render
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
PORT = int(os.getenv('PORT', 10000))
