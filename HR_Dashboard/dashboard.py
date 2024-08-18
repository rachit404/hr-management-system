import streamlit as st
import google.generativeai as genai
import PyPDF2 as pdf
import requests
from dotenv import load_dotenv
import os
import subprocess

st.set_page_config(page_title="HR Dashboard",layout="wide")
load_dotenv()

with st.sidebar:
    st.title("Hi, HR!")
    page = st.selectbox("",("Home", "ChatBot Assistant", "Interview Scheduling", "Analytics Dashboard", "Leave Management"),label_visibility = "collapsed",)
    
if page == "Home":
    st.header("Welcome to the HR Dashboard!")
    st.subheader("✨ Dashboard Overview ✨")
    st.markdown(
        """
        Welcome to our comprehensive HR Dashboard, your one-stop solution for managing all HR-related tasks efficiently. 
        Explore the features designed to streamline your workflow:
        """
    )
    
    features = {
        "🤖 ChatBot Assistant": "Leverage our AI-powered chatbot to assist with HR queries, provide detailed responses, and enhance decision-making.",
        "📄 Resume Screener": "Automate the resume screening process. Upload resumes and let our AI analyze them against job descriptions, saving you time and effort.",
        "📊 Analytics Dashboard": "Gain insights into key HR metrics with our interactive analytics dashboard. Visualize data, track performance, and make informed decisions.",
        "🗓️ Interview Scheduling": "Simplify the interview scheduling process. Our system integrates with calendars and sends automated reminders to candidates and interviewers.",
        "🏖️ Leave Management": "Manage employee leave requests seamlessly. Track leave balances, approve requests, and maintain accurate records."
    }

    for feature, description in features.items():
        st.subheader(feature)
        st.markdown(description)
    
elif page == "ChatBot Assistant":
    OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
    OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    def generate_text(prompt, max_tokens=1000, temperature=0.8, top_p=0.9):
        headers = {
            "Content-Type": "application/json",
            "api-key": OPENAI_KEY
        }
        data = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant. Please provide detailed and comprehensive responses."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stop": None
        }
        try:
            with st.spinner("Generating detailed response..."):
                response = requests.post(f"{OPENAI_ENDPOINT}/openai/deployments/ChatbotCC/chat/completions?api-version=2023-05-15", headers=headers, json=data)
                response.raise_for_status()
                result = response.json()
                return result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            st.error(f"Error: {e}")
            if response.status_code == 404:
                st.error("Deployment not found. Please check your deployment name and try again.")
            else:
                st.error(f"Detailed error: {response.text}")
            return None

    # Main content for OpenAI service
    st.header("AI Chatbot Assistant")

    if 'generated_text' not in st.session_state:
        st.session_state.generated_text = ""
    if 'prompt' not in st.session_state:
        st.session_state.prompt = ""

    st.info("This chatbot is designed to provide detailed and comprehensive responses. Feel free to ask complex questions!")

    st.session_state.prompt = st.text_area("Enter your question or prompt (the more specific, the better):", height=150)

    col1, col2, col3 = st.columns(3)
    with col1:
        max_tokens = st.slider("Response Length", min_value=100, max_value=2000, value=1000, step=100, help="Higher values allow for longer responses")
    with col2:
        temperature = st.slider("Creativity", min_value=0.5, max_value=1.0, value=0.8, step=0.1, help="Higher values increase response creativity")
    with col3:
        top_p = st.slider("Focus", min_value=0.1, max_value=1.0, value=0.9, step=0.1, help="Lower values make responses more focused")

    if st.button("Generate Response") and st.session_state.prompt.strip():
        st.session_state.generated_text = generate_text(st.session_state.prompt, max_tokens, temperature, top_p)
        if st.session_state.generated_text:
            st.subheader("Generated Response:")
            st.write(st.session_state.generated_text)

            # Check if response is too short and offer to expand
            if len(st.session_state.generated_text.split()) < 50:  # Arbitrary threshold
                if st.button("The response seems brief. Would you like me to expand on it?"):
                    expansion_prompt = f"Please provide a more detailed explanation of the following: {st.session_state.generated_text}"
                    expanded_response = generate_text(expansion_prompt, max_tokens, temperature, top_p)
                    if expanded_response:
                        st.subheader("Expanded Response:")
                        st.write(expanded_response)

    st.markdown("---")
    st.caption("This chatbot uses Azure OpenAI services to generate responses. The quality and length of responses may vary based on the input and settings.")

