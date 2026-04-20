from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = "secret123"

DATA_FILE = "users.json"

# Load users from JSON file
def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

# Save users to JSON file
def save_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f)

users = load_users()

SCHEDULE_FILE = "schedule.json"

def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r") as f:
            return json.load(f)
    return []

def save_schedule(data):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(data, f)

schedule = load_schedule()

@app.route('/')
def home():
    if 'user' in session:
        return render_template('dashboard.html', user=session['user'], schedule=schedule)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    global users
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        grade = request.form['grade']

        if username in users:
            return "User already exists"

        users[username] = {
            'password': password,
            'role': role,
            'grade':grade
        }

        save_users(users)

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users.get(username)

        if user and user['password'] == password:
            session['user'] = {
                'username': username,
                'role': user['role'],
                'grade': user['grade']
            }
            return redirect(url_for('home'))
        else:
            return "Invalid credentials"

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/add_homework', methods=['POST'])
def add_homework():
    if 'user' not in session or session['user']['role'] != 'teacher':
        return redirect(url_for('login'))

    subject = request.form['subject']
    homework = request.form['homework']
    day = request.form['day']
    grade = session['user']['grade']


    schedule.append({
        'subject': subject,
        'homework': homework,
        'day': day,
        'grade': grade
    })

    save_schedule(schedule)

    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)