import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import get_db_connection, update_remaining_leaves, get_remaining_leaves
from config import TOTAL_LEAVES_PER_YEAR, COLORSCHEME
from datetime import datetime, timedelta
import sqlite3

def user_dashboard(username):
    st.title(f"Welcome, {username}!")

    menu = ["Leave Summary", "Apply for Leave", "Leave History", "Team Calendar"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Leave Summary":
        show_leave_summary(username)
    elif choice == "Apply for Leave":
        apply_for_leave(username)
    elif choice == "Leave History":
        show_leave_history(username)
    elif choice == "Team Calendar":
        show_team_calendar(username)

def show_leave_summary(username):
    st.header("Leave Summary")
    conn = get_db_connection()
    if conn is None:
        st.error("Unable to connect to the database. Please try again later.")
        return

    user_id = get_user_id(username, conn)
    if user_id is None:
        conn.close()
        return

    remaining_leaves = get_remaining_leaves(user_id)
    if remaining_leaves is None:
        st.error("Unable to fetch remaining leaves. Please try again later.")
        conn.close()
        return

    taken_leaves = TOTAL_LEAVES_PER_YEAR - remaining_leaves

    current_year = datetime.now().year
    df = pd.read_sql_query(f"""
        SELECT leave_type, COUNT(*) as count, SUM(julianday(end_date) - julianday(start_date) + 1) as total_days
        FROM leaves
        WHERE user_id = ? AND strftime('%Y', start_date) = '{current_year}'
        GROUP BY leave_type
    """, conn, params=(user_id,))
    conn.close()

    col1, col2, col3 = st.columns(3)
    col1.metric("Available Leaves", remaining_leaves)
    col2.metric("Taken Leaves", taken_leaves)
    col3.metric("Upcoming Leaves", get_upcoming_leaves_count(user_id))

    # Create a unique radial chart for leave utilization
    fig = go.Figure(go.Barpolar(
        r=[taken_leaves, remaining_leaves],
        theta=['Taken', 'Remaining'],
        width=[0.5, 0.5],
        marker_color=[COLORSCHEME['primary'], COLORSCHEME['secondary']],
        marker_line_color="black",
        marker_line_width=2,
        opacity=0.8
    ))
    fig.update_layout(
        title="Leave Utilization",
        polar=dict(
            radialaxis=dict(range=[0, TOTAL_LEAVES_PER_YEAR], showticklabels=False, ticks=''),
            angularaxis=dict(showticklabels=True, ticks='')
        )
    )
    st.plotly_chart(fig)

    if not df.empty:
        st.subheader(f"Year-to-Date Leave Breakdown ({current_year})")
        
        # Create a unique bubble chart for leave type distribution
        fig = px.scatter(df, x='count', y='total_days', size='count', color='leave_type',
                         hover_name='leave_type', text='leave_type',
                         title="Leave Type Distribution",
                         labels={'count': 'Number of Leaves', 'total_days': 'Total Days Taken'})
        fig.update_traces(textposition='top center')
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig)
    else:
        st.info("No leave data available for this year.")
        
def get_user_id(username, conn):
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE username = ?', (username,))
    user = cur.fetchone()
    if user is None:
        st.error("User not found.")
        return None
    return user['id']

