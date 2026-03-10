from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
from datetime import date, datetime, timedelta

app = Flask(__name__)
DB = 'planner.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        completed INTEGER DEFAULT 0,
        task_date TEXT NOT NULL,
        category TEXT DEFAULT 'todo',
        urgency TEXT DEFAULT 'today',
        complexity TEXT DEFAULT 'quick',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        meeting_date TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT,
        note_date TEXT NOT NULL UNIQUE,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def purge_old_data():
    """Delete all data older than 24 hours."""
    cutoff = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d')
    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE task_date < ?", (cutoff,))
    conn.execute("DELETE FROM meetings WHERE meeting_date < ?", (cutoff,))
    conn.execute("DELETE FROM notes WHERE note_date < ?", (cutoff,))
    conn.commit()
    conn.close()

init_db()

@app.before_request
def before_request():
    purge_old_data()

@app.route('/')
def index():
    return redirect(url_for('daily'))

@app.route('/daily')
def daily():
    today = request.args.get('date', date.today().isoformat())
    return render_template('daily.html', today=today, today_real=date.today().isoformat())

@app.route('/matrix')
def matrix():
    today = request.args.get('date', date.today().isoformat())
    return render_template('matrix.html', today=today, today_real=date.today().isoformat())

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    d = request.args.get('date', date.today().isoformat())
    conn = get_db()
    tasks = conn.execute('SELECT * FROM tasks WHERE task_date=? ORDER BY created_at', (d,)).fetchall()
    conn.close()
    return jsonify([dict(t) for t in tasks])

@app.route('/api/tasks', methods=['POST'])
def add_task():
    data = request.json
    conn = get_db()
    conn.execute('INSERT INTO tasks (title, task_date, category, urgency, complexity) VALUES (?,?,?,?,?)',
        (data['title'], data.get('task_date', date.today().isoformat()),
         data.get('category', 'todo'), data.get('urgency', 'today'), data.get('complexity', 'quick')))
    conn.commit()
    task_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    task = conn.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()
    conn.close()
    return jsonify(dict(task))

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.json
    conn = get_db()
    fields, vals = [], []
    for key in ['title', 'completed', 'category', 'urgency', 'complexity']:
        if key in data:
            fields.append(f'{key}=?')
            vals.append(data[key])
    vals.append(task_id)
    conn.execute(f'UPDATE tasks SET {", ".join(fields)} WHERE id=?', vals)
    conn.commit()
    task = conn.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()
    conn.close()
    return jsonify(dict(task))

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    conn = get_db()
    conn.execute('DELETE FROM tasks WHERE id=?', (task_id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/meetings', methods=['GET'])
def get_meetings():
    d = request.args.get('date', date.today().isoformat())
    conn = get_db()
    meetings = conn.execute('SELECT * FROM meetings WHERE meeting_date=? ORDER BY created_at', (d,)).fetchall()
    conn.close()
    return jsonify([dict(m) for m in meetings])

@app.route('/api/meetings', methods=['POST'])
def add_meeting():
    data = request.json
    conn = get_db()
    conn.execute('INSERT INTO meetings (title, meeting_date) VALUES (?,?)',
        (data['title'], data.get('meeting_date', date.today().isoformat())))
    conn.commit()
    mid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    m = conn.execute('SELECT * FROM meetings WHERE id=?', (mid,)).fetchone()
    conn.close()
    return jsonify(dict(m))

@app.route('/api/meetings/<int:mid>', methods=['DELETE'])
def delete_meeting(mid):
    conn = get_db()
    conn.execute('DELETE FROM meetings WHERE id=?', (mid,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/notes', methods=['GET'])
def get_notes():
    d = request.args.get('date', date.today().isoformat())
    conn = get_db()
    note = conn.execute('SELECT * FROM notes WHERE note_date=?', (d,)).fetchone()
    conn.close()
    return jsonify(dict(note) if note else {'content': '', 'note_date': d})

@app.route('/api/notes', methods=['POST'])
def save_notes():
    data = request.json
    d = data.get('note_date', date.today().isoformat())
    conn = get_db()
    conn.execute('INSERT INTO notes (content, note_date) VALUES (?,?) ON CONFLICT(note_date) DO UPDATE SET content=?, updated_at=CURRENT_TIMESTAMP',
        (data['content'], d, data['content']))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
