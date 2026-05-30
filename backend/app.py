import sqlite3
import os
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.environ.get('DB_DIR', os.path.join(ROOT_DIR, 'backend', 'instance'))
DB_PATH = os.path.join(DB_DIR, 'app.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS fitness (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT DEFAULT '',
            note TEXT DEFAULT '',
            date TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    ''')
    conn.commit()
    conn.close()


# ---- CORS ----
@app.after_request
def add_cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    return resp


# ---- Static files ----
@app.route('/')
def serve_index():
    return send_from_directory(ROOT_DIR, 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(ROOT_DIR, filename)


# ---- Todos ----
@app.route('/api/todos', methods=['GET'])
def list_todos():
    conn = get_db()
    rows = conn.execute('SELECT * FROM todos ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/todos', methods=['POST'])
def add_todo():
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'text is required'}), 400
    conn = get_db()
    cur = conn.execute(
        'INSERT INTO todos (text, done, created_at) VALUES (?, ?, ?)',
        (text, 0, datetime.now().isoformat())
    )
    conn.commit()
    row = conn.execute('SELECT * FROM todos WHERE id = ?', (cur.lastrowid,)).fetchone()
    conn.close()
    return jsonify(dict(row)), 201


@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    data = request.get_json()
    conn = get_db()
    row = conn.execute('SELECT * FROM todos WHERE id = ?', (todo_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'not found'}), 404
    done = data.get('done', bool(row['done']))
    conn.execute('UPDATE todos SET done = ? WHERE id = ?', (1 if done else 0, todo_id))
    conn.commit()
    row = conn.execute('SELECT * FROM todos WHERE id = ?', (todo_id,)).fetchone()
    conn.close()
    return jsonify(dict(row))


@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    conn = get_db()
    conn.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True}), 200


# ---- Fitness ----
@app.route('/api/fitness', methods=['GET'])
def list_fitness():
    conn = get_db()
    rows = conn.execute('SELECT * FROM fitness ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/fitness', methods=['POST'])
def add_fitness():
    data = request.get_json()
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': 'title is required'}), 400
    now = datetime.now().isoformat()
    conn = get_db()
    cur = conn.execute(
        'INSERT INTO fitness (title, url, note, date, created_at) VALUES (?, ?, ?, ?, ?)',
        (title, data.get('url', ''), data.get('note', ''),
         datetime.now().strftime('%Y/%m/%d'), now)
    )
    conn.commit()
    row = conn.execute('SELECT * FROM fitness WHERE id = ?', (cur.lastrowid,)).fetchone()
    conn.close()
    return jsonify(dict(row)), 201


@app.route('/api/fitness/<int:fit_id>', methods=['DELETE'])
def delete_fitness(fit_id):
    conn = get_db()
    conn.execute('DELETE FROM fitness WHERE id = ?', (fit_id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True}), 200


# ---- Init ----
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
