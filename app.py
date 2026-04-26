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
    
    # Чтобы можно было заказывать побольше услуг (сразу несколько)
    services = request.form.getlist('service')
    service_str = ", ".join(services) if services else "Не выбрано"
    
    time_str = request.form.get('time') # Формат: 2026-04-23T15:30
    
    try:
        dt = datetime.strptime(time_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        return "<h2 style='color:red;'>Ошибка: Неверный формат времени!</h2><a href='/'>Назад</a>"
        
    # Проверка, чтобы дата не была в прошлом
    if dt < datetime.now():
        return "<h2 style='color:red;'>Ошибка: Нельзя забронировать на прошедшее время!</h2><a href='/'>Назад</a>"
    
    # 1. Проверка рабочего времени (работаем до 18:00)
    if dt.hour >= 18 or dt.hour < 9:
        return "<h2 style='color:red;'>Ошибка: Мы работаем с 09:00 до 18:00!</h2><a href='/'>Назад</a>"

    # 2. Проверка, не занято ли это время никем
    conn = sqlite3.connect('clients.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM bookings WHERE time = ?", (time_str,))
    if cursor.fetchone():
        conn.close()
        return "<h2 style='color:red;'>Ошибка: Это время уже занято! Выберите другое удобное время.</h2><a href='/'>Назад</a>"

    # Проверка, чтобы 1 и тот же человек не забронировал дважды в одно и то же время
    cursor.execute("SELECT id FROM bookings WHERE name = ? AND time = ?", (name, time_str))
    if cursor.fetchone():
        conn.close()
        return "<h2 style='color:red;'>Ошибка: Вы уже забронировали это время!</h2><a href='/'>Назад</a>"

    # 3. Сохранение, если всё ок
    cursor.execute("INSERT INTO bookings (name, service, time) VALUES (?, ?, ?)", (name, service_str, time_str))
    conn.commit()
    conn.close()
    return "<div style='text-align:center; padding: 50px; font-family: sans-serif;'><h2 style='color:#ff8fab;'>Вы успешно записаны!</h2><a href='/' style='text-decoration:none; padding:10px 20px; background:#ff8fab; color:white; border-radius:10px;'>На главную</a></div>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password.strip() == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = "Неверный пароль! Попробуйте снова."
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    conn = sqlite3.connect('clients.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings ORDER BY time ASC")
    rows = cursor.fetchall()
    conn.close()
    
    # Форматирование времени, чтобы показывались день недели и год
    formatted_bookings = []
    days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    for row in rows:
        try:
            dt = datetime.strptime(row[3], '%Y-%m-%dT%H:%M')
            # Пример: 24.04.2026, 15:30 (Пятница)
            formatted_time = f"{dt.strftime('%d.%m.%Y, %H:%M')} ({days[dt.weekday()]})"
        except ValueError:
            formatted_time = row[3]
        formatted_bookings.append((row[0], row[1], row[2], formatted_time))
        
    return render_template('admin.html', bookings=formatted_bookings)

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
    app.run(debug=True, port=5000)