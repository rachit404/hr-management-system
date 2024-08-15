import sqlite3
import pandas as pd

def get_db_connection():
    conn = sqlite3.connect('hr_database.db')
    conn.row_factory = sqlite3.Row
    return conn

def add_interview(candidate_name, interview_date):
    try:
        with get_db_connection() as conn:
            conn.execute('INSERT INTO interviews (candidate_name, interview_date) VALUES (?, ?)', 
                         (candidate_name, interview_date))
            conn.commit()
    except sqlite3.DatabaseError as e:
        print(f"Error adding interview: {e}")

def get_interviews():
    try:
        with get_db_connection() as conn:
            interviews = pd.read_sql_query("SELECT * FROM interviews ORDER BY id", conn)
            return interviews
    except sqlite3.DatabaseError as e:
        print(f"Error retrieving interviews: {e}")
        return pd.DataFrame()

def delete_interview(interview_id):
    try:
        with get_db_connection() as conn:
            conn.execute('DELETE FROM interviews WHERE id = ?', (interview_id,))
            conn.commit()

            # If you must renumber IDs
            interviews = pd.read_sql_query("SELECT * FROM interviews ORDER BY id", conn)
            for idx, row in enumerate(interviews.itertuples(), start=1):
                conn.execute('UPDATE interviews SET id = ? WHERE id = ?', (idx, row.id))
            conn.commit()
    except sqlite3.DatabaseError as e:
        print(f"Error deleting interview: {e}")

def delete_all_interviews():
    try:
        with get_db_connection() as conn:
            conn.execute('DELETE FROM interviews')
            conn.execute('DELETE FROM sqlite_sequence WHERE name="interviews"')
            conn.commit()
    except sqlite3.DatabaseError as e:
        print(f"Error deleting all interviews: {e}")
