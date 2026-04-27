from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import logging

app = Flask(__name__)
app.secret_key = "secret123"

DB_FILE = "school_diary.db"
ALLOWED_ROLES = {"student", "teacher"}
ALLOWED_GRADES = {"Grade1", "Grade2", "Grade3", "Grade4"}
ALLOWED_DAYS = {"Pirmdiena", "Otrdiena", "Tresdiena", "Ceturtdiena", "Piektdiena"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger(__name__)


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            grade TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS homeworks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            homework TEXT NOT NULL,
            day TEXT NOT NULL,
            grade TEXT NOT NULL,
            created_by TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def validate_user_input(username, password, role, grade):
    if len(username.strip()) < 3:
        return "Lietotājvārdam jābūt vismaz 3 simbolu garam."
    if len(password) < 8:
        return "Parolei jābūt vismaz 8 simbolu garai."
    if role not in ALLOWED_ROLES:
        return "Nederīga lietotāja loma."
    if grade not in ALLOWED_GRADES:
        return "Nederīga klase."
    return None


def validate_homework_input(subject, homework, day, grade):
    if not subject.strip() or len(subject.strip()) > 120:
        return "Mācību priekšmets ir obligāts (līdz 120 rakstu zīmēm)."
    if not homework.strip() or len(homework.strip()) > 500:
        return "Mājasdarbs ir obligāts (līdz 500 rakstu zīmēm)."
    if day not in ALLOWED_DAYS:
        return "Nederīga nedēļas diena."
    if grade not in ALLOWED_GRADES:
        return "Nederīga klase."
    return None


@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    schedule = conn.execute(
        "SELECT id, subject, homework, day, grade, created_by FROM homeworks ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template('dashboard.html', user=session['user'], schedule=schedule)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        role = request.form['role']
        grade = request.form['grade']

        validation_error = validate_user_input(username, password, role, grade)
        if validation_error:
            flash(validation_error, 'error')
            return redirect(url_for('register'))

        conn = get_db_connection()
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            conn.close()
            flash("Lietotājs ar šādu vārdu jau eksistē.", 'error')
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)
        conn.execute(
            "INSERT INTO users (username, password_hash, role, grade) VALUES (?, ?, ?, ?)",
            (username, password_hash, role, grade)
        )
        conn.commit()
        conn.close()

        logger.info("New user registered: %s (%s)", username, role)
        flash("Reģistrācija veiksmīga. Vari ielogoties.", 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute(
            "SELECT username, password_hash, role, grade FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user'] = {
                'username': user['username'],
                'role': user['role'],
                'grade': user['grade']
            }
            logger.info("Successful login: %s", username)
            return redirect(url_for('home'))

        logger.warning("Failed login attempt for username: %s", username)
        flash("Nepareizs lietotājvārds vai parole.", 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    user = session.get('user', {}).get('username')
    session.pop('user', None)
    if user:
        logger.info("Logout: %s", user)
    return redirect(url_for('login'))


@app.route('/add_homework', methods=['POST'])
def add_homework():
    if 'user' not in session or session['user']['role'] != 'teacher':
        flash("Tikai skolotājs var pievienot mājasdarbus.", 'error')
        return redirect(url_for('login'))

    subject = request.form['subject'].strip()
    homework = request.form['homework'].strip()
    day = request.form['day']
    grade = session['user']['grade']

    validation_error = validate_homework_input(subject, homework, day, grade)
    if validation_error:
        flash(validation_error, 'error')
        return redirect(url_for('home'))

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO homeworks (subject, homework, day, grade, created_by) VALUES (?, ?, ?, ?, ?)",
        (subject, homework, day, grade, session['user']['username'])
    )
    conn.commit()
    conn.close()

    logger.info("Homework added by %s for %s", session['user']['username'], grade)
    flash("Mājasdarbs pievienots.", 'success')
    return redirect(url_for('home'))


@app.route('/edit_homework/<int:homework_id>', methods=['POST'])
def edit_homework(homework_id):
    if 'user' not in session or session['user']['role'] != 'teacher':
        flash("Tikai skolotājs var rediģēt mājasdarbus.", 'error')
        return redirect(url_for('login'))

    subject = request.form['subject'].strip()
    homework = request.form['homework'].strip()
    day = request.form['day']
    grade = session['user']['grade']

    validation_error = validate_homework_input(subject, homework, day, grade)
    if validation_error:
        flash(validation_error, 'error')
        return redirect(url_for('home'))

    conn = get_db_connection()
    conn.execute(
        """
        UPDATE homeworks
        SET subject = ?, homework = ?, day = ?
        WHERE id = ? AND grade = ?
        """,
        (subject, homework, day, homework_id, grade)
    )
    conn.commit()
    conn.close()

    logger.info("Homework %s updated by %s", homework_id, session['user']['username'])
    flash("Mājasdarbs atjaunināts.", 'success')
    return redirect(url_for('home'))


@app.route('/delete_homework/<int:homework_id>', methods=['POST'])
def delete_homework(homework_id):
    if 'user' not in session or session['user']['role'] != 'teacher':
        flash("Tikai skolotājs var dzēst mājasdarbus.", 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute(
        "DELETE FROM homeworks WHERE id = ? AND grade = ?",
        (homework_id, session['user']['grade'])
    )
    conn.commit()
    conn.close()

    logger.info("Homework %s deleted by %s", homework_id, session['user']['username'])
    flash("Mājasdarbs dzēsts.", 'success')
    return redirect(url_for('home'))


init_db()

if __name__ == '__main__':
    app.run(debug=True)