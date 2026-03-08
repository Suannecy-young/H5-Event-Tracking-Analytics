# analysis/funnel_and_retention.py
"""
计算并输出：
 - 漏斗（去重用户数、转化率）
 - 留存（基于首次 page_view 的日 cohort）
输出文件:
 - analysis/funnel_report.csv
 - analysis/retention_matrix.csv
 - analysis/retention_matrix.png
"""

import os, sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(__file__))
DB = os.path.join(BASE, "data", "events.db")
OUT = os.path.join(os.path.dirname(__file__))

def read_events():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT event_name, user_id, timestamp FROM events", conn)
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    return df

def compute_funnel(df, steps):
    rows = []
    first_users = set(df[df['event_name']==steps[0]]['user_id'].dropna().unique())
    for i, s in enumerate(steps):
        users = set(df[df['event_name']==s]['user_id'].dropna().unique())
        prev_users = set(df[df['event_name']==steps[i-1]]['user_id'].dropna().unique()) if i>0 else first_users
        rows.append({
            'step': s,
            'users': len(users),
            'pct_from_prev': len(users)/len(prev_users) if prev_users else 0,
            'pct_from_first': len(users)/len(first_users) if first_users else 0
        })
    return pd.DataFrame(rows)

def compute_retention(df, cohort_event='page_view', days=14):
    # 1) 对每个 user 找到首次 cohort_event 时间（cohort_day）
    first = df[df['event_name']==cohort_event].groupby('user_id')['timestamp'].min().reset_index()
    first.columns = ['user_id','cohort_ts']
    first['cohort_day'] = first['cohort_ts'].dt.date

    # 2) 合并回去，计算用户在每个 day 相对于 cohort 的 day_index
    df2 = df.merge(first[['user_id','cohort_day']], on='user_id', how='inner')
    df2['event_day'] = df2['timestamp'].dt.date
    df2['day_index'] = (pd.to_datetime(df2['event_day']) - pd.to_datetime(df2['cohort_day'])).dt.days
    # 3) 计算 cohort x day 矩阵（按独立用户）
    cohorts = first['cohort_day'].sort_values().unique()
    matrix = []
    for cohort in cohorts:
        cohort_users = set(first[first['cohort_day']==cohort]['user_id'])
        row = {'cohort_day': cohort, 'cohort_size': len(cohort_users)}
        for d in range(0, days+1):
            users_on_day = df2[(df2['cohort_day']==cohort) & (df2['day_index']==d)]['user_id'].unique()
            row[f'day_{d}'] = len(set(users_on_day))
        matrix.append(row)
    mat = pd.DataFrame(matrix)
    # 4) 归一化为留存率（占 cohort_size）
    for d in range(0, days+1):
        mat[f'day_{d}_rate'] = mat[f'day_{d}'] / mat['cohort_size']
    return mat

def plot_retention(mat, days=14, png_path=None):
    # 使用热力图可视化
    cohorts = mat['cohort_day'].astype(str).tolist()
    rates = mat[[f'day_{d}_rate' for d in range(0, days+1)]].values
    fig, ax = plt.subplots(figsize=(10, max(2, len(cohorts)*0.25)))
    im = ax.imshow(rates, aspect='auto', cmap='Blues', vmin=0, vmax=1)
    ax.set_yticks(range(len(cohorts)))
    ax.set_yticklabels(cohorts)
    ax.set_xticks(range(days+1))
    ax.set_xticklabels([f'D{d}' for d in range(0, days+1)], rotation=45)
    ax.set_xlabel('Days since cohort')
    ax.set_ylabel('Cohort day')
    fig.colorbar(im, ax=ax, label='Retention rate')
    plt.tight_layout()
    if png_path:
        plt.savefig(png_path, dpi=150)
    return fig

def main():
    df = read_events()
    steps = ['page_view','signup','purchase']
    funnel = compute_funnel(df, steps)
    funnel.to_csv(os.path.join(OUT, 'funnel_report.csv'), index=False)
    print("漏斗：")
    print(funnel)

    retention = compute_retention(df, cohort_event='page_view', days=14)
    retention.to_csv(os.path.join(OUT, 'retention_matrix.csv'), index=False)
    print("留存矩阵已保存：", os.path.join(OUT, 'retention_matrix.csv'))
    fig = plot_retention(retention, days=14, png_path=os.path.join(OUT, 'retention_matrix.png'))
    print("留存热力图已保存：", os.path.join(OUT, 'retention_matrix.png'))

if __name__ == "__main__":
    main()
