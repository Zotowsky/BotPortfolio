import sqlite3
from config import DATABASE, TOKEN
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

class DB_Manager:
    def __init__(self, database=DATABASE):
        self.database = database
        self.conn = None
        
    def connect(self):
        """Устанавливает соединение с базой данных"""
        try:
            self.conn = sqlite3.connect(self.database)
            return self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Ошибка подключения к базе данных: {e}")
            return None
    
    def close(self):
        """Закрывает соединение с базой данных"""
        if self.conn:
            self.conn.close()
            self.conn = None
            
    def create_tables(self):
        """Создает все необходимые таблицы в базе данных"""
        cursor = self.connect()
        if not cursor:
            print("Не удалось получить курсор для работы с БД")
            return False
        
        try:
            # Создание таблицы status
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS status (
                status_id INTEGER PRIMARY KEY AUTOINCREMENT,
                status_name TEXT NOT NULL UNIQUE
            )''')
            
            # Создание таблицы skills
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT NOT NULL UNIQUE
            )''')
            
            # Создание таблицы projects
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                project_name TEXT NOT NULL,
                description TEXT,
                url TEXT,
                status_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (status_id) REFERENCES status(status_id)
            )''')
            
            # Создание таблицы project_skills
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                skill_id INTEGER NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(project_id),
                FOREIGN KEY (skill_id) REFERENCES skills(skill_id),
                UNIQUE (project_id, skill_id)
            )''')
            
            # Создание триггера
            cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_project_timestamp
            AFTER UPDATE ON projects
            FOR EACH ROW
            BEGIN
                UPDATE projects SET updated_at = CURRENT_TIMESTAMP 
                WHERE project_id = OLD.project_id;
            END''')
            
            # Добавляем базовые статусы
            self._add_default_statuses(cursor)
            
            if self.conn:
                self.conn.commit()
                print("Таблицы успешно созданы!")
                return True
            return False
            
        except sqlite3.Error as e:
            print(f"Ошибка при создании таблиц: {e}")
            if self.conn:
                self.conn.rollback()
            return False
        finally:
            self.close()
    
    def _add_default_statuses(self, cursor):
        """Добавляет стандартные статусы"""
        default_statuses = ["В планах", "В процессе", "Завершен"]
        for status in default_statuses:
            try:
                cursor.execute("INSERT OR IGNORE INTO status (status_name) VALUES (?)", (status,))
            except sqlite3.Error as e:
                print(f"Ошибка при добавлении статуса {status}: {e}")

    # Методы для работы со статусами
    def add_status(self, status_name):
        cursor = self.connect()
        try:
            cursor.execute("INSERT OR IGNORE INTO status (status_name) VALUES (?)", (status_name,))
            self.conn.commit()
        finally:
            self.close()
    
    def get_statuses(self):
        cursor = self.connect()
        try:
            cursor.execute("SELECT * FROM status")
            return cursor.fetchall()
        finally:
            self.close()

    # Методы для работы с навыками
    def add_skill(self, skill_name):
        cursor = self.connect()
        try:
            cursor.execute("INSERT OR IGNORE INTO skills (skill_name) VALUES (?)", (skill_name,))
            self.conn.commit()
        finally:
            self.close()
    
    def get_skills(self):
        cursor = self.connect()
        try:
            cursor.execute("SELECT * FROM skills")
            return cursor.fetchall()
        finally:
            self.close()

    # Методы для работы с проектами
    def add_project(self, user_id, project_name, description, url, status_id, skills):
        cursor = self.connect()
        try:
            cursor.execute(
                "INSERT INTO projects (user_id, project_name, description, url, status_id) VALUES (?, ?, ?, ?, ?)",
                (user_id, project_name, description, url, status_id)
            )
            project_id = cursor.lastrowid
            
            for skill in skills:
                cursor.execute(
                    "INSERT OR IGNORE INTO skills (skill_name) VALUES (?)",
                    (skill,)
                )
                cursor.execute(
                    "SELECT skill_id FROM skills WHERE skill_name = ?",
                    (skill,)
                )
                skill_id = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO project_skills (project_id, skill_id) VALUES (?, ?)",
                    (project_id, skill_id)
                )
            
            self.conn.commit()
            return project_id
        except sqlite3.Error as e:
            print(f"Ошибка при добавлении проекта: {e}")
            return None
        finally:
            self.close()
    
    def get_projects(self, user_id):
        cursor = self.connect()
        try:
            cursor.execute("""
                SELECT p.project_id, p.project_name, p.description, p.url, s.status_name, p.created_at, p.updated_at
                FROM projects p
                JOIN status s ON p.status_id = s.status_id
                WHERE p.user_id = ?
                ORDER BY p.updated_at DESC
            """, (user_id,))
            projects = cursor.fetchall()
            
            result = []
            for project in projects:
                cursor.execute("""
                    SELECT sk.skill_name 
                    FROM project_skills ps
                    JOIN skills sk ON ps.skill_id = sk.skill_id
                    WHERE ps.project_id = ?
                """, (project[0],))
                skills = [row[0] for row in cursor.fetchall()]
                result.append({
                    'id': project[0],
                    'name': project[1],
                    'description': project[2],
                    'url': project[3],
                    'status': project[4],
                    'created_at': project[5],
                    'updated_at': project[6],
                    'skills': skills
                })
            return result
        finally:
            self.close()
    
    def delete_project(self, project_id):
        cursor = self.connect()
        try:
            cursor.execute("DELETE FROM project_skills WHERE project_id = ?", (project_id,))
            cursor.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        finally:
            self.close()

class PortfolioBot:
    def __init__(self):
        self.db = DB_Manager()
        self.db.create_tables()
        self.user_states = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        user = update.effective_user
        await update.message.reply_text(
            f"Привет, {user.first_name}!\n"
            "Я бот для управления твоим портфолио.\n"
            "Используй команды:\n"
            "/add_project - добавить проект\n"
            "/my_projects - просмотреть проекты\n"
            "/delete_project - удалить проект"
        )

    async def add_project_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /add_project"""
        chat_id = update.effective_chat.id
        self.user_states[chat_id] = {'state': 'awaiting_project_name'}
        await update.message.reply_text("Введите название проекта:")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик текстовых сообщений"""
        chat_id = update.effective_chat.id
        user_state = self.user_states.get(chat_id, {})

        if user_state.get('state') == 'awaiting_project_name':
            self.user_states[chat_id] = {
                'state': 'awaiting_description',
                'project_name': update.message.text
            }
            await update.message.reply_text("Введите описание проекта:")

        elif user_state.get('state') == 'awaiting_description':
            self.user_states[chat_id] = {
                'state': 'awaiting_url',
                'project_name': user_state['project_name'],
                'description': update.message.text
            }
            await update.message.reply_text("Введите URL проекта (или 'нет', если нет ссылки):")

        elif user_state.get('state') == 'awaiting_url':
            url = update.message.text if update.message.text.lower() != 'нет' else None
            self.user_states[chat_id] = {
                'state': 'awaiting_status',
                'project_name': user_state['project_name'],
                'description': user_state['description'],
                'url': url
            }
            await self.show_status_keyboard(update)

        elif user_state.get('state') == 'awaiting_skills':
            skills = [s.strip() for s in update.message.text.split(',')]
            project_data = self.user_states[chat_id]
            
            status_id = next(
                status[0] for status in self.db.get_statuses() 
                if status[1] == project_data['status']
            )
            
            project_id = self.db.add_project(
                user_id=chat_id,
                project_name=project_data['project_name'],
                description=project_data['description'],
                url=project_data['url'],
                status_id=status_id,
                skills=skills
            )
            
            if project_id:
                await update.message.reply_text(f"Проект успешно добавлен (ID: {project_id})!")
            else:
                await update.message.reply_text("Ошибка при добавлении проекта.")
            
            del self.user_states[chat_id]

    async def show_status_keyboard(self, update: Update):
        """Показывает клавиатуру с выбором статуса"""
        statuses = self.db.get_statuses()
        keyboard = [
            [InlineKeyboardButton(status[1], callback_data=f"status_{status[0]}")]
            for status in statuses
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите статус проекта:", reply_markup=reply_markup)

    async def status_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик выбора статуса"""
        query = update.callback_query
        await query.answer()
        
        status_id = int(query.data.split('_')[1])
        status_name = next(
            status[1] for status in self.db.get_statuses()
            if status[0] == status_id
        )
        
        chat_id = query.message.chat_id
        self.user_states[chat_id]['status'] = status_name
        self.user_states[chat_id]['state'] = 'awaiting_skills'
        
        await query.edit_message_text(f"Статус выбран: {status_name}\nТеперь введите навыки через запятую:")

    async def my_projects_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /my_projects"""
        projects = self.db.get_projects(update.effective_chat.id)
        
        if not projects:
            await update.message.reply_text("У вас пока нет проектов.")
            return
        
        for project in projects:
            message = (
                f"📌 <b>{project['name']}</b>\n"
                f"📝 {project['description']}\n"
                f"🔗 {project['url'] or 'Нет ссылки'}\n"
                f"🔄 Статус: {project['status']}\n"
                f"🛠 Навыки: {', '.join(project['skills']) if project['skills'] else 'Не указаны'}\n"
                f"📅 Создан: {project['created_at']}\n"
                f"🔄 Обновлен: {project['updated_at']}\n"
                f"ID: {project['id']}"
            )
            await update.message.reply_text(message, parse_mode='HTML')

    async def delete_project_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /delete_project"""
        projects = self.db.get_projects(update.effective_chat.id)
        
        if not projects:
            await update.message.reply_text("У вас пока нет проектов для удаления.")
            return
        
        keyboard = [
            [InlineKeyboardButton(f"{p['name']} (ID: {p['id']})", callback_data=f"delete_{p['id']}")]
            for p in projects
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите проект для удаления:", reply_markup=reply_markup)

    async def delete_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик подтверждения удаления"""
        query = update.callback_query
        await query.answer()
        
        project_id = int(query.data.split('_')[1])
        success = self.db.delete_project(project_id)
        
        if success:
            await query.edit_message_text(f"Проект ID {project_id} успешно удален!")
        else:
            await query.edit_message_text("Ошибка при удалении проекта.")

    def run(self):
        """Запускает бота"""
        application = Application.builder().token(TOKEN).build()

        # Регистрация обработчиков
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("add_project", self.add_project_command))
        application.add_handler(CommandHandler("my_projects", self.my_projects_command))
        application.add_handler(CommandHandler("delete_project", self.delete_project_command))
        
        application.add_handler(CallbackQueryHandler(self.status_callback, pattern='^status_'))
        application.add_handler(CallbackQueryHandler(self.delete_callback, pattern='^delete_'))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        application.run_polling()

if __name__ == "__main__":
    bot = PortfolioBot()
    bot.run()