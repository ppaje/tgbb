import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from python_console import PythonConsole
from security import SecurityManager

logging.basicConfig(level=logging.INFO)

class PythonLearningBot:
    def __init__(self):
        self.token = os.getenv('BOT_TOKEN')
        self.webhook_url = os.getenv('WEBHOOK_URL', '')
        self.port = int(os.getenv('PORT', 10000))
        
        if not self.token:
            raise ValueError("BOT_TOKEN не установлен!")
            
        self.application = Application.builder().token(self.token).build()
        self.consoles = {}
        self.security = SecurityManager()
        self.user_stats = {}  # Статистика пользователей
        
        self.setup_handlers()
        
    def setup_handlers(self):
        """Настройка обработчиков"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("console", self.open_console))
        self.application.add_handler(CommandHandler("lessons", self.show_lessons))
        self.application.add_handler(CommandHandler("security", self.security_info))
        self.application.add_handler(CommandHandler("reset", self.reset_console))
        self.application.add_handler(CommandHandler("stats", self.show_stats))
        self.application.add_handler(CommandHandler("help", self.show_help))
        self.application.add_handler(CommandHandler("quiz", self.show_quiz))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_error_handler(self.error_handler)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        user_id = user.id
        
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                "codes_executed": 0,
                "errors": 0,
                "lessons_learned": 0
            }
        
        welcome_text = f"""
🤖 *Привет, {user.first_name}!*

Добро пожаловать в *Python Learning Bot* – интерактивный бот для обучения Python!

📚 *Возможности:*
💻 `/console` – Интерактивная Python консоль
📖 `/lessons` – Уроки по Python
🛡️ `/security` – Информация о безопасности
📊 `/stats` – Ваша статистика
❓ `/help` – Справка
🎯 `/quiz` – Тест по Python

🚀 *Начните вводить Python код, и я его выполню!*

