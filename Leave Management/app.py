import streamlit as st
from auth import login_page, logout
from admin import admin_dashboard
from user import user_dashboard
from database import init_db
from config import COLORSCHEME

def main():
    init_db()  # Initialize the database
    st.set_page_config(page_title="Leave Management")
    # Custom CSS
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

    st.sidebar.title("Navigation")

    # Initialize session state variables
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    if 'username' not in st.session_state:
        st.session_state.username = None

    if st.session_state.is_authenticated:
        if st.sidebar.button("Logout"):
            logout()
            st.rerun()

        if st.session_state.is_admin:
            admin_dashboard()
        elif st.session_state.username:
            user_dashboard(st.session_state.username)
        else:
            st.error("Session error. Please log in again.")
            logout()
            st.rerun()
    else:
        login_page()

if __name__ == "__main__":
    main()