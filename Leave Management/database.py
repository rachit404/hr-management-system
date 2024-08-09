import sqlite3
import pandas as pd
from config import DB_PATH, TOTAL_LEAVES_PER_YEAR
from datetime import datetime

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if conn is None:
        return
    
    try:
        cur = conn.cursor()
        
        cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin BOOLEAN NOT NULL DEFAULT 0,
            department TEXT,
            remaining_leaves INTEGER NOT NULL DEFAULT 20
        )
        ''')

        cur.execute('''
        CREATE TABLE IF NOT EXISTS leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL,
            leave_type TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        conn.commit()
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")
    finally:
        conn.close()

def add_user(username, password, department, is_admin=False):
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO users (username, password, department, is_admin, remaining_leaves) VALUES (?, ?, ?, ?, ?)',
                    (username, password, department, is_admin, TOTAL_LEAVES_PER_YEAR))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error adding user: {e}")
        return False
    finally:
        conn.close()

def update_remaining_leaves(user_id, days_taken):
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute('UPDATE users SET remaining_leaves = remaining_leaves - ? WHERE id = ?', (days_taken, user_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating remaining leaves: {e}")
        return False
    finally:
        conn.close()

def get_remaining_leaves(user_id):
    conn = get_db_connection()
    if conn is None:
        return None
    
    try:
        cur = conn.cursor()
        cur.execute('SELECT remaining_leaves FROM users WHERE id = ?', (user_id,))
        result = cur.fetchone()
        return result['remaining_leaves'] if result else None
    except sqlite3.Error as e:
        print(f"Error getting remaining leaves: {e}")
        return None
    finally:
        conn.close()

def get_user_leaves(user_id):
    conn = get_db_connection()
    if conn is None:
        return None
    
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM leaves WHERE user_id = ? ORDER BY start_date DESC', (user_id,))
        return cur.fetchall()
    except sqlite3.Error as e:
        print(f"Error getting user leaves: {e}")
        return None
    finally:
        conn.close()

def get_all_leaves():
    conn = get_db_connection()
    if conn is None:
        return None
    
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT leaves.*, users.username, users.department 
            FROM leaves 
            JOIN users ON leaves.user_id = users.id 
            ORDER BY start_date DESC
        ''')
        return cur.fetchall()
    except sqlite3.Error as e:
        print(f"Error getting all leaves: {e}")
        return None
    finally:
        conn.close()

def update_leave_status(leave_id, status):
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute('UPDATE leaves SET status = ? WHERE id = ?', (status, leave_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating leave status: {e}")
        return False
    finally:
        conn.close()

def get_department_leaves(department):
    conn = get_db_connection()
    if conn is None:
        return None
    
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT leaves.*, users.username 
            FROM leaves 
            JOIN users ON leaves.user_id = users.id 
            WHERE users.department = ? 
            ORDER BY start_date DESC
        ''', (department,))
        return cur.fetchall()
    except sqlite3.Error as e:
        print(f"Error getting department leaves: {e}")
        return None
    finally:
        conn.close()

# New functions

def get_all_users():
    conn = get_db_connection()
    if conn is None:
        return None
    
    try:
        df = pd.read_sql_query("SELECT id, username, department, is_admin, remaining_leaves FROM users", conn)
        return df
    except sqlite3.Error as e:
        print(f"Error fetching all users: {e}")
        return None
    finally:
        conn.close()

# In database.py

def update_user_data(user_id, username, department, is_admin, new_remaining_leaves, adjust_leaves, adjustment_reason):
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute('''
            UPDATE users 
            SET username = ?, department = ?, is_admin = ?, remaining_leaves = ? 
            WHERE id = ?
        ''', (username, department, is_admin, new_remaining_leaves, user_id))
        
        if adjust_leaves != 0:
            today = datetime.now().date().isoformat()
            cur.execute('''
                INSERT INTO leaves (user_id, start_date, end_date, reason, status, leave_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, today, today, adjustment_reason, 'approved', 'Administrative Adjustment'))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating user data: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()