Пример:
```
print("Hello, Python!")
x = 5 * 10
x
```
        """
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать справку"""
        help_text = """
📚 *Справка по Python Learning Bot*

*Команды:*
• `/start` – Главное меню
• `/console` – Открыть консоль
• `/lessons` – Уроки (5 уровней)
• `/quiz` – Тест по Python
• `/stats` – Ваша статистика
• `/reset` – Сбросить консоль
• `/security` – О безопасности

*Возможности консоли:*
✅ Выполнение Python кода
✅ Сохранение переменных между запусками
✅ Доступные модули: math, json, datetime, random
✅ Ограничения: 1000 символов, 5 секунд на выполнение

*Примеры:*
```python
# Переменные
name = "Python"
age = 30

# Цикл
for i in range(5):
    print(i)

# Функция
def hello(x):
    return x * 2

# Математика
import math
math.sqrt(16)
```
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def open_console(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Открыть интерактивную консоль"""
        user_id = update.effective_user.id
        self.consoles[user_id] = PythonConsole()
        
        msg = """
💻 *Интерактивная Python консоль открыта!*

*Возможности:*
• Выполнение Python кода
• Сохранение переменных между запусками
• Ограничения безопасности для защиты сервера

*Доступные модули:*
✅ `math` – математические функции
✅ `json` – работа с JSON
✅ `datetime` – работа со временем
✅ `random` – случайные числа

*Пример:*
```python
>>> print("Hello, Python!")
>>> x = 5 * 10
>>> x
50
>>> import math
>>> math.sqrt(16)
4.0
```

Используйте `/reset` для очистки консоли
        """
        await update.message.reply_text(msg, parse_mode='Markdown')

    async def show_lessons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать доступные уроки"""
        keyboard = [
            [InlineKeyboardButton("1️⃣ Переменные и типы данных", callback_data="lesson_1")],
            [InlineKeyboardButton("2️⃣ Условные операторы", callback_data="lesson_2")],
            [InlineKeyboardButton("3️⃣ Циклы", callback_data="lesson_3")],
            [InlineKeyboardButton("4️⃣ Функции", callback_data="lesson_4")],
            [InlineKeyboardButton("5️⃣ Списки и словари", callback_data="lesson_5")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📚 *Выберите урок для изучения:*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def show_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать викторину"""
        keyboard = [
            [InlineKeyboardButton("❓ Вопрос 1: Типы данных", callback_data="quiz_1")],
            [InlineKeyboardButton("❓ Вопрос 2: Цикл for", callback_data="quiz_2")],
            [InlineKeyboardButton("❓ Вопрос 3: Функции", callback_data="quiz_3")],
            [InlineKeyboardButton("❓ Вопрос 4: Списки", callback_data="quiz_4")],
            [InlineKeyboardButton("❓ Вопрос 5: Словари", callback_data="quiz_5")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🎯 *Викторина по Python:*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def security_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать информацию о безопасности"""
        info = """
🛡️ *Информация о безопасности бота*

*Ограничения для защиты:*
• Максимальная длина кода: 1000 символов
• Время выполнения: 5 секунд
• Память: 50 МБ

*Запрещено:*
❌ `import os`, `sys`, `subprocess`
❌ `__import__()`, `eval()`, `exec()`
❌ `open()`, `read()`, `write()` файлы
❌ `socket`, `urllib`, `requests`
❌ Доступ к приватным атрибутам (`__*__`)

*Разрешено:*
✅ `math` – математика
✅ `json` – JSON данные
✅ `datetime` – время
✅ `random` – случайные числа
✅ Встроенные функции (print, len, range и т.д.)
✅ Работа с переменными, функциями, циклами
✅ Списки, словари, кортежи, множества

*Как работает безопасность:*
1. Сканирование кода на опасные функции
2. Проверка синтаксиса
3. Контроль использования памяти
4. Таймаут выполнения
5. Фильтрация вывода ошибок

        """
        await update.message.reply_text(info, parse_mode='Markdown')

    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статистику пользователя"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                "codes_executed": 0,
                "errors": 0,
                "lessons_learned": 0
            }
        
        stats = self.user_stats[user_id]
        
        stats_text = f"""
📊 *Ваша статистика:*

✅ Код выполнен: `{stats['codes_executed']}`
❌ Ошибок: `{stats['errors']}`
📚 Уроков изучено: `{stats['lessons_learned']}`

Продолжайте практику! 🚀
        """
        await update.message.reply_text(stats_text, parse_mode='Markdown')

    async def reset_console(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Сбросить консоль пользователя"""
        user_id = update.effective_user.id
        if user_id in self.consoles:
            result = self.consoles[user_id].reset_console()
            await update.message.reply_text(result)
        else:
            await update.message.reply_text("Консоль еще не открыта. Используйте `/console`", parse_mode='Markdown')

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик кнопок"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        callback_data = query.data
        
        # Обновление статистики
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                "codes_executed": 0,
                "errors": 0,
                "lessons_learned": 0
            }
        
        lessons_content = {
            "lesson_1": """
*📖 Урок 1: Переменные и типы данных*

Переменная – это имя, которое хранит значение.

```python
# Строка (str)
name = 'Python'
greeting = "Hello, World!"

# Целое число (int)
age = 30
count = 100

# Число с плавающей точкой (float)
height = 5.9
price = 19.99

# Булево значение (bool)
is_active = True
is_closed = False

# Проверка типа
print(type(name))      # <class 'str'>
print(type(age))       # <class 'int'>
print(type(height))    # <class 'float'>
print(type(is_active)) # <class 'bool'>
```

*Задание:* Создайте переменные для вашего профиля!
            """,
            "lesson_2": """
*📖 Урок 2: Условные операторы*

Условные операторы позволяют выполнять различный код в зависимости от условия.

```python
age = 18

# if-else
if age >= 18:
    print('Вы взрослый')
else:
    print('Вы несовершеннолетний')

# if-elif-else
if age < 13:
    print('Вы ребенок')
elif age < 18:
    print('Вы подросток')
else:
    print('Вы взрослый')

# Логические операторы
if age > 18 and age < 65:
    print('Работающий возраст')
```

*Задание:* Напишите условие для проверки четности числа!
            """,
            "lesson_3": """
*📖 Урок 3: Циклы*

Циклы повторяют код несколько раз.

```python
# Цикл for
for i in range(5):
    print(i)  # 0, 1, 2, 3, 4

# Цикл while
count = 0
while count < 3:
    print(count)
    count += 1

# Перебор списка
fruits = ['яблоко', 'банан', 'апельсин']
for fruit in fruits:
    print(fruit)

# range с параметрами
for i in range(1, 10, 2):  # от 1 до 10, шаг 2
    print(i)  # 1, 3, 5, 7, 9
```

*Задание:* Выведите таблицу умножения на 5!
            """,
            "lesson_4": """
*📖 Урок 4: Функции*

Функции – это блоки кода, которые можно переиспользовать.

```python
# Простая функция
def greet():
    return 'Привет!'

print(greet())

# Функция с параметрами
def add(a, b):
    return a + b

result = add(5, 3)
print(result)  # 8

# Функция с несколькими параметрами
def calculate(x, y, operation):
    if operation == '+':
        return x + y
    elif operation == '-':
        return x - y
    elif operation == '*':
        return x * y

print(calculate(10, 5, '*'))  # 50
```

*Задание:* Напишите функцию для вычисления площади прямоугольника!
            """,
            "lesson_5": """
*📖 Урок 5: Списки и словари*

Списки и словари – это коллекции данных.

```python
# Список
fruits = ['яблоко', 'банан', 'апельсин']
numbers = [1, 2, 3, 4, 5]

# Доступ к элементам
print(fruits[0])    # яблоко
print(fruits[-1])   # апельсин

# Методы списков
fruits.append('груша')
fruits.remove('банан')
print(len(fruits))  # 3

# Словарь
person = {
    'имя': 'Иван',
    'возраст': 25,
    'город': 'Москва'
}

# Доступ к словарю
print(person['имя'])      # Иван
print(person.get('возраст'))  # 25

# Добавление элемента
person['профессия'] = 'Программист'
```

*Задание:* Создайте словарь своего контакта!
            """,
        }
        
        quiz_questions = {
            "quiz_1": """
❓ *Вопрос 1: Какой это тип данных?*

```python
x = 3.14
```

A️⃣ int (целое число)
B️⃣ float (число с плавающей точкой)
C️⃣ str (строка)
D️⃣ bool (булево значение)

*Ответ:* B️⃣ float
            """,
            "quiz_2": """
❓ *Вопрос 2: Сколько раз выполнится цикл?*

```python
for i in range(3):
    print(i)
```

A️⃣ 2 раза
B️⃣ 3 раза
C️⃣ 4 раза
D️⃣ Бесконечный цикл

*Ответ:* B️⃣ 3 раза (0, 1, 2)
            """,
            "quiz_3": """
❓ *Вопрос 3: Что вернет функция?*

```python
def test(x):
    return x * 2

result = test(5)
```

A️⃣ 5
B️⃣ 10
C️⃣ "55"
D️⃣ None

*Ответ:* B️⃣ 10
            """,
            "quiz_4": """
❓ *Вопрос 4: Что выведет код?*

```python
lst = [1, 2, 3, 4, 5]
print(lst[2])
```

A️⃣ 1
B️⃣ 2
C️⃣ 3
D️⃣ 4

*Ответ:* C️⃣ 3 (индексация начинается с 0)
            """,
            "quiz_5": """
❓ *Вопрос 5: Как получить значение из словаря?*

```python
person = {'имя': 'Иван', 'возраст': 25}
x = person['имя']
```

A️⃣ None
B️⃣ 25
C️⃣ 'Иван'
D️⃣ Ошибка

*Ответ:* C️⃣ 'Иван'
            """,
        }
        
        if callback_data.startswith("lesson_"):
            content = lessons_content.get(callback_data, "Урок не найден")
            self.user_stats[user_id]["lessons_learned"] += 1
        elif callback_data.startswith("quiz_"):
            content = quiz_questions.get(callback_data, "Вопрос не найден")
        else:
            content = "Опция не найдена"
        
        await query.edit_message_text(content, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода кода"""
        user_id = update.effective_user.id
        code = update.message.text

        # Проверка безопасности
        quick_check = self.security.sanitize_input(code)
        if not quick_check["is_safe"]:
            error_msg = "❌ *Обнаружены проблемы с безопасностью:*\n" + "\n".join(quick_check["issues"][:3])
            await update.message.reply_text(error_msg, parse_mode='Markdown')
            if user_id in self.user_stats:
                self.user_stats[user_id]["errors"] += 1
            return

        if user_id not in self.consoles:
            self.consoles[user_id] = PythonConsole()

        try:
            result = self.consoles[user_id].execute(code)
            
            if result.startswith(('❌', '⏰', '💥')):
                response = result
                if user_id in self.user_stats:
                    self.user_stats[user_id]["errors"] += 1
            else:
                response = f"```python\n>>> {code}\n{result}\n```"
                if user_id in self.user_stats:
                    self.user_stats[user_id]["codes_executed"] += 1
            
            await update.message.reply_text(response, parse_mode='MarkdownV2')
            
        except Exception as e:
            error_msg = f"❌ Системная ошибка:\n```\n{str(e)}\n```"
            await update.message.reply_text(error_msg, parse_mode='MarkdownV2')
            if user_id in self.user_stats:
                self.user_stats[user_id]["errors"] += 1

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик ошибок"""
        logging.error(msg="Exception while handling an update:", exc_info=context.error)

    def run(self):
        """Запуск бота"""
        if self.webhook_url:
            self.run_webhook()
        else:
            self.run_polling()

    def run_webhook(self):
        """Запуск в режиме webhook"""
        self.application.run_webhook(
            listen="0.0.0.0",
            port=self.port,
            url_path=self.token,
            webhook_url=f"{self.webhook_url}/{self.token}"
        )

    def run_polling(self):
        """Запуск в режиме polling (для разработки)"""
        self.application.run_polling()
