import sqlite3
from datetime import date

DB_NAME = "screener.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS graham_scores (
                ticker TEXT,
                run_date DATE,
                score REAL,
                PRIMARY KEY (ticker, run_date)
            )
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_graham_scores_run_date ON graham_scores(run_date)
        ''')

def save_scores(dataframe):
    today = date.today().isoformat()
    with sqlite3.connect(DB_NAME) as conn:
        for _, row in dataframe.iterrows():
            conn.execute(
                "INSERT OR REPLACE INTO graham_scores (ticker, run_date, score) VALUES (?, ?, ?)",
                (row["ticker"], today, row["score"])
            )

def get_last_score(ticker):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.execute(
            "SELECT score FROM graham_scores WHERE ticker = ? ORDER BY run_date DESC LIMIT 1 OFFSET 1",
            (ticker,)
        )
        row = cur.fetchone()
        return row[0] if row else None
