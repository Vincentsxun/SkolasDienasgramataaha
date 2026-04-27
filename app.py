from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import uuid

app = Flask(__name__)
app.secret_key = "secret123"

DATA_FILE = "users.json"
SCHEDULE_FILE = "schedule.json"
DAY_ORDER = ["Pirmdiena", "Otrdiena", "Tresdiena", "Ceturtdiena", "Piektdiena"]


def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            loaded_schedule = json.load(f)
            for item in loaded_schedule:
                item.setdefault("id", str(uuid.uuid4())[:8])
                item.setdefault("completed_by", [])
            return loaded_schedule
    return []


def save_schedule(data):
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def validate_password(password):
    if len(password) < 6:
        return "Parolei jābūt vismaz 6 simbolus garai."
    if not any(char.isdigit() for char in password):
        return "Parolē jābūt vismaz vienam ciparam."
    return None


def is_password_valid(stored_password, entered_password):
    if stored_password.startswith("pbkdf2:") or stored_password.startswith("scrypt:"):
        return check_password_hash(stored_password, entered_password)
    return stored_password == entered_password


users = load_users()
schedule = load_schedule()


@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))

    grade_schedule = [item for item in schedule if item['grade'] == session['user']['grade']]
    grade_schedule.sort(key=lambda item: DAY_ORDER.index(item['day']))

    return render_template(
        'dashboard.html',
        user=session['user'],
        schedule=grade_schedule,
        day_order=DAY_ORDER,
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    global users
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        role = request.form['role']
        grade = request.form['grade']

        if username in users:
            flash("Lietotājs jau eksistē.")
            return redirect(url_for('register'))

        password_error = validate_password(password)
        if password_error:
            flash(password_error)
            return redirect(url_for('register'))

        users[username] = {
            'password': generate_password_hash(password),
            'role': role,
            'grade': grade
        }

        save_users(users)
        flash("Konts veiksmīgi izveidots. Tagad pieslēdzies.")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        user = users.get(username)

        if user and is_password_valid(user['password'], password):
            session['user'] = {
                'username': username,
                'role': user['role'],
                'grade': user['grade']
            }
            flash("Esi veiksmīgi pieslēdzies!")
            return redirect(url_for('home'))

        flash("Nepareizs lietotājvārds vai parole.")
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Tu veiksmīgi izrakstījies.")
    return redirect(url_for('login'))


@app.route('/add_homework', methods=['POST'])
def add_homework():
    if 'user' not in session or session['user']['role'] != 'teacher':
        return redirect(url_for('login'))

    subject = request.form['subject'].strip()
    homework = request.form['homework'].strip()
    day = request.form['day']
    grade = session['user']['grade']

    if len(homework) < 5:
        flash("Mājasdarbam jābūt aprakstītam vismaz ar 5 simboliem.")
        return redirect(url_for('home'))

    schedule.append({
        'id': str(uuid.uuid4())[:8],
        'subject': subject,
        'homework': homework,
        'day': day,
        'grade': grade,
        'completed_by': []
    })

    save_schedule(schedule)
    flash("Mājasdarbs pievienots!")
    return redirect(url_for('home'))


@app.route('/toggle_done/<homework_id>', methods=['POST'])
def toggle_done(homework_id):
    if 'user' not in session or session['user']['role'] != 'student':
        return redirect(url_for('login'))

    username = session['user']['username']

    for item in schedule:
        if item['id'] == homework_id and item['grade'] == session['user']['grade']:
            if username in item['completed_by']:
                item['completed_by'].remove(username)
                flash("Atzīme noņemta: nav pabeigts.")
            else:
                item['completed_by'].append(username)
                flash("Lieliski! Mājasdarbs atzīmēts kā pabeigts.")
            save_schedule(schedule)
            break

    return redirect(url_for('home'))


@app.route('/delete_homework/<homework_id>', methods=['POST'])
def delete_homework(homework_id):
    if 'user' not in session or session['user']['role'] != 'teacher':
        return redirect(url_for('login'))

    for item in list(schedule):
        if item['id'] == homework_id and item['grade'] == session['user']['grade']:
            schedule.remove(item)
            save_schedule(schedule)
            flash("Mājasdarbs dzēsts.")
            break

    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
