from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
import re

app = Flask(__name__)
app.secret_key = "secret123"

DATA_FILE = "users.json"

# ----------------- Helpers -----------------

def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f)


def is_valid_email(email):
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email)


def is_strong_password(pw):
    # min 6 chars, at least 1 number
    return len(pw) >= 6 and any(c.isdigit() for c in pw)


users = load_users()

@app.route('/')
def home():
    if 'user' in session:
        role = session['user']['role']
        if role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    global users
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        role = request.form['role']

        # Username unique
        if username in users:
            flash('Username already exists')
            return redirect(url_for('register'))

        # Email unique
        if any(u.get('email') == email for u in users.values()):
            flash('Email already registered')
            return redirect(url_for('register'))

        # Email validation
        if not is_valid_email(email):
            flash('Invalid email format')
            return redirect(url_for('register'))

        # Password strength
        if not is_strong_password(password):
            flash('Password must be at least 6 characters and include a number')
            return redirect(url_for('register'))

        users[username] = {
            'email': email,
            'password': password,
            'role': role
        }

        save_users(users)
        flash('Account created! Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        for username, user in users.items():
            if user['email'] == email and user['password'] == password:
                session['user'] = {
                    'username': username,
                    'role': user['role']
                }
                return redirect(url_for('home'))

        flash('Invalid email or password')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/student')
def student_dashboard():
    if 'user' not in session or session['user']['role'] != 'student':
        return redirect(url_for('login'))
    return render_template('student_dashboard.html', user=session['user'])


@app.route('/teacher')
def teacher_dashboard():
    if 'user' not in session or session['user']['role'] != 'teacher':
        return redirect(url_for('login'))
    return render_template('teacher_dashboard.html', user=session['user'])


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
