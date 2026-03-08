from flask import Flask, request, jsonify
import sqlite3
import json
import os
from flask_cors import CORS 

app = Flask(__name__)
CORS(app)                   

# ====== 数据库路径（永远指向项目内 data/events.db） ======
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "events.db")

# ====== 初始化数据库（如果不存在就创建表） ======
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT,
            user_id TEXT,
            timestamp TEXT,
            metadata TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ====== 接收埋点 ======
@app.route('/track', methods=['POST'])
def track():
    data = request.get_json()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        "INSERT INTO events (event_name, user_id, timestamp, metadata) VALUES (?, ?, ?, ?)",
        (
            data['event_name'],
            data['user_id'],
            data['timestamp'],
            json.dumps(data.get('metadata', {}))
        )
    )

    conn.commit()
    conn.close()

    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True)
