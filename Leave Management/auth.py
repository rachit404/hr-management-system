import streamlit as st
from database import get_db_connection
from config import ADMIN_USERNAME, ADMIN_PASSWORD, COLORSCHEME

def login(username, password):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return True, True
    
    conn = get_db_connection()
    if conn is None:
        st.error("Unable to connect to the database. Please try again later.")
        return False, False

    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cur.fetchone()
        if user:
            return True, user['is_admin']
        return False, False
    except Exception as e:
        st.error(f"An error occurred during login: {e}")
        return False, False
    finally:
        conn.close()

def login_page():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {COLORSCHEME['background']};
            color: {COLORSCHEME['text']};
        }}
        .stButton>button {{
            color: white;
            background-color: {COLORSCHEME['primary']};
            border-radius: 5px;
        }}
        .stTextInput>div>div>input {{
            border-radius: 5px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("Leave Management System")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown(
            f"""
            <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h2 style="text-align: center; color: {COLORSCHEME['primary']};">Login</h2>
            """,
            unsafe_allow_html=True
        )
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", key="login_button"):
            is_authenticated, is_admin = login(username, password)
            if is_authenticated:
                st.session_state.is_authenticated = True
                st.session_state.is_admin = is_admin
                st.session_state.username = username
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password")
        
        st.markdown("</div>", unsafe_allow_html=True)

def logout():
    for key in ['is_authenticated', 'is_admin', 'username']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()