elif page == "Interview Scheduling":
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    def get_ai_response(prompt, pdf_text, job_desc):
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(f"{prompt}\n\nJob Description: {job_desc}\n\nResume: {pdf_text}")
        return response.text

    def extract_pdf_text(uploaded_file):
        reader = pdf.PdfReader(uploaded_file)
        return "".join(page.extract_text() for page in reader.pages)

    # Custom CSS
    st.markdown("""
    <style>
        :root {
            --background-color-light: #f8f9fa;
            --background-color-dark: #343a40;
            --text-color-light: #212529;
            --text-color-dark: #f8f9fa;
            --card-background-light: #ffffff;
            --card-background-dark: #495057;
            --card-border-light: #e9ecef;
            --card-border-dark: #343a40;
            --primary-color-light: #007bff;
            --primary-color-dark: #1a73e8;
            --primary-hover-light: #0056b3;
            --primary-hover-dark: #1558b5;
        }

        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        * {
            font-family: 'Inter', sans-serif;
        }
        
        .main {
            background-color: var(--background-color-light);
            color: var(--text-color-light);
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--text-color-light);
        }

        .stButton>button {
            background-color: var(--primary-color-light);
            color: white;
            border: none;
            border-radius: 4px;
            padding: 10px 20px;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .stButton>button:hover {
            background-color: var(--primary-hover-light);
        }

        .stTextArea>div>div>textarea, .stFileUploader {
            background-color: white;
            border: 1px solid var(--card-border-light);
            border-radius: 4px;
        }

        .card {
            background-color: var(--card-background-light);
            border: 1px solid var(--card-border-light);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }

        .result-card {
            background-color: var(--card-background-light);
            border-left: 5px solid #28a745;
            margin-top: 20px;
        }

        .analysis-sidebar {
            background-color: var(--background-color-light);
            border-right: 1px solid var(--card-border-light);
            padding: 20px;
            height: 100%;
        }

        .result-content {
            max-height: 500px;
            overflow-y: auto;
            padding: 10px;
        }

        .st-cc {
            background-color: var(--card-border-light);
            border-radius: 4px;
            padding: 2px 6px;
            margin-bottom: 5px;
        }

        .stProgress > div > div > div {
            background-color: #28a745;
        }

        @media (prefers-color-scheme: dark) {
            .main {
                background-color: var(--background-color-dark);
                color: var(--text-color-dark);
            }

            h1, h2, h3, h4, h5, h6 {
                color: var(--text-color-dark);
            }

            .stButton>button {
                background-color: var(--primary-color-dark);
            }

            .stButton>button:hover {
                background-color: var(--primary-hover-dark);
            }

            .stTextArea>div>div>textarea, .stFileUploader {
                background-color: var(--card-background-dark);
                border: 1px solid var(--card-border-dark);
            }

            .card {
                background-color: var(--card-background-dark);
                border: 1px solid var(--card-border-dark);
                box-shadow: 0 2px 5px rgba(255,255,255,0.05);
            }

            .result-card {
                background-color: var(--card-background-dark);
            }

            .analysis-sidebar {
                background-color: var(--background-color-dark);
                border-right: 1px solid var(--card-border-dark);
            }

            .st-cc {
                background-color: var(--card-border-dark);
            }
        }
    </style>
    """, unsafe_allow_html=True)

    def main():
        tab1, tab2, tab3 = st.tabs(["📄 Input", "🔍 Analysis", "ℹ️ How It Works"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                <div class="card">
                    <h3>Job Description</h3>
                    <p>Enter the job description you're applying for:</p>
                </div>
                """, unsafe_allow_html=True)
                job_description = st.text_area("", height=200, key="job_desc")
                if job_description:
                    st.session_state.job_description = job_description

            with col2:
                st.markdown("""
                <div class="card">
                    <h3>Upload Resume</h3>
                    <p>Upload your resume in PDF format:</p>
                </div>
                """, unsafe_allow_html=True)
                uploaded_file = st.file_uploader("", type="pdf", key="resume")
                if uploaded_file:
                    st.success("Resume uploaded successfully!")
                    st.session_state.uploaded_file = uploaded_file

        with tab2:
            st.markdown("""
            <div class="card">
                <h3>Resume Analysis Dashboard</h3>
                <p>Select an analysis type and view detailed insights about your resume.</p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.markdown("""
                <div class="analysis-sidebar">
                    <h4>Analysis Options</h4>
                </div>
                """, unsafe_allow_html=True)
                analysis_type = st.radio("", ["Resume Analysis", "Skill Gap Analysis", "Match Percentage"], key="analysis_type")
                
                if st.button("Run Analysis", key="run_analysis"):
                    if 'uploaded_file' not in st.session_state or 'job_description' not in st.session_state:
                        st.error("Please upload your resume and enter a job description in the Input tab.")
                    else:
                        st.session_state.analysis_run = True

            with col2:
                if 'analysis_run' in st.session_state and st.session_state.analysis_run:
                    with st.spinner("Analyzing your resume..."):
                        pdf_text = extract_pdf_text(st.session_state.uploaded_file)
                        prompt = get_prompt(analysis_type)
                        response = get_ai_response(prompt, pdf_text, st.session_state.job_description)
                        display_results(analysis_type, response)
                else:
                    st.info("Select an analysis type and click 'Run Analysis' to get started.")

        with tab3:
            st.markdown("""
            <div class="card">
                <h3>How ResumeMaster AI Works</h3>
                <p>Our advanced AI system analyzes your resume against the job description to provide valuable insights:</p>
                <ul>
                    <li><strong>Resume Analysis:</strong> Get a detailed evaluation of your resume's strengths and areas for improvement.</li>
                    <li><strong>Skill Gap Analysis:</strong> Identify missing skills and receive personalized recommendations for enhancement.</li>
                    <li><strong>Match Percentage:</strong> Obtain a quantitative assessment of how well your resume aligns with the job requirements.</li>
                </ul>
                <p>To get started, simply upload your resume and paste the job description in the Input tab, then choose your analysis type and run the analysis!</p>
            </div>
            """, unsafe_allow_html=True)

    def get_prompt(analysis_type):
        prompts = {
            "Resume Analysis": "Analyze the resume against the job description. Provide a professional assessment of the candidate's alignment with the role, highlighting strengths and areas for improvement. Format your response with clear headings and bullet points for easy readability.",
            "Skill Gap Analysis": "Identify skill gaps between the resume and job description. Offer specific, actionable recommendations for skill enhancement and professional development. Use a table format to display skills: Required Skills | Current Level | Recommended Action",
            "Match Percentage": "Calculate the match percentage between the resume and job description. Provide: 1) Overall match percentage, 2) Key matching skills, 3) Missing key skills, 4) Recommendations for improvement. Use charts or percentages where appropriate."
        }
        return prompts[analysis_type]

    def display_results(analysis_type, response):
        st.markdown(f"""
        <div class="card result-card">
            <h3>{analysis_type} Results</h3>
            <div class="result-content">
                {response}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if analysis_type == "Match Percentage":
            # Example of adding a visual element (This is a placeholder, you'd need to extract the actual percentage from the AI response)
            match_percentage = 75  # This should be extracted from the AI response
            st.progress(match_percentage / 100)
            # st.write(f"Overall Match: {match_percentage}%")

    if __name__ == "__main__":
        main()

    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #6c757d;'>© 2024 ResumeMaster AI. All rights reserved.</div>", unsafe_allow_html=True)

elif page == "Analytics Dashboard":
    st.header("Analytics Dashboard")
    power_bi_embed_url = "https://app.powerbi.com/view?r=eyJrIjoiYWM5YzA1ZGQtOWZhMS00NmJjLTkyMGUtZTRjODg4MGFiZTE2IiwidCI6ImQxZjE0MzQ4LWYxYjUtNGEwOS1hYzk5LTdlYmYyMTNjYmM4MSIsImMiOjEwfQ%3D%3D"
    st.write(
        f'<iframe title="CCAnalysis" width="800" height="475" src="https://app.powerbi.com/view?r=eyJrIjoiYWM5YzA1ZGQtOWZhMS00NmJjLTkyMGUtZTRjODg4MGFiZTE2IiwidCI6ImQxZjE0MzQ4LWYxYjUtNGEwOS1hYzk5LTdlYmYyMTNjYmM4MSIsImMiOjEwfQ%3D%3D" frameborder="0" allowFullScreen="true"></iframe>',
        unsafe_allow_html=True,
    )

elif page == "Leave Management":
    # Create a styled button-like link using HTML and CSS
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

        <a href="https://leave-app.streamlit.app/" class="button" target="_blank">Leave Management</a>
        """, unsafe_allow_html=True)
