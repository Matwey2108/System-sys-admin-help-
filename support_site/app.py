from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import requests
from datetime import datetime

app = Flask(__name__)

# --- НАСТРОЙКИ ЯНДЕКС ДИСКА ---
YANDEX_USER = "matvei.tsypovyaz@yandex.ru"
YANDEX_PASS = "ydmtmgyufklamyzd" # Тот самый 16-значный код
YANDEX_URL = "https://webdav.yandex.ru/"

def send_to_yandex(filename, content):
    """Отправляет текстовый файл на Яндекс Диск через WebDAV"""
    try:
        # Создаем полный путь к файлу на диске
        target_url = f"{YANDEX_URL}{filename}"
        
        # Отправляем PUT запрос (базовая авторизация)
        response = requests.put(
            target_url, 
            data=content.encode('utf-8'), 
            auth=(YANDEX_USER, YANDEX_PASS)
        )
        
        if response.status_code == 201:
            print(f"Файл {filename} успешно сохранен на Яндекс Диске")
        else:
            print(f"Ошибка Яндекса: {response.status_code}")
    except Exception as e:
        print(f"Ошибка при связи с Яндексом: {e}")

# --- ОСТАЛЬНАЯ ЛОГИКА ---

def init_db():
    with sqlite3.connect('support.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT,
                category TEXT,
                description TEXT,
                status TEXT DEFAULT 'В очереди',
                created_at TEXT
            )
        ''')

@app.route('/')
def index():
    with sqlite3.connect('support.db') as conn:
        conn.row_factory = sqlite3.Row
        tickets = conn.execute('SELECT * FROM tickets ORDER BY id DESC').fetchall()
    return render_template('index.html', tickets=tickets)

@app.route('/add', methods=['POST'])
def add_ticket():
    user = request.form.get('user_name')
    category = request.form.get('category')
    desc = request.form.get('description')
    date = datetime.now().strftime("%d.%m.%Y %H:%M")

    if user and desc:
        # 1. Сохраняем в локальную базу
        with sqlite3.connect('support.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO tickets (user_name, category, description, created_at) VALUES (?, ?, ?, ?)',
                         (user, category, desc, date))
            ticket_id = cursor.lastrowid # Получаем ID новой заявки

        # 2. Формируем текст для Яндекс Диска
        file_content = f"""
        ЗАЯВКА №{ticket_id}
        Дата: {date}
        От кого: {user}
        Категория: {category}
        Описание: {desc}
        """
        
        # 3. Отправляем файл (имя файла будет ticket_1.txt и т.д.)
        file_name = f"ticket_{ticket_id}.txt"
        send_to_yandex(file_name, file_content)

    return redirect(url_for('index'))

@app.route('/delete/<int:ticket_id>')
def delete_ticket(ticket_id):
    with sqlite3.connect('support.db') as conn:
        conn.execute('DELETE FROM tickets WHERE id = ?', (ticket_id,))
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)