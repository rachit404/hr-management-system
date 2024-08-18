import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import get_db_connection,  add_user, update_user_data, get_all_users
from config import COLORSCHEME
from datetime import datetime

def admin_dashboard():
    st.title("Admin Dashboard")

    menu = ["Leave Overview", "Manage Leaves", "Interview Scheduling", "Create User", "User Management"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Leave Overview":
        show_leave_overview()
        show_leave_utilization()
        show_top_leave_reasons()
        show_leave_trends()
    elif choice == "Manage Leaves":
        manage_leaves()
    elif choice == "Interview Scheduling":
        st.markdown("""
        <style>
        .button {
            margin-top: 40px;
            display: inline-block;
            padding: 10px 20px;
            font-size: 16px;
            font-weight: bold;
            color: #e72d2e;
            background-color: #0e1117;
            border: 0.5px solid #00F;
            border-radius: 5px;
            text-align: center;
            text-decoration: none;
            cursor: pointer;
        }
        .button:hover {
            color: #e72d2e;
            border: 1px solid #e72d2e;
            text-decoration: none;
        }
        </style>

        <a href="https://interview-sched.streamlit.app/" class="button" target="_blank">Interview Scheduling</a>
        """, unsafe_allow_html=True)
    elif choice == "Create User":
        create_user()
    elif choice == "User Management":
        user_management()

def show_leave_overview():
    st.header("Leave Overview")
    conn = get_db_connection()
    if conn is None:
        st.error("Unable to connect to the database. Please try again later.")
        return

    df = pd.read_sql_query("""
        SELECT users.department, leaves.status, COUNT(*) as count
        FROM leaves
        JOIN users ON leaves.user_id = users.id
        GROUP BY users.department, leaves.status
    """, conn)
    conn.close()

    if not df.empty:
        fig = px.bar(df, x='department', y='count', color='status', title="Leave Distribution by Department",
                     labels={'count': 'Number of Leaves', 'department': 'Department'},
                     color_discrete_map={'approved': COLORSCHEME['success'], 
                                         'pending': COLORSCHEME['warning'],
                                         'rejected': COLORSCHEME['danger']})
        st.plotly_chart(fig)
    else:
        st.write("No leave data available.")

def show_leave_utilization():
    st.subheader("Leave Utilization")
    conn = get_db_connection()
    if conn is None:
        st.error("Unable to connect to the database. Please try again later.")
        return

    df = pd.read_sql_query("""
        SELECT users.department, 
               AVG(users.remaining_leaves) as avg_remaining_leaves,
               20 - AVG(users.remaining_leaves) as avg_used_leaves
        FROM users
        GROUP BY users.department
    """, conn)
    conn.close()

    if not df.empty:
        fig = px.bar(df, x='department', y=['avg_used_leaves', 'avg_remaining_leaves'],
                     title="Average Leave Utilization by Department",
                     labels={'value': 'Days', 'department': 'Department', 'variable': 'Leave Type'},
                     color_discrete_map={'avg_used_leaves': COLORSCHEME['primary'], 
                                         'avg_remaining_leaves': COLORSCHEME['secondary']})
        fig.update_layout(barmode='stack')
        st.plotly_chart(fig)
    else:
        st.write("No leave utilization data available.")

def show_top_leave_reasons():
    st.subheader("Top Reasons for Leave")
    conn = get_db_connection()
    if conn is None:
        st.error("Unable to connect to the database. Please try again later.")
        return

    df = pd.read_sql_query("""
        SELECT leave_type, COUNT(*) as count
        FROM leaves
        GROUP BY leave_type
        ORDER BY count DESC
        LIMIT 5
    """, conn)
    conn.close()

    if not df.empty:
        fig = px.pie(df, values='count', names='leave_type', title="Top 5 Reasons for Leave")
        st.plotly_chart(fig)
    else:
        st.write("No leave reason data available.")

def show_leave_trends():
    st.subheader("Leave Trends")
    conn = get_db_connection()
    if conn is None:
        st.error("Unable to connect to the database. Please try again later.")
        return

    df = pd.read_sql_query("""
        SELECT strftime('%Y-%m', start_date) as month, COUNT(*) as count
        FROM leaves
        GROUP BY month
        ORDER BY month
    """, conn)
    conn.close()

    if not df.empty:
        df['month'] = pd.to_datetime(df['month'])
        fig = px.line(df, x='month', y='count', title="Leave Trends Over Time")
        st.plotly_chart(fig)
    else:
        st.write("No leave trend data available.")

def manage_leaves():
    st.header("Manage Leaves")
    conn = get_db_connection()
    if conn is None:
        st.error("Unable to connect to the database. Please try again later.")
        return

    df = pd.read_sql_query("""
        SELECT leaves.*, users.username, users.department 
        FROM leaves 
        JOIN users ON leaves.user_id = users.id 
        WHERE leaves.status = 'pending'
    """, conn)
    conn.close()

    if not df.empty:
        for _, leave in df.iterrows():
            with st.expander(f"{leave['username']} - {leave['start_date']} to {leave['end_date']}"):
                st.write(f"Department: {leave['department']}")
                st.write(f"Leave Type: {leave['leave_type']}")
                st.write(f"Reason: {leave['reason']}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Approve", key=f"approve_{leave['id']}", type="primary"):
                        if update_leave_status(leave['id'], 'approved'):
                            st.success("Leave approved!")
                            st.rerun()
                        else:
                            st.error("Failed to approve leave. Please try again.")
                with col2:
                    if st.button("Reject", key=f"reject_{leave['id']}", type="secondary"):
                        if update_leave_status(leave['id'], 'rejected'):
                            st.success("Leave rejected!")
                            st.rerun()
                        else:
                            st.error("Failed to reject leave. Please try again.")
    else:
        st.info("No pending leaves.")

def update_leave_status(leave_id, status):
    conn = get_db_connection()
    if conn is None:
        return False

    try:
        cur = conn.cursor()
        cur.execute('UPDATE leaves SET status = ? WHERE id = ?', (status, leave_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating leave status: {e}")
        return False
    finally:
        conn.close()

def create_user():
    st.header("Create New User")
    with st.form("create_user_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        department = st.selectbox("Department", ["HR", "IT", "Finance", "Marketing", "Operations"])
        is_admin = st.checkbox("Is Admin")
        submitted = st.form_submit_button("Create User")

        if submitted:
            if username and password and department:
                if add_user(username, password, department, is_admin):
                    st.success("User created successfully!")
                else:
                    st.error("Error creating user. Please try again.")
            else:
                st.error("Please fill in all fields.")

def user_management():
    st.header("User Management")
    
    # Display all users
    users_df = get_all_users()
    if users_df is not None:
        st.dataframe(users_df)
    else:
        st.error("Unable to fetch user data. Please try again later.")
        return

    user_id = st.number_input("Enter user ID to update", min_value=1, step=1)
    if st.button("Load User Data"):
        update_user(user_id)

def update_user(user_id):
    conn = get_db_connection()
    if conn is None:
        st.error("Unable to connect to the database. Please try again later.")
        return

    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cur.fetchone()
        if user:
            with st.form("update_user_form"):
                username = st.text_input("Username", value=user['username'])
                department = st.selectbox("Department", 
                                          ["HR", "IT", "Finance", "Marketing", "Operations"], 
                                          index=["HR", "IT", "Finance", "Marketing", "Operations"].index(user['department']))
                is_admin = st.checkbox("Is Admin", value=user['is_admin'])
                remaining_leaves = st.number_input("Remaining Leaves", value=user['remaining_leaves'], min_value=0, max_value=30)
                
                adjust_leaves = st.number_input("Adjust Leaves", value=0, min_value=-30, max_value=30, 
                                                help="Positive value to add leaves, negative to deduct")
                adjustment_reason = st.text_input("Adjustment Reason")
                
                submitted = st.form_submit_button("Update User")

                if submitted:
                    new_remaining_leaves = remaining_leaves + adjust_leaves
                    success = update_user_data(user_id, username, department, is_admin, new_remaining_leaves, adjust_leaves, adjustment_reason)
                    
                    if success:
                        st.success("User updated successfully!")
                        # Clear cache and refresh the user table
                        st.cache_data.clear()
                        updated_df = get_all_users()
                        if updated_df is not None:
                            st.dataframe(updated_df)
                        else:
                            st.error("Unable to fetch updated user data. Please refresh the page.")
                    else:
                        st.error("Failed to update user. Please try again.")
        else:
            st.error("User not found")
    except Exception as e:
        st.error(f"An error occurred while fetching user data: {e}")
    finally:
        conn.close()

