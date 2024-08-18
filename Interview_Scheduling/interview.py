import streamlit as st
from datetime import datetime, timedelta
from hr_database import add_interview, get_interviews, delete_interview, delete_all_interviews, table_creation
import plotly.express as px
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Initialize session state


def refresh_data():
    st.session_state.interviews = get_interviews()


def send_sms_via_email(to_email, body, from_email, from_password):
    smtp_server = 'smtp.gmail.com'  # Change this to your email provider's SMTP server
    smtp_port = 587  # Change this to your email provider's SMTP port

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = "Interview Notification"

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, from_password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        print(f"SMS sent to {to_email}")
    except Exception as e:
        print(f"Failed to send SMS: {e}")


def interview_scheduling():
    st.set_page_config(page_title="Interview Scheduler", page_icon=":calendar:", layout="wide")
    st.title("📅 Interview Scheduling System")
    table_creation()
    if 'interviews' not in st.session_state:
        st.session_state.interviews = get_interviews()
    
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(to right, #6a11cb, #2575fc);
        color: white;
    }
    .title h1 {
        font-size: 3rem;
        text-align: center;
    }
    .stButton button {
        background-color: #4CAF50; 
        color: white;
        border: none;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
        transition: 0.3s;
    }
    .stButton button:hover {
        background-color: #45a049;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.header("Schedule a New Interview")
        candidate_name = st.text_input("Candidate Name", placeholder="Enter candidate name here...")
        interview_date = st.date_input("Interview Date", min_value=datetime.now().date())

        # Time input in HH:MM format
        interview_time = st.text_input("Interview Time (HH:MM)", placeholder="Enter time in HH:MM format", value="09:00")
        interview_duration = st.number_input("Duration (minutes)", min_value=15, max_value=240, step=15, value=60)

        if st.button("Schedule Interview"):
            try:
                interview_datetime = datetime.combine(interview_date, datetime.strptime(interview_time, "%H:%M").time())
                add_interview(candidate_name, interview_datetime.strftime("%Y-%m-%d %H:%M"))
                st.success(f"Interview scheduled for {candidate_name} on {interview_datetime.strftime('%Y-%m-%d %H:%M')} for {interview_duration} minutes")
                refresh_data()  # Update the session state with new data
            except ValueError:
                st.error("Invalid time format. Please enter time as HH:MM.")

    with col2:
        st.header("Interview Process")
        st.markdown("""
        1. 📄 *Resume selection*
        2. ☎ *Initial screening*
        3. 💻 *Technical interview*
        4. 🗣 *HR interview*
        5. ✅ *Final decision*
        """)
        
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Build the absolute path to the image
        image_path = os.path.join(current_dir, "your_image.jpg")
        # Check if the image file exists and display it
        if os.path.exists(image_path):
            st.image(image_path, caption="AI-generated interview process visualization")
        else:
            st.error(f"Image file not found at {image_path}. Please check the file path.")

    # Display and manage interviews
    st.header("Scheduled Interviews")
    if st.session_state.interviews.empty:
        st.write("No interviews scheduled yet.")
    else:
        interviews = st.session_state.interviews
        interviews['interview_end'] = pd.to_datetime(interviews['interview_date']) + timedelta(minutes=60)
        st.dataframe(interviews)
        fig = px.timeline(interviews, x_start='interview_date', x_end='interview_end', y='candidate_name', title='Interview Schedule')
        st.plotly_chart(fig)

        st.header("Manage Scheduled Interviews")
        for index, row in interviews.iterrows():
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**Candidate:** {row['candidate_name']}")
            with col2:
                st.write(f"**Scheduled on:** {row['interview_date']}")
            with col3:
                if st.button(f"Notify {row['candidate_name']}", key=row['id']):
                    st.success(f"Notified {row['candidate_name']} about their interview on {row['interview_date']}")

        col4, col5 = st.columns([3, 1])
        with col4:
            interview_id = st.text_input("Enter Interview ID to Remove", placeholder="Interview ID")
        with col5:
            if st.button("Remove Interview"):
                if interview_id:
                    delete_interview(int(interview_id))
                    st.success("Interview removed successfully!")
                    refresh_data()  # Update the session state with new data
                else:
                    st.error("Please enter a valid interview ID.")

        if st.button("Remove All Interviews"):
            delete_all_interviews()
            st.success("All interviews removed successfully!")
            st.session_state.interviews = pd.DataFrame()  # Clear the interviews DataFrame

if __name__ == "__main__":
    interview_scheduling()
