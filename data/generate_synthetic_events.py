# data/generate_synthetic_events.py
"""
生成合成用户事件并写入 data/events.db
用法：
    python data/generate_synthetic_events.py
会往 data/events.db 写入多用户的 page_view/signup/purchase 事件（时间分布可控）
"""

import sqlite3, json, os, random
from datetime import datetime, timedelta

OUT_DB = os.path.join(os.path.dirname(__file__), "events.db")

random.seed(42)

def ensure_table():
    conn = sqlite3.connect(OUT_DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_name TEXT,
        user_id TEXT,
        timestamp TEXT,
        metadata TEXT
    );""")
    conn.commit()
    conn.close()

def insert_event(conn, event_name, user_id, ts, metadata=None):
    if metadata is None:
        metadata = {}
    c = conn.cursor()
    c.execute("INSERT INTO events (event_name, user_id, timestamp, metadata) VALUES (?, ?, ?, ?)",
              (event_name, user_id, ts.isoformat(), json.dumps(metadata)))
    conn.commit()

def generate(num_users=200, start_date=None):
    if start_date is None:
        start_date = datetime.utcnow() - timedelta(days=14)  # 两周数据
    conn = sqlite3.connect(OUT_DB)
    for i in range(1, num_users+1):
        uid = f"user_{i:04d}"
        # 每个用户有一个首次访问时间（随机在两周内）
        first = start_date + timedelta(days=random.randint(0,13), hours=random.randint(0,23), minutes=random.randint(0,59))
        # 所有用户至少有 page_view
        insert_event(conn, "page_view", uid, first)
        # 随机决定是否 signup（高、中、低三组）
        group = random.choices(["high","mid","low"], weights=[0.2,0.5,0.3])[0]
        if group == "high":
            # 70% 转 signup, 60% 转 purchase
            if random.random() < 0.7:
                t_signup = first + timedelta(minutes=random.randint(1,60))
                insert_event(conn, "signup", uid, t_signup)
                if random.random() < 0.6:
                    t_purchase = t_signup + timedelta(minutes=random.randint(5,300))
                    insert_event(conn, "purchase", uid, t_purchase)
        elif group == "mid":
            # 40% signup, 20% purchase
            if random.random() < 0.4:
                t_signup = first + timedelta(minutes=random.randint(1,120))
                insert_event(conn, "signup", uid, t_signup)
                if random.random() < 0.2:
                    t_purchase = t_signup + timedelta(hours=random.randint(1,72))
                    insert_event(conn, "purchase", uid, t_purchase)
        else:
            # low: 10% signup, 5% purchase
            if random.random() < 0.1:
                t_signup = first + timedelta(hours=random.randint(1,48))
                insert_event(conn, "signup", uid, t_signup)
                if random.random() < 0.05:
                    t_purchase = t_signup + timedelta(days=random.randint(0,7))
                    insert_event(conn, "purchase", uid, t_purchase)

        # 额外噪声：随机重复 page_view 点击
        for _ in range(random.randint(0,3)):
            ts_noise = first + timedelta(minutes=random.randint(1,1000))
            insert_event(conn, "page_view", uid, ts_noise)
    conn.close()
    print(f"生成完成：{num_users} 个用户事件已写入 {OUT_DB}")

if __name__ == "__main__":
    ensure_table()
    generate(num_users=300)
