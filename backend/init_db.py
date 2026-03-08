import sqlite3
import os

os.makedirs('../data', exist_ok=True)
conn = sqlite3.connect('../data/events.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name TEXT,
    user_id TEXT,
    timestamp TEXT,
    metadata TEXT
)
''')

conn.commit()
conn.close()
print("数据库创建成功")
