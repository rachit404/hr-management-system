import sqlite3
import pandas as pd

def get_db_connection():
    conn = sqlite3.connect('hr_database.db')
    conn.row_factory = sqlite3.Row
    return conn

def table_creation():
    conn = get_db_connection()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS interviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_name TEXT NOT NULL,
        interview_date TEXT NOT NULL
    )
    ''')
    conn.commit()

def add_interview(candidate_name, interview_date):
    conn = get_db_connection()
    conn.execute('INSERT INTO interviews (candidate_name, interview_date) VALUES (?, ?)', (candidate_name, interview_date))
    conn.commit()
    conn.close()

def get_interviews():
    conn = get_db_connection()
    interviews = pd.read_sql_query("SELECT * FROM interviews ORDER BY id", conn)
    conn.close()
    return interviews

def delete_interview(interview_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM interviews WHERE id = ?', (interview_id,))
    conn.commit()

    # Renumber the remaining IDs
    interviews = pd.read_sql_query("SELECT * FROM interviews ORDER BY id", conn)
    for idx, row in enumerate(interviews.itertuples(), start=1):
        conn.execute('UPDATE interviews SET id = ? WHERE id = ?', (idx, row.id))
    conn.commit()
    conn.close()

def delete_all_interviews():
    conn = get_db_connection()
    conn.execute('DELETE FROM interviews')
    conn.execute('DELETE FROM sqlite_sequence WHERE name="interviews"')
    conn.commit()
    conn.close()
