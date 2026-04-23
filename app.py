from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super_secret_key'
ADMIN_PASSWORD = "777"

def init_db():
    conn = sqlite3.connect('clients.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS bookings (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, service TEXT, time TEXT)')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_booking', methods=['POST'])
def add_booking():
    name = request.form.get('name')
    service = request.form.get('service')
    time_str = request.form.get('time') # Формат: 2026-04-23T15:30
    
    # 1. Проверка рабочего времени (до 18:00)
    dt = datetime.strptime(time_str, '%Y-%m-%dT%H:%M')
    if dt.hour >= 18:
        return "<h2>Ошибка: Мы работаем только до 18:00!</h2><a href='/'>Назад</a>"

    # 2. Проверка, не занято ли это время
    conn = sqlite3.connect('clients.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM bookings WHERE time = ?", (time_str,))
    if cursor.fetchone():
        conn.close()
        return "<h2>Ошибка: Это время уже занято! Выберите другое.</h2><a href='/'>Назад</a>"

    # 3. Сохранение, если всё ок
    cursor.execute("INSERT INTO bookings (name, service, time) VALUES (?, ?, ?)", (name, service, time_str))
    conn.commit()
    conn.close()
    return "<h2>Вы успешно записаны!</h2><a href='/'>Назад</a>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
    return render_template('login.html')

@app.route('/admin')
def admin():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = sqlite3.connect('clients.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings ORDER BY time ASC")
    rows = cursor.fetchall()
    conn.close()
    return render_template('admin.html', bookings=rows)

@app.route('/delete/<int:id>')
def delete(id):
    if session.get('logged_in'):
        conn = sqlite3.connect('clients.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bookings WHERE id=?", (id,))
        conn.commit()
        conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)