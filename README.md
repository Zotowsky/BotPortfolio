📂 Portfolio Manager Bot
Telegram-бот для управления персональным портфолио проектов

https://img.shields.io/badge/Python-3.8+-blue?logo=python
https://img.shields.io/badge/Telegram%2520Bot%2520API-20.x+-brightgreen?logo=telegram
https://img.shields.io/badge/Database-SQLite-lightgrey?logo=sqlite

📌 Описание
Бот помогает систематизировать ваши проекты:

📁 Хранит информацию о проектах (название, описание, ссылки)

🛠 Учитывает используемые технологии/навыки

🔄 Отслеживает статус разработки (в планах, в процессе, завершен)

📊 Формирует удобное портфолио для демонстрации

🚀 Возможности
Команда	Описание
/start	Главное меню
/add_project	Добавить новый проект
/my_projects	Показать все проекты
/delete_project	Удалить проект
/edit_project	Изменить данные проекта
Пример работы:

text
/start → /add_project → Вводим:  
Название: "Чат-бот для Warframe"  
Описание: "Бот с гайдами по игре"  
Навыки: Python, Telegram API, SQLite  
Статус: "Завершен"  
⚙️ Установка
1. Клонируйте репозиторий
bash
git clone https://github.com/ваш-username/portfolio-bot.git
cd portfolio-bot
2. Установите зависимости
bash
pip install -r requirements.txt
3. Настройка
Создайте файл config.py:

python
DATABASE = 'portfolio.db'  
TELEGRAM_TOKEN = 'ваш_токен_бота'  
4. Запуск
bash
python logic.py
🛠 Технологии
Backend: Python 3.8+

Библиотеки: python-telegram-bot, sqlite3

База данных: SQLite (файл portfolio.db)

📁 Структура базы данных
sql
CREATE TABLE projects (
    project_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    project_name TEXT,
    description TEXT,
    url TEXT,
    status TEXT,
    created_at TIMESTAMP
);
📜 Лицензия
MIT License. Открытый исходный код.

📮 Контакты
По вопросам и предложениям:
✉️ Email: your.email@example.com
💬 Telegram: @your_username

✨ Готово! Ваше портфолио теперь всегда под рукой в Telegram.

🔄 Пример обновления
bash
# Добавьте новые навыки в проект:
/edit_project → Выбрать проект → Добавить "Docker, FastAPI"
https://railway.app/button.svg

Для развертывания на хостинге используйте кнопку выше.