def get_upcoming_leaves_count(user_id):
    conn = get_db_connection()
    if conn is None:
        return 0

    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) as count
        FROM leaves
        WHERE user_id = ? AND start_date >= date('now') AND status = 'approved'
    """, (user_id,))
    result = cur.fetchone()
    conn.close()
    return result['count'] if result else 0

def apply_for_leave(username):
    st.header("Apply for Leave")
    conn = get_db_connection()
    if conn is None:
        st.error("Unable to connect to the database. Please try again later.")
        return

    user_id = get_user_id(username, conn)
    if user_id is None:
        conn.close()
        return

    remaining_leaves = get_remaining_leaves(user_id)
    if remaining_leaves is None:
        st.error("Unable to fetch remaining leaves. Please try again later.")
        conn.close()
        return

    with st.form("leave_application_form"):
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        leave_type = st.selectbox("Leave Type", ["Annual Leave", "Sick Leave", "Personal Leave", "Other"])
        reason = st.text_area("Reason")
        submitted = st.form_submit_button("Submit Leave Application")

        if submitted:
            if start_date <= end_date:
                days_requested = (end_date - start_date).days + 1
                if days_requested <= remaining_leaves:
                    try:
                        cur = conn.cursor()
                        cur.execute('''
                        INSERT INTO leaves (user_id, start_date, end_date, reason, status, leave_type)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ''', (user_id, start_date.isoformat(), end_date.isoformat(), reason, 'pending', leave_type))
                        conn.commit()
                        if update_remaining_leaves(user_id, days_requested):
                            st.success("Leave application submitted successfully!")
                        else:
                            st.error("Error updating remaining leaves. Please try again.")
                    except sqlite3.Error as e:
                        st.error(f"Error submitting leave application: {e}")
                else:
                    st.error(f"You don't have enough leaves. Available: {remaining_leaves}, Requested: {days_requested}")
            else:
                st.error("End date must be after start date")

    conn.close()

def show_leave_history(username):
    st.header("Leave History")
    conn = get_db_connection()
    if conn is None:
        st.error("Unable to connect to the database. Please try again later.")
        return

    user_id = get_user_id(username, conn)
    if user_id is None:
        conn.close()
        return

    df = pd.read_sql_query('SELECT * FROM leaves WHERE user_id = ? ORDER BY start_date DESC', conn, params=(user_id,))
    conn.close()

    if not df.empty:
        df['start_date'] = pd.to_datetime(df['start_date'])
        df['end_date'] = pd.to_datetime(df['end_date'])
        df['duration'] = (df['end_date'] - df['start_date']).dt.days + 1
        df['start_date'] = df['start_date'].dt.strftime('%Y-%m-%d')
        df['end_date'] = df['end_date'].dt.strftime('%Y-%m-%d')
        
        columns = ['start_date', 'end_date', 'duration', 'leave_type', 'reason', 'status']
        df = df[columns]
        
        def color_status(val):
            if val == 'approved':
                return f'background-color: {COLORSCHEME["success"]}; color: white'
            elif val == 'pending':
                return f'background-color: {COLORSCHEME["warning"]}; color: black'
            else:
                return f'background-color: {COLORSCHEME["danger"]}; color: white'
        
        styled_df = df.style.applymap(color_status, subset=['status'])
        
        st.dataframe(styled_df, use_container_width=True)
        
        fig = px.pie(df, names='leave_type', title='Leave Type Distribution')
        st.plotly_chart(fig)
    else:
        st.info("No leave history available.")

def show_team_calendar(username):
    st.header("Team Calendar")
    conn = get_db_connection()
    if conn is None:
        st.error("Unable to connect to the database. Please try again later.")
        return

    user_id = get_user_id(username, conn)
    if user_id is None:
        conn.close()
        return

    cur = conn.cursor()
    cur.execute('SELECT department FROM users WHERE id = ?', (user_id,))
    user = cur.fetchone()
    department = user['department']

    df = pd.read_sql_query("""
        SELECT leaves.*, users.username
        FROM leaves
        JOIN users ON leaves.user_id = users.id
        WHERE users.department = ? AND leaves.status = 'approved'
    """, conn, params=(department,))
    conn.close()

    if not df.empty:
        df['start_date'] = pd.to_datetime(df['start_date'])
        df['end_date'] = pd.to_datetime(df['end_date'])

        year = datetime.now().year
        date_range = pd.date_range(start=f'{year}-01-01', end=f'{year}-12-31', freq='D')
        calendar_df = pd.DataFrame(index=date_range, columns=['Leave Count'])

        for _, row in df.iterrows():
            mask = (calendar_df.index >= row['start_date']) & (calendar_df.index <= row['end_date'])
            calendar_df.loc[mask, 'Leave Count'] += 1

        fig = px.imshow(calendar_df.T,
                        x=calendar_df.index,
                        y=calendar_df.columns,
                        color_continuous_scale='YlOrRd',
                        title=f'Team Leave Calendar - {department} Department')
        fig.update_xaxes(tickformat='%b\n%Y')
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

        st.write("Select a date to see team leave details:")
        selected_date = st.date_input("Select a date", datetime.now())
        selected_leaves = df[(df['start_date'] <= selected_date) & (df['end_date'] >= selected_date)]
        if not selected_leaves.empty:
            st.write(f"Team members on leave on {selected_date}:")
            for _, leave in selected_leaves.iterrows():
                st.write(f"- {leave['username']}: {leave['leave_type']}")
        else:
            st.write("No team members on leave for this date.")
    else:
        st.info("No team leave data available for calendar view.")