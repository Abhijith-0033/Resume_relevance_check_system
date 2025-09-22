import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import hashlib
import io
import base64
from pathlib import Path
import tempfile
import os
import google.generativeai as genai
import os
import json
from typing import Dict, List, Optional
import re
from collections import Counter
from datetime import datetime
import sqlite3
import requests
from pathlib import Path
import traceback
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.chunk import ne_chunk
from nltk.tag import pos_tag
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import textstat
import time
from datetime import datetime
from typing import Dict, List, Any
import logging
# Download required NLTK data
nltk.download('punkt')   # Sentence tokenizer
nltk.download('punkt_tab')

try:
    import fitz
except ModuleNotFoundError:
    print("PyMuPDF is not installed. Run: pip install PyMuPDF")

# Import your backend system
try:
    from main1 import ResumeRelevanceSystem
    BACKEND_AVAILABLE = True
except ImportError:
    st.error("Backend system not found. Please ensure resume_relevance_system.py is in the same directory.")
    BACKEND_AVAILABLE = False

# Set up logging for better debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Database configuration
# Google Drive file ID
FILE_ID = "1AGJ3hQxIl6w9i1OKnbzhkdo22nnTvYCz"
# Local file path where DB will be saved
DATABASE_PATH = Path("db.sqlite")

# Direct download link
DOWNLOAD_URL = f"https://drive.google.com/uc?id={FILE_ID}"

# Download DB if it doesn't exist locally
if not DATABASE_PATH.exists():
    print("Downloading database...")
    r = requests.get(DOWNLOAD_URL, allow_redirects=True)
    with open(DATABASE_PATH, "wb") as f:
        f.write(r.content)
    print("Database downloaded.")

# Connect to the local DB
def get_db_connection():
    return sqlite3.connect(DATABASE_PATH)

# Page configuration
st.set_page_config(
    page_title="Resume Relevance Check System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS for professional styling
st.markdown("""
<style>
    /* Main styling */
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1e40af, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -0.05em;
    }
    
    .sub-header {
        font-size: 1.25rem;
        color: #64748b;
        text-align: center;
        margin-bottom: 3rem;
        font-weight: 300;
    }
    
    /* Login page styling */
    .login-container {
        background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
        padding: 3rem 2rem;
        border-radius: 1rem;
        box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);
        border: 1px solid rgba(59, 130, 246, 0.1);
    }
    
    .role-button {
        background: linear-gradient(135deg, #1e40af, #3b82f6);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 0.75rem;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;
        font-weight: 600;
        font-size: 1.1rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    
    .role-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #1e40af, #1e3a8a);
    }
    
    .css-1d391kg .css-1544g2n {
        color: white;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 2rem;
        border-radius: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        border-left: 5px solid #10b981;
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    
    /* Verdict badges */
    .verdict-high {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.875rem;
        display: inline-block;
    }
    
    .verdict-medium {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.875rem;
        display: inline-block;
    }
    
    .verdict-low {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.875rem;
        display: inline-block;
    }
    
    /* Upload area */
    .upload-area {
        border: 2px dashed #cbd5e1;
        border-radius: 1rem;
        padding: 3rem;
        text-align: center;
        background: linear-gradient(135deg, #f8fafc, #f1f5f9);
        transition: all 0.3s ease;
    }
    
    .upload-area:hover {
        border-color: #3b82f6;
        background: linear-gradient(135deg, #eff6ff, #dbeafe);
    }
    
    /* Cards */
    .job-card {
        background: white;
        padding: 2rem;
        border-radius: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .job-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        border-color: #3b82f6;
    }
    
    /* Success/Error messages */
    .success-message {
        background: linear-gradient(135deg, #d1fae5, #a7f3d0);
        color: #065f46;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #10b981;
        margin: 1rem 0;
    }
    
    .error-message {
        background: linear-gradient(135deg, #fee2e2, #fecaca);
        color: #991b1b;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ef4444;
        margin: 1rem 0;
    }
    
    /* Form styling */
    .stTextInput > div > div > input {
        border-radius: 0.5rem;
        border: 2px solid #e2e8f0;
        padding: 0.75rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #1e40af, #3b82f6);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    
    /* Progress bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #1e40af, #3b82f6);
        border-radius: 9999px;
    }
</style>
""", unsafe_allow_html=True)

def character_selection_page():
    """Character selection page - first screen"""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 4rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 3rem;
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.3);
    ">
        <h1 style="
            font-size: 4rem;
            font-weight: 900;
            color: white;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            letter-spacing: -2px;
        ">Resume Relevance System</h1>
        <p style="
            font-size: 1.6rem;
            color: rgba(255, 255, 255, 0.9);
            margin: 1rem 0 0 0;
            font-weight: 300;
        ">AI-Powered Career Matching Platform</p>
        <div style="
            width: 60px;
            height: 4px;
            background: linear-gradient(90deg, #ffd89b, #19547b);
            margin: 2rem auto 0;
            border-radius: 2px;
        "></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <h2 style="
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 3rem 0 2rem 0;
    ">Choose Your Role</h2>
    """, unsafe_allow_html=True)

    # Create two columns for character selection
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Student and Placement Cell selection cards
        col_student, col_placement = st.columns(2, gap="large")
        
        with col_student:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
                padding: 3rem 2rem;
                border-radius: 25px;
                text-align: center;
                box-shadow: 0 20px 40px rgba(168, 237, 234, 0.4);
                transition: all 0.3s ease;
                cursor: pointer;
                border: 3px solid transparent;
                height: 400px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            " onmouseover="this.style.transform='translateY(-10px)'; this.style.borderColor='#667eea'" 
               onmouseout="this.style.transform='translateY(0px)'; this.style.borderColor='transparent'">
                <div style="
                    width: 120px;
                    height: 120px;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 2rem;
                    font-size: 4rem;
                    box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
                ">👨‍🎓</div>
                <h2 style="
                    color: #2c3e50;
                    margin: 0 0 1rem 0;
                    font-weight: 800;
                    font-size: 2rem;
                ">Student</h2>
                <p style="
                    color: #34495e;
                    margin: 0;
                    line-height: 1.6;
                    font-size: 1.1rem;
                ">Upload your resume, find job opportunities, and get AI-powered matching analysis</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Select Student", key="select_student", use_container_width=True, type="primary"):
                st.session_state.selected_role = "student"
                st.rerun()
        
        with col_placement:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%);
                padding: 3rem 2rem;
                border-radius: 25px;
                text-align: center;
                box-shadow: 0 20px 40px rgba(255, 216, 155, 0.4);
                transition: all 0.3s ease;
                cursor: pointer;
                border: 3px solid transparent;
                height: 400px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            " onmouseover="this.style.transform='translateY(-10px)'; this.style.borderColor='#667eea'" 
               onmouseout="this.style.transform='translateY(0px)'; this.style.borderColor='transparent'">
                <div style="
                    width: 120px;
                    height: 120px;
                    background: linear-gradient(135deg, #ff6b6b, #ffa726);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 2rem;
                    font-size: 4rem;
                    box-shadow: 0 10px 25px rgba(255, 107, 107, 0.3);
                ">🏢</div>
                <h2 style="
                    color: white;
                    margin: 0 0 1rem 0;
                    font-weight: 800;
                    font-size: 2rem;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                ">Placement Cell</h2>
                <p style="
                    color: rgba(255, 255, 255, 0.95);
                    margin: 0;
                    line-height: 1.6;
                    font-size: 1.1rem;
                ">Manage student resumes, job descriptions, and run batch evaluations</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Select Placement Cell", key="select_placement", use_container_width=True, type="secondary"):
                st.session_state.selected_role = "placement"
                st.rerun()

# Database helper functions
def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DATABASE_PATH)

def hash_password(password):
    """Hash password for security"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password, user_type):
    """Authenticate user against database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hashed_password = hash_password(password)
    
    if user_type == "student":
        cursor.execute("SELECT student_id FROM Students WHERE username = ? AND password = ?", 
                      (username, hashed_password))
        user = cursor.fetchone()
        user_id = user[0] if user else None
    else:
        cursor.execute("SELECT placement_id FROM PlacementUsers WHERE username = ? AND password = ?", 
                      (username, hashed_password))
        user = cursor.fetchone()
        user_id = user[0] if user else None
    
    conn.close()
    return user_id

def register_user(username, password, user_type):
    """Register new user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hashed_password = hash_password(password)
    
    try:
        if user_type == "student":
            cursor.execute("INSERT INTO Students (username, password) VALUES (?, ?)",
                          (username, hashed_password))
        else:
            cursor.execute("INSERT INTO PlacementUsers (username, password) VALUES (?, ?)",
                          (username, hashed_password))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def save_resume_to_db(student_id, name, email, file_content):
    """Save resume to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO Resumes (student_id, name, email, resume_file) 
        VALUES (?, ?, ?, ?)
    """, (student_id, name, email, file_content))
    
    resume_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return resume_id

def save_job_to_db(placement_id, company_name, job_title, file_content):
    """Save job description to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO JobDescriptions (placement_id, company_name, job_title, description_file) 
        VALUES (?, ?, ?, ?)
    """, (placement_id, company_name, job_title, file_content))
    
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return job_id

def get_user_resumes(student_id=None):
    """Get resumes from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if student_id:
        cursor.execute("""
            SELECT resume_id, name, email, uploaded_at 
            FROM Resumes WHERE student_id = ?
            ORDER BY uploaded_at DESC
        """, (student_id,))
    else:
        cursor.execute("""
            SELECT r.resume_id, r.name, r.email, r.uploaded_at, s.username
            FROM Resumes r
            JOIN Students s ON r.student_id = s.student_id
            ORDER BY r.uploaded_at DESC
        """)
    
    resumes = cursor.fetchall()
    conn.close()
    return resumes

def get_job_descriptions(placement_id=None):
    """Get job descriptions from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if placement_id:
        cursor.execute("""
            SELECT job_id, company_name, job_title, uploaded_at 
            FROM JobDescriptions WHERE placement_id = ?
            ORDER BY uploaded_at DESC
        """, (placement_id,))
    else:
        cursor.execute("""
            SELECT job_id, company_name, job_title, uploaded_at
            FROM JobDescriptions
            ORDER BY uploaded_at DESC
        """)
    
    jobs = cursor.fetchall()
    conn.close()
    return jobs

def get_file_from_db(file_id, file_type):
    """Get file content from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if file_type == "resume":
        cursor.execute("SELECT resume_file FROM Resumes WHERE resume_id = ?", (file_id,))
    else:
        cursor.execute("SELECT description_file FROM JobDescriptions WHERE job_id = ?", (file_id,))
    
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'page' not in st.session_state:
        st.session_state.page = "Dashboard"
    if 'selected_role' not in st.session_state:  # ADD THIS LINE
        st.session_state.selected_role = None

# Initialize system
@st.cache_resource
def init_backend_system():
    """Initialize the resume relevance system"""
    if BACKEND_AVAILABLE:
        return ResumeRelevanceSystem()
    return None

def login_page():
    """Login page after role selection"""
    role_display = "Student" if st.session_state.selected_role == "student" else "Placement Cell"
    role_color = "#a8edea" if st.session_state.selected_role == "student" else "#ffd89b"
    
    # Header with selected role
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {role_color}, #667eea);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
    ">
        <h1 style="
            font-size: 3rem;
            font-weight: 900;
            color: white;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        ">Resume Relevance System</h1>
        <p style="
            font-size: 1.4rem;
            color: rgba(255, 255, 255, 0.9);
            margin: 1rem 0 0 0;
        ">{role_display} Portal</p>
    </div>
    """, unsafe_allow_html=True)

    # Back button
    if st.button("← Back to Role Selection", key="back_to_roles"):
        st.session_state.selected_role = None
        st.rerun()

    st.markdown('<div style="max-width: 800px; margin: 0 auto;">', unsafe_allow_html=True)
    
    # Create tabs for login and register
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        st.markdown(f"<h3 style='text-align: center; color: #2c3e50;'>Login as {role_display}</h3>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                login_button = st.form_submit_button(f"Login as {role_display}", use_container_width=True, type="primary")
                
                if login_button:
                    if username and password:
                        user_id = authenticate_user(username, password, st.session_state.selected_role)
                        if user_id:
                            st.session_state.authenticated = True
                            st.session_state.user_role = st.session_state.selected_role
                            st.session_state.user_id = user_id
                            st.session_state.username = username
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
                    else:
                        st.warning("Please fill in all fields")
    
    with tab2:
        st.markdown(f"<h3 style='text-align: center; color: #2c3e50;'>Register as {role_display}</h3>", unsafe_allow_html=True)
        
        with st.form("register_form"):
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                reg_username = st.text_input("Choose Username", placeholder="Choose a unique username")
                reg_password = st.text_input("Choose Password", type="password", placeholder="Choose a strong password")
                reg_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                
                register_button = st.form_submit_button(f"Register as {role_display}", use_container_width=True, type="secondary")
                
                if register_button:
                    if reg_username and reg_password and reg_confirm:
                        if reg_password == reg_confirm:
                            if register_user(reg_username, reg_password, st.session_state.selected_role):
                                st.success("Registration successful! Please login.")
                            else:
                                st.error("Username already exists")
                        else:
                            st.error("Passwords don't match")
                    else:
                        st.warning("Please fill in all fields")
    
    st.markdown('</div>', unsafe_allow_html=True)

def sidebar_navigation():
    """Enhanced sidebar navigation with system name and user info"""
    with st.sidebar:
        # System name styled at top
        st.markdown("""
        <div style="
            font-size: 2rem; 
            font-weight: 900; 
            background: linear-gradient(135deg, #1e40af, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            padding: 1rem 0;
            margin-bottom: 1rem;
            letter-spacing: -0.05em;
            user-select: none;
        ">
            Resume Relevance System
        </div>
        """, unsafe_allow_html=True)

        # User info header
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e40af, #3b82f6); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; text-align: center;">
            <h3 style="color: white; margin: 0;">Welcome!</h3>
            <p style="color: #e0f2fe; margin: 0; font-weight: 600;">{st.session_state.username}</p>
            <p style="color: #a5f3fc; margin: 0; font-size: 0.85rem; font-weight: 400;">{st.session_state.user_role.title()}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation menu - REMOVED "My Results" from student menu
        if st.session_state.user_role == "student":
            menu_items = [
                ("🏠", "Dashboard"),
                ("📄", "Upload Resume"),
                ("💼", "View Jobs"),
                ("🔍", "Individual Analysis"),
                ("📊", "Batch Analysis")
                # REMOVED: ("📈", "My Results")
            ]
        else:
            menu_items = [
                ("🏠", "Dashboard"),
                ("📚", "Manage Resumes"),
                ("💼", "Manage Jobs"),
                ("🔍", "Individual Evaluation"),
                ("📊", "Batch Evaluation"),
                ("📈", "System Statistics")
            ]
        
        selected_page = st.radio(
            "Navigation",
            options=[item[1] for item in menu_items],
            format_func=lambda x: f"{[item[0] for item in menu_items if item[1] == x][0]} {x}",
            key="navigation"
        )
        
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        return selected_page

def dashboard_page():
    """Enhanced professional dashboard with colorful design and core functions"""
    
    # Hero Section with System Name and Branding
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 4rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 3rem;
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute;
            top: -50px;
            right: -50px;
            width: 200px;
            height: 200px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 50%;
        "></div>
        <div style="
            position: absolute;
            bottom: -30px;
            left: -30px;
            width: 150px;
            height: 150px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 50%;
        "></div>
        <h1 style="
            font-size: 3.5rem;
            font-weight: 900;
            color: white;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            letter-spacing: -2px;
        ">Resume Relevance System</h1>
        <p style="
            font-size: 1.4rem;
            color: rgba(255, 255, 255, 0.9);
            margin: 1rem 0 0 0;
            font-weight: 300;
        ">AI-Powered Career Matching Platform</p>
        <div style="
            width: 60px;
            height: 4px;
            background: linear-gradient(90deg, #ffd89b, #19547b);
            margin: 2rem auto 0;
            border-radius: 2px;
        "></div>
    </div>
    """, unsafe_allow_html=True)

    # Welcome Message with User Context
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 3rem;
        border-left: 6px solid #ff6b6b;
        box-shadow: 0 10px 25px rgba(252, 182, 159, 0.3);
    ">
        <h2 style="
            color: #2c3e50;
            margin: 0 0 0.5rem 0;
            font-weight: 700;
        ">Welcome back, {st.session_state.username}! 👋</h2>
        <p style="
            color: #34495e;
            margin: 0;
            font-size: 1.1rem;
        ">Ready to {"find your perfect job match" if st.session_state.user_role == "student" else "help students achieve their career goals"}?</p>
    </div>
    """, unsafe_allow_html=True)

    # Core Functions Grid
    st.markdown("""
    <h2 style="
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 3rem 0 2rem 0;
    ">Core Functions</h2>
    """, unsafe_allow_html=True)

    if st.session_state.user_role == "student":
        # Student Dashboard Functions
        col1, col2, col3 = st.columns(3, gap="large")
        
        with col1:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
                padding: 2.5rem 2rem;
                border-radius: 20px;
                text-align: center;
                box-shadow: 0 15px 35px rgba(168, 237, 234, 0.4);
                transition: transform 0.3s ease;
                cursor: pointer;
                border: 2px solid transparent;
            " onmouseover="this.style.transform='translateY(-10px)'" 
               onmouseout="this.style.transform='translateY(0px)'">
                <div style="
                    width: 80px;
                    height: 80px;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 1.5rem;
                    font-size: 2.5rem;
                ">📄</div>
                <h3 style="
                    color: #2c3e50;
                    margin: 0 0 1rem 0;
                    font-weight: 700;
                    font-size: 1.4rem;
                ">Upload Resume</h3>
                <p style="
                    color: #34495e;
                    margin: 0 0 1.5rem 0;
                    line-height: 1.6;
                ">Upload your resume and get it analyzed by our AI system</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📄 Upload Resume", key="dash_upload", use_container_width=True, type="primary"):
                st.session_state.page = "Upload Resume"
                st.rerun()
        
        with col2:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%);
                padding: 2.5rem 2rem;
                border-radius: 20px;
                text-align: center;
                box-shadow: 0 15px 35px rgba(255, 216, 155, 0.4);
                transition: transform 0.3s ease;
                cursor: pointer;
            " onmouseover="this.style.transform='translateY(-10px)'" 
               onmouseout="this.style.transform='translateY(0px)'">
                <div style="
                    width: 80px;
                    height: 80px;
                    background: linear-gradient(135deg, #ff6b6b, #ffa726);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 1.5rem;
                    font-size: 2.5rem;
                ">💼</div>
                <h3 style="
                    color: white;
                    margin: 0 0 1rem 0;
                    font-weight: 700;
                    font-size: 1.4rem;
                ">Browse Jobs</h3>
                <p style="
                    color: rgba(255, 255, 255, 0.9);
                    margin: 0 0 1.5rem 0;
                    line-height: 1.6;
                ">Explore available job opportunities and find your perfect match</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("💼 Browse Jobs", key="dash_jobs", use_container_width=True, type="secondary"):
                st.session_state.page = "View Jobs"
                st.rerun()
        
        with col3:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
                padding: 2.5rem 2rem;
                border-radius: 20px;
                text-align: center;
                box-shadow: 0 15px 35px rgba(255, 154, 158, 0.4);
                transition: transform 0.3s ease;
                cursor: pointer;
            " onmouseover="this.style.transform='translateY(-10px)'" 
               onmouseout="this.style.transform='translateY(0px)'">
                <div style="
                    width: 80px;
                    height: 80px;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 1.5rem;
                    font-size: 2.5rem;
                ">🎯</div>
                <h3 style="
                    color: #2c3e50;
                    margin: 0 0 1rem 0;
                    font-weight: 700;
                    font-size: 1.4rem;
                ">Match Analysis</h3>
                <p style="
                    color: #34495e;
                    margin: 0 0 1.5rem 0;
                    line-height: 1.6;
                ">Get detailed analysis of how well your resume matches job requirements</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🎯 Start Analysis", key="dash_analysis", use_container_width=True, type="secondary"):
                st.session_state.page = "Individual Analysis"
                st.rerun()

    else:
        # Placement Cell Dashboard Functions
        col1, col2, col3 = st.columns(3, gap="large")
        
        with col1:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #d299c2 0%, #fef9d7 100%);
                padding: 2.5rem 2rem;
                border-radius: 20px;
                text-align: center;
                box-shadow: 0 15px 35px rgba(210, 153, 194, 0.4);
                transition: transform 0.3s ease;
                cursor: pointer;
            " onmouseover="this.style.transform='translateY(-10px)'" 
               onmouseout="this.style.transform='translateY(0px)'">
                <div style="
                    width: 80px;
                    height: 80px;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 1.5rem;
                    font-size: 2.5rem;
                ">📚</div>
                <h3 style="
                    color: #2c3e50;
                    margin: 0 0 1rem 0;
                    font-weight: 700;
                    font-size: 1.4rem;
                ">Manage Resumes</h3>
                <p style="
                    color: #34495e;
                    margin: 0 0 1.5rem 0;
                    line-height: 1.6;
                ">View and manage all student resumes in the system</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📚 Manage Resumes", key="dash_resumes", use_container_width=True, type="primary"):
                st.session_state.page = "Manage Resumes"
                st.rerun()
        
        with col2:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%);
                padding: 2.5rem 2rem;
                border-radius: 20px;
                text-align: center;
                box-shadow: 0 15px 35px rgba(137, 247, 254, 0.4);
                transition: transform 0.3s ease;
                cursor: pointer;
            " onmouseover="this.style.transform='translateY(-10px)'" 
               onmouseout="this.style.transform='translateY(0px)'">
                <div style="
                    width: 80px;
                    height: 80px;
                    background: linear-gradient(135deg, #ff6b6b, #ffa726);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 1.5rem;
                    font-size: 2.5rem;
                ">💼</div>
                <h3 style="
                    color: white;
                    margin: 0 0 1rem 0;
                    font-weight: 700;
                    font-size: 1.4rem;
                ">Manage Jobs</h3>
                <p style="
                    color: rgba(255, 255, 255, 0.95);
                    margin: 0 0 1.5rem 0;
                    line-height: 1.6;
                ">Add and manage job descriptions for student matching</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("💼 Manage Jobs", key="dash_manage_jobs", use_container_width=True, type="secondary"):
                st.session_state.page = "Manage Jobs"
                st.rerun()
        
        with col3:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
                padding: 2.5rem 2rem;
                border-radius: 20px;
                text-align: center;
                box-shadow: 0 15px 35px rgba(250, 112, 154, 0.4);
                transition: transform 0.3s ease;
                cursor: pointer;
            " onmouseover="this.style.transform='translateY(-10px)'" 
               onmouseout="this.style.transform='translateY(0px)'">
                <div style="
                    width: 80px;
                    height: 80px;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 1.5rem;
                    font-size: 2.5rem;
                ">📊</div>
                <h3 style="
                    color: #2c3e50;
                    margin: 0 0 1rem 0;
                    font-weight: 700;
                    font-size: 1.4rem;
                ">Batch Evaluation</h3>
                <p style="
                    color: #34495e;
                    margin: 0 0 1.5rem 0;
                    line-height: 1.6;
                ">Run comprehensive analysis on multiple resumes at once</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📊 Batch Evaluation", key="dash_batch", use_container_width=True, type="secondary"):
                st.session_state.page = "Batch Evaluation"
                st.rerun()

    # Additional Features Section
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1], gap="large")
    
    with col1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 3rem;
            border-radius: 20px;
            color: white;
            box-shadow: 0 20px 40px rgba(102, 126, 234, 0.3);
        ">
            <h3 style="
                margin: 0 0 1.5rem 0;
                font-size: 2rem;
                font-weight: 700;
            ">🚀 Why Choose Our Platform?</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                <div>
                    <h4 style="margin: 0 0 0.5rem 0; color: #ffd89b;">⚡ AI-Powered</h4>
                    <p style="margin: 0; opacity: 0.9;">Advanced algorithms for precise matching</p>
                </div>
                <div>
                    <h4 style="margin: 0 0 0.5rem 0; color: #a8edea;">📊 Detailed Analytics</h4>
                    <p style="margin: 0; opacity: 0.9;">Comprehensive scoring and feedback</p>
                </div>
                <div>
                    <h4 style="margin: 0 0 0.5rem 0; color: #ff9a9e;">🎯 Skill Matching</h4>
                    <p style="margin: 0; opacity: 0.9;">Identifies gaps and strengths</p>
                </div>
                <div>
                    <h4 style="margin: 0 0 0.5rem 0; color: #89f7fe;">🔒 Secure & Private</h4>
                    <p style="margin: 0; opacity: 0.9;">Your data is protected</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # System Status
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 10px 25px rgba(252, 182, 159, 0.3);
            height: fit-content;
        ">
            <h4 style="
                margin: 0 0 1.5rem 0;
                color: #2c3e50;
                font-weight: 700;
                text-align: center;
            ">System Status</h4>
        """, unsafe_allow_html=True)
        
        # Get system stats
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM Resumes")
        total_resumes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM JobDescriptions")
        total_jobs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Students")
        total_students = cursor.fetchone()[0]
        
        conn.close()
        
        st.markdown(f"""
            <div style="text-align: center;">
                <div style="margin-bottom: 1rem;">
                    <span style="
                        display: inline-block;
                        background: rgba(255, 107, 107, 0.2);
                        color: #ff6b6b;
                        padding: 0.5rem 1rem;
                        border-radius: 25px;
                        font-weight: 600;
                        margin: 0.25rem;
                    ">📄 {total_resumes} Resumes</span>
                </div>
                <div style="margin-bottom: 1rem;">
                    <span style="
                        display: inline-block;
                        background: rgba(102, 126, 234, 0.2);
                        color: #667eea;
                        padding: 0.5rem 1rem;
                        border-radius: 25px;
                        font-weight: 600;
                        margin: 0.25rem;
                    ">💼 {total_jobs} Jobs</span>
                </div>
                <div>
                    <span style="
                        display: inline-block;
                        background: rgba(16, 185, 129, 0.2);
                        color: #10b981;
                        padding: 0.5rem 1rem;
                        border-radius: 25px;
                        font-weight: 600;
                        margin: 0.25rem;
                    ">👥 {total_students} Students</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def extract_contact_info_from_text(text):
    """Extract contact information from resume text using regex patterns"""
    import re
    
    contact_info = {
        'name': '',
        'email': '',
        'phone': ''
    }
    
    # Email extraction
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    contact_info['email'] = emails[0] if emails else ""
    
    # Phone extraction (Multiple patterns for different formats)
    phone_patterns = [
        r'(\+91|91)?[-.\s]?[6-9]\d{9}',  # Indian mobile numbers
        r'\b[6-9]\d{9}\b',  # Simple 10-digit format
        r'\(\d{3}\)\s?\d{3}-\d{4}',  # US format (xxx) xxx-xxxx
        r'\d{3}-\d{3}-\d{4}',  # US format xxx-xxx-xxxx
        r'\+\d{1,3}[-.\s]?\d{10,14}'  # International format
    ]
    
    for pattern in phone_patterns:
        phones = re.findall(pattern, text)
        if phones:
            # Clean up the phone number
            phone = str(phones[0])
            if isinstance(phones[0], tuple):
                phone = phones[0][0] + phones[0][1] if len(phones[0]) > 1 else phones[0][0]
            contact_info['phone'] = re.sub(r'[^\d+]', '', phone)
            break
    
    # Name extraction - Look for name patterns at the beginning of the resume
    lines = text.split('\n')
    
    # Try to find name in first few lines
    name_patterns = [
        r'^[A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)*$',  # Standard First Last format
        r'^[A-Z][A-Z\s]+$',  # All caps name
    ]
    
    for line in lines[:5]:  # Check first 5 lines
        line = line.strip()
        if len(line) > 0:
            # Skip common headers
            skip_words = ['resume', 'cv', 'curriculum', 'vitae', 'profile', 'contact', 'phone', 'email', 'address']
            if not any(word in line.lower() for word in skip_words):
                # Check if line looks like a name
                words = line.split()
                if 2 <= len(words) <= 4:  # Name should be 2-4 words
                    if all(word.isalpha() or word.replace('.', '').isalpha() for word in words):
                        # Check if it's not an email or phone
                        if '@' not in line and not re.search(r'\d{3,}', line):
                            contact_info['name'] = line.title()
                            break
    
    # Fallback: Look for "Name:" pattern
    if not contact_info['name']:
        name_field_pattern = r'(?:name|full\s*name)\s*:?\s*([A-Za-z\s\.]{2,40})'
        name_match = re.search(name_field_pattern, text, re.IGNORECASE)
        if name_match:
            contact_info['name'] = name_match.group(1).strip().title()
    
    return contact_info

def upload_resume_page():
    """Enhanced resume upload with automatic contact extraction"""
    st.markdown('<h1 class="main-header">Upload Resume</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="upload-area">', unsafe_allow_html=True)
        st.subheader("📄 Upload Your Resume")
        
        uploaded_file = st.file_uploader(
            "Choose a PDF or DOCX file",
            type=['pdf', 'docx', 'doc'],
            help="Upload your resume in PDF or DOCX format"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if uploaded_file:
            st.success(f"File selected: {uploaded_file.name}")
            
            # Extract contact information from the uploaded file
            extracted_info = {'name': '', 'email': '', 'phone': ''}
            
            try:
                # Create a temporary file to extract text
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_file_path = tmp_file.name
                
                # Extract text based on file type
                if uploaded_file.name.lower().endswith('.pdf'):
                    try:
                        import fitz  # PyMuPDF
                        doc = fitz.open(tmp_file_path)
                        text = ""
                        for page_num in range(doc.page_count):
                            page = doc[page_num]
                            text += page.get_text()
                        doc.close()
                        extracted_info = extract_contact_info_from_text(text)
                    except ImportError:
                        st.warning("PDF processing library not available. Please fill in details manually.")
                    except Exception as e:
                        st.warning(f"Could not extract information from PDF: {str(e)}")
                
                elif uploaded_file.name.lower().endswith(('.docx', '.doc')):
                    try:
                        import docx2txt
                        text = docx2txt.process(tmp_file_path)
                        extracted_info = extract_contact_info_from_text(text)
                    except ImportError:
                        st.warning("DOCX processing library not available. Please fill in details manually.")
                    except Exception as e:
                        st.warning(f"Could not extract information from DOCX: {str(e)}")
                
                # Clean up temporary file
                os.unlink(tmp_file_path)
                
                # Show extracted information
                if any(extracted_info.values()):
                    st.info("✨ Automatically extracted information from your resume!")
                
            except Exception as e:
                st.warning(f"Could not process file for auto-extraction: {str(e)}")
            
            # Personal information form with pre-filled values
            with st.form("personal_info"):
                st.subheader("Personal Information")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    name = st.text_input(
                        "Full Name *", 
                        value=extracted_info.get('name', ''),
                        help="Automatically extracted from resume" if extracted_info.get('name') else None
                    )
                    phone = st.text_input(
                        "Phone Number", 
                        value=extracted_info.get('phone', ''),
                        help="Automatically extracted from resume" if extracted_info.get('phone') else None
                    )
                
                with col_b:
                    email = st.text_input(
                        "Email Address *", 
                        value=extracted_info.get('email', ''),
                        help="Automatically extracted from resume" if extracted_info.get('email') else None
                    )
                    linkedin = st.text_input("LinkedIn Profile (optional)")
                
                # Show what was auto-detected
                if any(extracted_info.values()):
                    with st.expander("🔍 Auto-Detected Information", expanded=False):
                        st.json(extracted_info)
                
                submitted = st.form_submit_button("Upload Resume", type="primary", use_container_width=True)
                
                if submitted:
                    if name and email and uploaded_file:
                        try:
                            # Reset file pointer for saving
                            uploaded_file.seek(0)
                            file_content = uploaded_file.read()
                            
                            # Save to database
                            resume_id = save_resume_to_db(
                                st.session_state.user_id, name, email, file_content
                            )
                            
                            st.markdown("""
                            <div class="success-message">
                                ✅ Resume uploaded successfully!<br>
                                Resume ID: {}
                            </div>
                            """.format(resume_id), unsafe_allow_html=True)
                            
                            # If backend is available, also process with the AI system
                            if BACKEND_AVAILABLE:
                                # Save temporarily for processing
                                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                                    tmp_file.write(file_content)
                                    tmp_file_path = tmp_file.name
                                
                                try:
                                    system = init_backend_system()
                                    if system:
                                        backend_resume_id = system.add_resume(tmp_file_path, name, email)
                                        if backend_resume_id:
                                            st.info(f"Resume also processed by AI system. Backend ID: {backend_resume_id}")
                                finally:
                                    os.unlink(tmp_file_path)
                            
                        except Exception as e:
                            st.markdown(f"""
                            <div class="error-message">
                                ❌ Error uploading resume: {str(e)}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.warning("Please fill in all required fields and select a file")
    
    with col2:
        st.subheader("📚 Your Previous Resumes")
        
        # Get user's resumes
        resumes = get_user_resumes(st.session_state.user_id)
        
        if resumes:
            for resume in resumes:
                with st.container():
                    st.markdown(f"""
                    <div class="job-card">
                        <h4 style="margin: 0; color: #1e40af;">{resume[1]}</h4>
                        <p style="margin: 0.5rem 0; color: #64748b;">📧 {resume[2]}</p>
                        <p style="margin: 0; color: #94a3b8; font-size: 0.9rem;">📅 {resume[3][:19]}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No resumes uploaded yet")


def view_jobs_page():
    """Enhanced job viewing page"""
    st.markdown('<h1 class="main-header">Available Job Opportunities</h1>', unsafe_allow_html=True)
    
    # Get all job descriptions
    jobs = get_job_descriptions()
    
    if not jobs:
        st.info("No job descriptions available yet")
        return
    
    # Search and filter
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search jobs by company or role", placeholder="Enter search term...")
    
    with col2:
        sort_by = st.selectbox("Sort by", ["Latest", "Company", "Role"])
    
    # Filter and sort jobs
    filtered_jobs = jobs
    if search_term:
        filtered_jobs = [
            job for job in jobs 
            if search_term.lower() in job[1].lower() or search_term.lower() in job[2].lower()
        ]
    
    # Display jobs
    st.subheader(f"💼 Available Positions ({len(filtered_jobs)})")
    
    for job in filtered_jobs:
        job_id, company_name, job_title, uploaded_at = job
        
        with st.container():
            st.markdown(f"""
            <div class="job-card">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <h3 style="margin: 0; color: #1e40af;">{job_title}</h3>
                        <h4 style="margin: 0.5rem 0; color: #059669;">🏢 {company_name}</h4>
                        <p style="margin: 0; color: #94a3b8; font-size: 0.9rem;">📅 Posted: {uploaded_at[:10]}</p>
                    </div>
                    <div style="text-align: right;">
                        <code style="background: #f1f5f9; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.8rem;">
                            ID: {job_id}
                        </code>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col3:
                if st.button(f"Apply/Analyze", key=f"apply_{job_id}", type="primary"):
                    st.session_state.selected_job_id = job_id
                    st.session_state.page = "Individual Analysis"
                    st.rerun()
            
            st.markdown("---")

def individual_analysis_page():
    """Enhanced individual analysis with database integration"""
    st.markdown('<h1 class="main-header">Individual Analysis</h1>', unsafe_allow_html=True)
    
    # Get data from database
    jobs = get_job_descriptions()
    if st.session_state.user_role == "student":
        resumes = get_user_resumes(st.session_state.user_id)
    else:
        resumes = get_user_resumes()  # All resumes for placement cell
    
    if not jobs:
        st.warning("No job descriptions available")
        return
    
    if not resumes:
        st.warning("No resumes available")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔍 Select Job")
        job_options = {f"{job[1]} - {job[2]}": job[0] for job in jobs}
        selected_job = st.selectbox("Choose a job description", list(job_options.keys()))
        selected_job_id = job_options.get(selected_job)
    
    with col2:
        st.subheader("📄 Select Resume")
        if st.session_state.user_role == "student":
            resume_options = {f"{resume[1]} - {resume[2]}": resume[0] for resume in resumes}
        else:
            resume_options = {f"{resume[1]} ({resume[4]}) - {resume[2]}": resume[0] for resume in resumes}
        
        selected_resume = st.selectbox("Choose a resume", list(resume_options.keys()))
        selected_resume_id = resume_options.get(selected_resume)
    
    # Analysis section
    if st.button("🚀 Analyze Match", type="primary", use_container_width=True):
        if selected_job_id and selected_resume_id and BACKEND_AVAILABLE:
            with st.spinner("Analyzing resume-job match... This may take a few moments."):
                try:
                    # Get file contents from database
                    resume_content = get_file_from_db(selected_resume_id, "resume")
                    job_content = get_file_from_db(selected_job_id, "job")
                    
                    if not resume_content or not job_content:
                        st.error("Could not retrieve file contents")
                        return
                    
                    # Save files temporarily for processing
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as resume_tmp:
                        resume_tmp.write(resume_content)
                        resume_tmp_path = resume_tmp.name
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as job_tmp:
                        job_tmp.write(job_content)
                        job_tmp_path = job_tmp.name
                    
                    try:
                        # Initialize backend system
                        system = init_backend_system()
                        if not system:
                            st.error("Backend system not available")
                            return
                        
                        # Add files to backend system temporarily
                        resume_name = [r[1] for r in resumes if r[0] == selected_resume_id][0]
                        resume_email = [r[2] for r in resumes if r[0] == selected_resume_id][0]
                        
                        job_info = [j for j in jobs if j[0] == selected_job_id][0]
                        company_name = job_info[1]
                        job_title = job_info[2]
                        
                        backend_resume_id = system.add_resume(resume_tmp_path, resume_name, resume_email)
                        backend_job_id = system.add_job_description(job_tmp_path, company_name, job_title)
                        
                        if backend_resume_id and backend_job_id:
                            # Perform evaluation
                            evaluation = system.evaluate_resume(backend_resume_id, backend_job_id)
                            
                            if evaluation:
                                st.success("✅ Analysis completed!")
                                
                                # Display results
                                display_evaluation_results(evaluation)
                            else:
                                st.error("Analysis failed")
                        else:
                            st.error("Failed to process files")
                    
                    finally:
                        # Clean up temporary files
                        os.unlink(resume_tmp_path)
                        os.unlink(job_tmp_path)
                        
                except Exception as e:
                    st.error(f"Error during analysis: {str(e)}")
        
        elif not BACKEND_AVAILABLE:
            st.error("Backend system not available. Please ensure resume_relevance_system.py is properly installed.")
        else:
            st.warning("Please select both job and resume")

def display_evaluation_results(evaluation):
    """Display evaluation results in a professional format"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Relevance Score Gauge
        score = evaluation['relevance_score']
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Relevance Score", 'font': {'size': 20}},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "#1e40af"},
                'steps': [
                    {'range': [0, 50], 'color': "#fee2e2"},
                    {'range': [50, 80], 'color': "#fef3c7"},
                    {'range': [80, 100], 'color': "#d1fae5"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Verdict and Scores
        verdict = evaluation['verdict']
        verdict_class = f"verdict-{verdict.lower()}"
        
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <h3>Verdict</h3>
            <span class="{verdict_class}">{verdict} Fit</span>
            <br><br>
            <h4>Score Breakdown</h4>
            <p><strong>Hard Match:</strong> {evaluation['hard_match_score']:.1f}%</p>
            <p><strong>Soft Match:</strong> {evaluation['soft_match_score']:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Missing Skills
        missing_skills = evaluation.get('missing_skills', [])
        st.markdown(f"""
        <div style="padding: 1rem;">
            <h3>Missing Skills ({len(missing_skills)})</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if missing_skills:
            for i, skill in enumerate(missing_skills[:8], 1):
                st.markdown(f"{i}. {skill}")
            
            if len(missing_skills) > 8:
                st.markdown(f"... and {len(missing_skills) - 8} more")
        else:
            st.success("All required skills matched!")
    
    # Detailed Feedback
    st.markdown("---")
    st.subheader("📝 Detailed Feedback & Recommendations")
    
    with st.expander("View Full Feedback", expanded=True):
        feedback_lines = evaluation['feedback'].split('\n')
        for line in feedback_lines:
            if line.strip():
                if line.startswith('🎯') or line.startswith('✅') or line.startswith('❌') or line.startswith('💡') or line.startswith('📊'):
                    st.markdown(f"**{line}**")
                else:
                    st.markdown(line)
    
    # Export functionality
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export Results (JSON)", use_container_width=True):
            results_json = json.dumps(evaluation, indent=2)
            st.download_button(
                label="Download JSON",
                data=results_json,
                file_name=f"evaluation_{evaluation['evaluation_id'][:8]}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📄 Export Summary (Text)", use_container_width=True):
            summary = f"""
RESUME EVALUATION SUMMARY
========================
Evaluation ID: {evaluation['evaluation_id']}
Date: {evaluation['timestamp']}

OVERALL SCORE: {evaluation['relevance_score']}/100
VERDICT: {evaluation['verdict']} Fit

SCORE BREAKDOWN:
- Hard Match: {evaluation['hard_match_score']}/100
- Soft Match: {evaluation['soft_match_score']}/100

MISSING SKILLS ({len(missing_skills)}):
{chr(10).join([f"- {skill}" for skill in missing_skills[:10]])}

FEEDBACK:
{evaluation['feedback']}
            """
            st.download_button(
                label="Download Summary",
                data=summary,
                file_name=f"evaluation_summary_{evaluation['evaluation_id'][:8]}.txt",
                mime="text/plain"
            )

def manage_jobs_page():
    """Enhanced job management with database integration"""
    st.markdown('<h1 class="main-header">Manage Job Descriptions</h1>', unsafe_allow_html=True)
    
    # Add new job section
    with st.expander("➕ Add New Job Description", expanded=False):
        with st.form("add_job_form"):
            st.subheader("Job Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                company_name = st.text_input("Company Name *")
                job_title = st.text_input("Job Title *")
            
            with col2:
                location = st.text_input("Location")
                salary_range = st.text_input("Salary Range")
            
            # Job description input
            st.subheader("Job Description")
            input_method = st.radio("Input Method", ["Upload File (PDF/DOC)", "Manual Text Entry"])
            
            uploaded_file = None
            job_text = ""
            
            if input_method == "Upload File (PDF/DOC)":
                uploaded_file = st.file_uploader("Upload Job Description", type=['pdf', 'docx', 'doc'])
            else:
                job_text = st.text_area("Job Description Text *", height=200, 
                                      placeholder="Enter the complete job description including requirements, responsibilities, and qualifications...")
            
            submitted = st.form_submit_button("Add Job Description", type="primary", use_container_width=True)
            
            if submitted and company_name and job_title:
                try:
                    if input_method == "Upload File (PDF/DOC)" and uploaded_file:
                        # Handle file upload
                        file_content = uploaded_file.read()
                        job_id = save_job_to_db(st.session_state.user_id, company_name, job_title, file_content)
                        
                    elif input_method == "Manual Text Entry" and job_text:
                        # Handle text input - convert to bytes
                        full_text = f"""Company: {company_name}
Job Title: {job_title}
Location: {location}
Salary Range: {salary_range}

Job Description:
{job_text}"""
                        file_content = full_text.encode('utf-8')
                        job_id = save_job_to_db(st.session_state.user_id, company_name, job_title, file_content)
                    else:
                        st.warning("Please provide job description content")
                        job_id = None
                    
                    if job_id:
                        st.markdown("""
                        <div class="success-message">
                            ✅ Job description added successfully!<br>
                            Job ID: {}
                        </div>
                        """.format(job_id), unsafe_allow_html=True)
                        st.rerun()
                    
                except Exception as e:
                    st.markdown(f"""
                    <div class="error-message">
                        ❌ Error adding job description: {str(e)}
                    </div>
                    """, unsafe_allow_html=True)
            elif submitted:
                st.warning("Please fill in all required fields")
    
    # List existing jobs
    st.subheader("📋 Existing Job Descriptions")
    
    if st.session_state.user_role == "placement":
        jobs = get_job_descriptions(st.session_state.user_id)
    else:
        jobs = get_job_descriptions()
    
    if jobs:
        # Search functionality
        search_term = st.text_input("🔍 Search jobs", placeholder="Search by company or job title...")
        
        filtered_jobs = jobs
        if search_term:
            filtered_jobs = [
                job for job in jobs 
                if search_term.lower() in job[1].lower() or search_term.lower() in job[2].lower()
            ]
        
        st.markdown(f"**Found {len(filtered_jobs)} job(s)**")
        
        for job in filtered_jobs:
            job_id, company_name, job_title, uploaded_at = job
            
            with st.container():
                st.markdown(f"""
                <div class="job-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h3 style="margin: 0; color: #1e40af;">{job_title}</h3>
                            <h4 style="margin: 0.5rem 0; color: #059669;">🏢 {company_name}</h4>
                            <p style="margin: 0; color: #94a3b8; font-size: 0.9rem;">📅 {uploaded_at[:19]}</p>
                        </div>
                        <div>
                            <code style="background: #f1f5f9; padding: 0.25rem 0.5rem; border-radius: 0.25rem;">
                                ID: {job_id}
                            </code>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col2:
                    if st.button("🔍 Analyze All", key=f"analyze_{job_id}"):
                        st.session_state.selected_job_id = job_id
                        st.session_state.page = "Batch Evaluation"
                        st.rerun()
                
                with col3:
                    if st.button("📊 Individual", key=f"individual_{job_id}"):
                        st.session_state.selected_job_id = job_id
                        st.session_state.page = "Individual Evaluation"
                        st.rerun()
                
                st.markdown("---")
    else:
        st.info("No job descriptions available yet")

def manage_resumes_page():
    """Enhanced resume management (Placement Cell only)"""
    if st.session_state.user_role != "placement":
        st.error("Access denied. This page is only for Placement Cell users.")
        return
    
    st.markdown('<h1 class="main-header">Manage Resumes</h1>', unsafe_allow_html=True)
    
    # Get all resumes
    resumes = get_user_resumes()  # All resumes
    
    if not resumes:
        st.info("No resumes uploaded yet")
        return
    
    # Search and filter
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search resumes", placeholder="Search by name, email, or username...")
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # Filter resumes
    filtered_resumes = resumes
    if search_term:
        filtered_resumes = [
            resume for resume in resumes 
            if search_term.lower() in resume[1].lower() or 
               search_term.lower() in resume[2].lower() or 
               search_term.lower() in resume[4].lower()
        ]
    
    st.markdown(f"**Found {len(filtered_resumes)} resume(s)**")
    
    # Display resumes
    for resume in filtered_resumes:
        resume_id, name, email, uploaded_at, username = resume
        
        with st.container():
            st.markdown(f"""
            <div class="job-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3 style="margin: 0; color: #1e40af;">{name}</h3>
                        <p style="margin: 0.25rem 0; color: #059669;">📧 {email}</p>
                        <p style="margin: 0.25rem 0; color: #6366f1;">👤 {username}</p>
                        <p style="margin: 0; color: #94a3b8; font-size: 0.9rem;">📅 {uploaded_at[:19]}</p>
                    </div>
                    <div>
                        <code style="background: #f1f5f9; padding: 0.25rem 0.5rem; border-radius: 0.25rem;">
                            ID: {resume_id}
                        </code>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col2:
                if st.button("📄 Download", key=f"download_{resume_id}"):
                    # Get file content and provide download
                    file_content = get_file_from_db(resume_id, "resume")
                    if file_content:
                        st.download_button(
                            label="Download Resume",
                            data=file_content,
                            file_name=f"resume_{name}_{resume_id}.pdf",
                            mime="application/pdf",
                            key=f"download_btn_{resume_id}"
                        )
            
            with col3:
                if st.button("🔍 Analyze", key=f"analyze_resume_{resume_id}"):
                    st.session_state.selected_resume_id = resume_id
                    st.session_state.page = "Individual Evaluation"
                    st.rerun()
            
            st.markdown("---")
    
    # Summary statistics
    st.markdown("---")
    st.subheader("📊 Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Resumes", len(resumes))
    
    with col2:
        # Count resumes uploaded in last 7 days
        recent_count = sum(1 for r in resumes if (datetime.now() - datetime.fromisoformat(r[3].replace(' ', 'T'))).days <= 7)
        st.metric("This Week", recent_count)
    
    with col3:
        if st.button("📥 Export List", use_container_width=True):
            # Create CSV of resume list
            df = pd.DataFrame(filtered_resumes, columns=['Resume ID', 'Name', 'Email', 'Upload Date', 'Username'])
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"resumes_list_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

def batch_evaluation_page():
    """Enhanced batch evaluation page for placement cell"""
    if st.session_state.user_role != "placement":
        st.error("Access denied. This page is only for Placement Cell users.")
        return
    
    st.markdown('<h1 class="main-header">Batch Evaluation</h1>', unsafe_allow_html=True)
    
    # Get data from database
    jobs = get_job_descriptions()
    resumes = get_user_resumes()  # All resumes for placement cell
    
    if not jobs:
        st.warning("No job descriptions available. Please add job descriptions first.")
        return
    
    if not resumes:
        st.warning("No resumes available. Please wait for students to upload resumes.")
        return
    
    # Job Selection Section
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
    ">
        <h2 style="color: white; margin: 0;">Select Job Description for Batch Evaluation</h2>
        <p style="color: rgba(255, 255, 255, 0.9); margin: 0.5rem 0 0 0;">
            Choose a job description to evaluate all resumes against
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Job selection with detailed cards
    selected_job_id = None
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"Available Job Descriptions ({len(jobs)})")
        
        # Search functionality
        search_term = st.text_input("🔍 Search jobs", placeholder="Search by company or job title...")
        
        filtered_jobs = jobs
        if search_term:
            filtered_jobs = [
                job for job in jobs 
                if search_term.lower() in job[1].lower() or search_term.lower() in job[2].lower()
            ]
        
        # Display job cards with selection
        for job in filtered_jobs:
            job_id, company_name, job_title, uploaded_at = job
            
            with st.container():
                col_info, col_select = st.columns([3, 1])
                
                with col_info:
                    st.markdown(f"""
                    <div class="job-card">
                        <h3 style="margin: 0; color: #1e40af;">{job_title}</h3>
                        <h4 style="margin: 0.5rem 0; color: #059669;">🏢 {company_name}</h4>
                        <p style="margin: 0; color: #94a3b8; font-size: 0.9rem;">📅 {uploaded_at[:19]}</p>
                        <code style="background: #f1f5f9; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.8rem;">
                            ID: {job_id}
                        </code>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_select:
                    if st.button(f"Select & Evaluate", key=f"select_{job_id}", type="primary", use_container_width=True):
                        selected_job_id = job_id
                        # Store in session state for processing
                        st.session_state.batch_job_id = job_id
                        st.session_state.batch_job_title = job_title
                        st.session_state.batch_company_name = company_name
    
    with col2:
        # Statistics overview
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 10px 25px rgba(252, 182, 159, 0.3);
            height: fit-content;
        ">
            <h4 style="margin: 0 0 1rem 0; color: #2c3e50; text-align: center;">System Overview</h4>
            <div style="text-align: center;">
                <div style="margin-bottom: 1rem;">
                    <span style="
                        display: inline-block;
                        background: rgba(59, 130, 246, 0.2);
                        color: #3b82f6;
                        padding: 0.5rem 1rem;
                        border-radius: 25px;
                        font-weight: 600;
                        margin: 0.25rem;
                    ">📄 {len(resumes)} Resumes</span>
                </div>
                <div style="margin-bottom: 1rem;">
                    <span style="
                        display: inline-block;
                        background: rgba(16, 185, 129, 0.2);
                        color: #10b981;
                        padding: 0.5rem 1rem;
                        border-radius: 25px;
                        font-weight: 600;
                        margin: 0.25rem;
                    ">💼 {len(jobs)} Jobs</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Check if a job was selected and perform batch evaluation
    if 'batch_job_id' in st.session_state and BACKEND_AVAILABLE:
        st.markdown("---")
        
        # Display selected job info
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
            padding: 2rem;
            border-radius: 15px;
            margin: 2rem 0;
            border-left: 6px solid #10b981;
            box-shadow: 0 10px 25px rgba(167, 243, 208, 0.3);
        ">
            <h3 style="margin: 0 0 0.5rem 0; color: #2c3e50;">Selected Job for Batch Evaluation</h3>
            <h2 style="margin: 0; color: #1e40af;">{st.session_state.batch_job_title}</h2>
            <p style="margin: 0.5rem 0 0 0; color: #059669; font-size: 1.1rem;">
                🏢 {st.session_state.batch_company_name}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Batch evaluation button and progress
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🚀 Start Batch Evaluation", type="primary", use_container_width=True, key="start_batch"):
                perform_batch_evaluation()
            
            if st.button("🗑️ Clear Selection", type="secondary", use_container_width=True, key="clear_batch"):
                if 'batch_job_id' in st.session_state:
                    del st.session_state.batch_job_id
                if 'batch_job_title' in st.session_state:
                    del st.session_state.batch_job_title
                if 'batch_company_name' in st.session_state:
                    del st.session_state.batch_company_name
                if 'batch_results' in st.session_state:
                    del st.session_state.batch_results
                st.rerun()
    
    # Display results if available
    if 'batch_results' in st.session_state:
        display_batch_results()

import streamlit as st
import tempfile
import os
import json
import traceback
from datetime import datetime
from typing import Dict, List, Any
import logging

# Set up logging for better debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_match_percentage(analysis_result: Dict) -> float:
    """Calculate match percentage based on analysis results"""
    try:
        # Get scores from analysis
        overall_assessment = analysis_result.get("overall_assessment", {})
        
        strength_score = float(overall_assessment.get("strength_score", 5))
        readability_score = float(overall_assessment.get("readability_score", 5))
        ats_score = float(overall_assessment.get("ats_compatibility", 5))
        
        # Calculate weighted average
        # Strength: 50%, ATS: 30%, Readability: 20%
        match_percentage = (strength_score * 0.5 + ats_score * 0.3 + readability_score * 0.2) * 10
        
        # Factor in job matching if available
        job_match = analysis_result.get("job_match", {})
        if job_match and job_match.get('similarity_score', 0) > 0:
            job_similarity = job_match.get('similarity_score', 0)
            # Blend the scores: 70% resume quality + 30% job match
            match_percentage = (match_percentage * 0.7) + (job_similarity * 0.3)
        
        return round(min(100, max(0, match_percentage)), 1)
        
    except Exception as e:
        logger.error(f"Error calculating match percentage: {str(e)}")
        return 50.0  # Default fallback score
        
    except Exception as e:
        logger.error(f"Error calculating match percentage: {str(e)}")
        return 50  # Default fallback
def get_analyzer_instance(analyzer_type: str = "advanced"):
    """Get the appropriate analyzer instance"""
    try:
        if analyzer_type == "advanced":
            return ResumeAnalyzer()
        elif analyzer_type == "text_analysis":
            return TextAnalysisResumeAnalyzer()
        else:
            return SimpleResumeAnalyzer()
    except Exception as e:
        logger.error(f"Error initializing {analyzer_type} analyzer: {str(e)}")
        # Fallback to simple analyzer
        try:
            return SimpleResumeAnalyzer()
        except:
            return None


def perform_batch_evaluation():
    """Enhanced batch evaluation with local analyzers (No API keys required)"""
    
    if 'batch_job_id' not in st.session_state:
        st.error("No job selected for batch evaluation")
        return
    
    job_id = st.session_state.batch_job_id
    
    try:
        # Get all resumes and job description
        resumes = get_user_resumes()  # Assuming this function exists
        
        if not resumes:
            st.error("No resumes found for evaluation")
            return
        
        # Initialize progress tracking
        total_resumes = len(resumes)
        st.markdown(f"### 🔄 Processing {total_resumes} resumes...")
        
        # Analyzer selection
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("🤖 Using local AI analyzer - no external APIs required!")
        with col2:
            analyzer_type = st.selectbox(
                "Analyzer Type:",
                ["advanced", "text_analysis", "simple"],
                format_func=lambda x: {
                    "advanced": "🧠 Advanced NLP",
                    "text_analysis": "📊 Text Analysis", 
                    "simple": "⚡ Simple"
                }.get(x, x)
            )
        
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        results_container = st.empty()
        
        # Initialize results storage
        batch_results = []
        successful_analyses = 0
        failed_analyses = 0
        error_details = []
        
        # Performance tracking
        start_time = datetime.now()
        processing_times = []
        
        # Get job description once
        job_description = ""
        try:
            job_content = get_file_from_db(job_id, "job")
            if job_content:
                job_description = extract_text_from_resume_file(job_content, 'txt')
                logger.info(f"Successfully extracted job description: {len(job_description)} characters")
            else:
                st.warning("Could not retrieve job description content")
        except Exception as e:
            st.error(f"Error retrieving job description: {str(e)}")
            logger.error(f"Job description error: {str(e)}")
        
        # Initialize local analyzer with enhanced error handling
        try:
            analyzer = get_analyzer_instance(analyzer_type)
            if analyzer is None:
                st.error("Failed to initialize any analyzer. Please check your Python environment.")
                return
            logger.info(f"Local {analyzer_type} analyzer initialized successfully")
            st.success(f"✅ {analyzer_type.replace('_', ' ').title()} analyzer ready!")
        except Exception as e:
            st.error(f"Error initializing local analyzer: {str(e)}")
            logger.error(f"Analyzer initialization error: {str(e)}")
            return
        
        # Process each resume
        for idx, resume in enumerate(resumes):
            resume_start_time = datetime.now()
            resume_id, resume_filename, upload_date, user_name = resume[:4]
            
            try:
                # Update progress
                progress = (idx + 1) / total_resumes
                progress_bar.progress(progress)
                status_text.text(f"Processing: {resume_filename} ({idx + 1}/{total_resumes})")
                
                # Log processing start
                logger.info(f"Processing resume {idx + 1}/{total_resumes}: {resume_filename}")
                
                # Get resume content with error handling
                resume_content = None
                try:
                    resume_content = get_file_from_db(resume_id, "resume")
                    if not resume_content:
                        raise ValueError(f"No content retrieved for resume ID {resume_id}")
                    logger.info(f"Retrieved resume content: {len(resume_content)} bytes")
                except Exception as e:
                    error_msg = f"Failed to retrieve resume content: {str(e)}"
                    logger.error(error_msg)
                    error_details.append({
                        'resume': resume_filename,
                        'error': error_msg,
                        'stage': 'content_retrieval'
                    })
                    failed_analyses += 1
                    continue
                
                # Extract text from resume with enhanced error handling
                resume_text = ""
                try:
                    file_extension = resume_filename.split('.')[-1].lower() if '.' in resume_filename else 'pdf'
                    resume_text = extract_text_from_resume_file(resume_content, file_extension)
                    
                    if "Error" in resume_text:
                        raise ValueError(f"Text extraction failed: {resume_text}")
                    
                    if len(resume_text.strip()) < 50:
                        logger.warning(f"Resume text seems short: {len(resume_text)} characters")
                        # Continue processing even with short text
                    
                    logger.info(f"Extracted text: {len(resume_text)} characters")
                    
                except Exception as e:
                    error_msg = f"Failed to extract text: {str(e)}"
                    logger.error(error_msg)
                    error_details.append({
                        'resume': resume_filename,
                        'error': error_msg,
                        'stage': 'text_extraction'
                    })
                    failed_analyses += 1
                    continue
                
                # Perform local analysis with enhanced error handling
                try:
                    if hasattr(analyzer, 'analyze_resume_comprehensively'):
                        analysis_result = analyzer.analyze_resume_comprehensively(resume_text, job_description)
                    elif hasattr(analyzer, 'basic_analysis'):
                        analysis_result = analyzer.basic_analysis(resume_text)
                    else:
                        raise AttributeError("Analyzer doesn't have expected analysis methods")
                    
                    if not analysis_result:
                        raise ValueError("Analysis returned empty result")
                    
                    if "error" in analysis_result:
                        raise ValueError(f"Analysis returned error: {analysis_result.get('error', 'Unknown error')}")
                    
                    # Calculate match percentage from analysis
                    match_percentage = calculate_match_percentage(analysis_result)
                    
                    # Calculate processing time
                    processing_time = (datetime.now() - resume_start_time).total_seconds()
                    processing_times.append(processing_time)
                    
                    # Store successful result
                    result = {
                        'resume_id': resume_id,
                        'resume_filename': resume_filename,
                        'user_name': user_name,
                        'upload_date': upload_date,
                        'match_percentage': match_percentage,
                        'analysis': analysis_result,
                        'status': 'success',
                        'processing_time': processing_time,
                        'analyzer_type': analyzer_type,
                        'processed_at': datetime.now().isoformat()
                    }
                    
                    batch_results.append(result)
                    successful_analyses += 1
                    logger.info(f"Successfully analyzed: {resume_filename} - Match: {match_percentage}% (Time: {processing_time:.2f}s)")
                    
                except Exception as e:
                    error_msg = f"Local analysis failed: {str(e)}"
                    logger.error(f"Analysis error for {resume_filename}: {error_msg}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    
                    error_details.append({
                        'resume': resume_filename,
                        'error': error_msg,
                        'stage': 'local_analysis'
                    })
                    failed_analyses += 1
                    
                    # Add failed result to maintain record
                    result = {
                        'resume_id': resume_id,
                        'resume_filename': resume_filename,
                        'user_name': user_name,
                        'upload_date': upload_date,
                        'match_percentage': 0,
                        'analysis': {'error': error_msg},
                        'status': 'failed',
                        'processing_time': 0,
                        'analyzer_type': analyzer_type,
                        'processed_at': datetime.now().isoformat()
                    }
                    batch_results.append(result)
                    continue
                
            except Exception as e:
                # Catch-all for any unexpected errors
                error_msg = f"Unexpected error processing resume: {str(e)}"
                logger.error(f"Unexpected error for {resume_filename}: {error_msg}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                error_details.append({
                    'resume': resume_filename,
                    'error': error_msg,
                    'stage': 'general_processing'
                })
                failed_analyses += 1
                continue
        
        # Complete progress
        progress_bar.progress(1.0)
        total_time = (datetime.now() - start_time).total_seconds()
        avg_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        status_text.text("✅ Batch evaluation completed!")
        
        # Store results in session state with enhanced metadata
        st.session_state.batch_results = {
            'results': batch_results,
            'job_id': job_id,
            'job_title': st.session_state.get('batch_job_title', 'Unknown'),
            'company_name': st.session_state.get('batch_company_name', 'Unknown'),
            'total_processed': total_resumes,
            'successful': successful_analyses,
            'failed': failed_analyses,
            'error_details': error_details,
            'analyzer_type': analyzer_type,
            'performance_stats': {
                'total_time': total_time,
                'average_time_per_resume': avg_time,
                'processing_times': processing_times
            },
            'processed_at': datetime.now().isoformat()
        }
        
        # Display enhanced summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("✅ Successful", successful_analyses, f"out of {total_resumes}")
        
        with col2:
            st.metric("❌ Failed", failed_analyses)
            
        with col3:
            st.metric("⏱️ Avg Time", f"{avg_time:.1f}s", "per resume")
        
        st.success(f"🎉 Batch evaluation completed in {total_time:.1f} seconds using {analyzer_type.replace('_', ' ').title()} analyzer!")
        
        if failed_analyses > 0:
            st.warning(f"⚠️ {failed_analyses} resumes failed to process. Check error details below.")
        
        # Display error details if any
        if error_details:
            with st.expander(f"❌ Error Details ({len(error_details)} errors)", expanded=False):
                for error in error_details:
                    st.error(f"**{error['resume']}** - {error['stage']}: {error['error']}")
        
        # Display performance statistics
        if processing_times:
            with st.expander("📊 Performance Statistics", expanded=False):
                st.write(f"**Total Processing Time:** {total_time:.2f} seconds")
                st.write(f"**Average Time per Resume:** {avg_time:.2f} seconds")
                st.write(f"**Fastest Analysis:** {min(processing_times):.2f} seconds")
                st.write(f"**Slowest Analysis:** {max(processing_times):.2f} seconds")
                st.write(f"**Analyzer Used:** {analyzer_type.replace('_', ' ').title()}")
        
        logger.info(f"Batch evaluation completed: {successful_analyses} successful, {failed_analyses} failed, Total time: {total_time:.2f}s")
        
    except Exception as e:
        st.error(f"Critical error in batch evaluation: {str(e)}")
        logger.error(f"Critical batch evaluation error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")


def display_batch_results():
    """Enhanced display of batch evaluation results"""
    
    if 'batch_results' not in st.session_state:
        st.warning("No batch evaluation results found. Please run a batch evaluation first.")
        return
    
    batch_data = st.session_state.batch_results
    results = batch_data.get('results', [])
    
    if not results:
        st.warning("No results to display.")
        return
    
    # Header with job information
    st.markdown(f"## 📊 Batch Evaluation Results")
    st.markdown(f"**Job:** {batch_data.get('job_title', 'Unknown')} at {batch_data.get('company_name', 'Unknown')}")
    st.markdown(f"**Processed:** {batch_data.get('processed_at', 'Unknown')} using {batch_data.get('analyzer_type', 'Unknown').replace('_', ' ').title()} analyzer")
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Resumes", batch_data.get('total_processed', 0))
    
    with col2:
        st.metric("Successful", batch_data.get('successful', 0))
    
    with col3:
        st.metric("Failed", batch_data.get('failed', 0))
    
    with col4:
        success_rate = (batch_data.get('successful', 0) / max(1, batch_data.get('total_processed', 1))) * 100
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    # Performance stats if available
    perf_stats = batch_data.get('performance_stats', {})
    if perf_stats:
        st.markdown("### ⚡ Performance Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Time", f"{perf_stats.get('total_time', 0):.1f}s")
        
        with col2:
            st.metric("Avg per Resume", f"{perf_stats.get('average_time_per_resume', 0):.1f}s")
        
        with col3:
            analyzer_type = batch_data.get('analyzer_type', 'unknown')
            st.metric("Analyzer Used", analyzer_type.replace('_', ' ').title())
    
    # Filter and sort options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Successful", "Failed"],
            key="batch_status_filter"
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Match Percentage (High to Low)", "Match Percentage (Low to High)", 
             "Name (A-Z)", "Name (Z-A)", "Date Uploaded"],
            key="batch_sort_option"
        )
    
    with col3:
        show_details = st.checkbox("Show Analysis Details", value=False)
    
    # Filter results
    filtered_results = results
    if status_filter == "Successful":
        filtered_results = [r for r in results if r.get('status') == 'success']
    elif status_filter == "Failed":
        filtered_results = [r for r in results if r.get('status') == 'failed']
    
    # Sort results
    if sort_by == "Match Percentage (High to Low)":
        filtered_results = sorted(filtered_results, key=lambda x: x.get('match_percentage', 0), reverse=True)
    elif sort_by == "Match Percentage (Low to High)":
        filtered_results = sorted(filtered_results, key=lambda x: x.get('match_percentage', 0))
    elif sort_by == "Name (A-Z)":
        filtered_results = sorted(filtered_results, key=lambda x: x.get('resume_filename', ''))
    elif sort_by == "Name (Z-A)":
        filtered_results = sorted(filtered_results, key=lambda x: x.get('resume_filename', ''), reverse=True)
    elif sort_by == "Date Uploaded":
        filtered_results = sorted(filtered_results, key=lambda x: x.get('upload_date', ''), reverse=True)
    
    # Display results
    st.markdown(f"### 📋 Results ({len(filtered_results)} resumes)")
    
    for idx, result in enumerate(filtered_results, 1):
        status = result.get('status', 'unknown')
        match_percentage = result.get('match_percentage', 0)
        filename = result.get('resume_filename', 'Unknown')
        user_name = result.get('user_name', 'Unknown')
        processing_time = result.get('processing_time', 0)
        
        # Status indicator
        status_icon = "✅" if status == 'success' else "❌"
        status_color = "success" if status == 'success' else "error"
        
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.write(f"{status_icon} **{filename}**")
                st.caption(f"Candidate: {user_name}")
            
            with col2:
                if status == 'success':
                    st.metric("Match Score", f"{match_percentage}%")
                else:
                    st.write("❌ Processing Failed")
            
            with col3:
                st.write(f"⏱️ {processing_time:.1f}s")
                st.caption(f"Uploaded: {result.get('upload_date', 'Unknown')}")
            
            with col4:
                if show_details and status == 'success':
                    if st.button(f"📄 Details", key=f"details_{idx}"):
                        st.session_state[f'show_analysis_{idx}'] = True
        
        # Show detailed analysis if requested
        if show_details and status == 'success' and st.session_state.get(f'show_analysis_{idx}', False):
            with st.expander(f"📊 Detailed Analysis: {filename}", expanded=True):
                analysis = result.get('analysis', {})
                
                # Display analysis summary
                overall = analysis.get('overall_assessment', {})
                if overall:
                    subcol1, subcol2, subcol3 = st.columns(3)
                    
                    with subcol1:
                        st.metric("Strength", f"{overall.get('strength_score', 'N/A')}/10")
                    with subcol2:
                        st.metric("Readability", f"{overall.get('readability_score', 'N/A')}/10")
                    with subcol3:
                        st.metric("ATS Score", f"{overall.get('ats_compatibility', 'N/A')}/10")
                
                # Show strengths and weaknesses
                strengths = analysis.get('strengths', [])
                weaknesses = analysis.get('weaknesses', [])
                
                if strengths:
                    st.write("**✅ Strengths:**")
                    for strength in strengths[:3]:  # Show top 3
                        st.write(f"• {strength}")
                
                if weaknesses:
                    st.write("**⚠️ Areas for Improvement:**")
                    for weakness in weaknesses[:3]:  # Show top 3
                        st.write(f"• {weakness}")
                
                # Hide details button
                if st.button(f"Hide Details", key=f"hide_{idx}"):
                    st.session_state[f'show_analysis_{idx}'] = False
                    st.rerun()
        
        st.divider()
    
    # Export options
    st.markdown("### 📥 Export Results")
    col1, col2 = st.columns(2)
    
    with col1:
        # Create CSV export
        if st.button("📊 Export to CSV"):
            import pandas as pd
            
            export_data = []
            for result in results:
                export_data.append({
                    'Resume': result.get('resume_filename', ''),
                    'Candidate': result.get('user_name', ''),
                    'Match Percentage': result.get('match_percentage', 0),
                    'Status': result.get('status', ''),
                    'Processing Time (s)': result.get('processing_time', 0),
                    'Upload Date': result.get('upload_date', ''),
                    'Processed At': result.get('processed_at', '')
                })
            
            df = pd.DataFrame(export_data)
            csv = df.to_csv(index=False)
            
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"batch_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        # Create JSON export
        if st.button("📄 Export Full Report (JSON)"):
            import json
            
            report_json = json.dumps(batch_data, indent=2, default=str)
            
            st.download_button(
                label="Download JSON Report",
                data=report_json,
                file_name=f"batch_evaluation_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
def extract_text_from_resume_file(file_content, file_extension):
    """Enhanced text extraction with better error handling"""
    try:
        logger.info(f"Extracting text from {file_extension} file ({len(file_content)} bytes)")
        
        if file_extension.lower() == 'pdf':
            return extract_pdf_text(file_content)
        elif file_extension.lower() in ['docx', 'doc']:
            return extract_docx_text(file_content)
        elif file_extension.lower() == 'txt':
            return extract_txt_text(file_content)
        else:
            # Try to decode as text
            try:
                text = file_content.decode('utf-8', errors='ignore')
                if len(text.strip()) > 0:
                    return text
                else:
                    raise ValueError("Decoded text is empty")
            except Exception as e:
                return f"Error: Unsupported file format '{file_extension}': {str(e)}"
                
    except Exception as e:
        logger.error(f"Text extraction error: {str(e)}")
        return f"Error extracting text: {str(e)}"

def extract_pdf_text(file_content):
    """Extract text from PDF with fallback options"""
    try:
        # Try PyMuPDF first
        try:
            import fitz  # PyMuPDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name
            
            doc = fitz.open(tmp_file_path)
            text = ""
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text += page.get_text()
            doc.close()
            os.unlink(tmp_file_path)
            
            if len(text.strip()) > 0:
                return text
            else:
                raise ValueError("PDF appears to be empty or image-based")
                
        except ImportError:
            # Try pdfplumber as fallback
            try:
                import pdfplumber
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(file_content)
                    tmp_file_path = tmp_file.name
                
                text = ""
                with pdfplumber.open(tmp_file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text
                
                os.unlink(tmp_file_path)
                
                if len(text.strip()) > 0:
                    return text
                else:
                    raise ValueError("PDF appears to be empty or image-based")
                    
            except ImportError:
                return "Error: No PDF processing library available (install PyMuPDF or pdfplumber)"
                
    except Exception as e:
        logger.error(f"PDF extraction error: {str(e)}")
        return f"Error extracting PDF: {str(e)}"

def extract_docx_text(file_content):
    """Extract text from DOCX files"""
    try:
        import docx2txt
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name
        
        text = docx2txt.process(tmp_file_path)
        os.unlink(tmp_file_path)
        
        if text and len(text.strip()) > 0:
            return text
        else:
            # Try alternative method
            try:
                from docx import Document
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
                    tmp_file.write(file_content)
                    tmp_file_path = tmp_file.name
                
                doc = Document(tmp_file_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                os.unlink(tmp_file_path)
                return text
                
            except ImportError:
                return "Error: python-docx library not available"
                
    except ImportError:
        return "Error: docx2txt library not available. Please install python-docx2txt."
    except Exception as e:
        logger.error(f"DOCX extraction error: {str(e)}")
        return f"Error extracting DOCX: {str(e)}"

def extract_txt_text(file_content):
    """Extract text from TXT files"""
    try:
        # Try different encodings
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                text = file_content.decode(encoding)
                if len(text.strip()) > 0:
                    return text
            except UnicodeDecodeError:
                continue
        
        # If all encodings fail, use utf-8 with error handling
        return file_content.decode('utf-8', errors='replace')
        
    except Exception as e:
        logger.error(f"TXT extraction error: {str(e)}")
        return f"Error extracting text: {str(e)}"

def display_batch_results():
    """Enhanced display of batch results with error handling"""
    
    if 'batch_results' not in st.session_state:
        st.warning("No batch results available")
        return
    
    batch_data = st.session_state.batch_results
    results = batch_data.get('results', [])
    
    if not results:
        st.warning("No results to display")
        return
    
    # Results header
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
    ">
        <h2 style="color: white; margin: 0;">Batch Evaluation Results</h2>
        <p style="color: rgba(255, 255, 255, 0.9); margin: 0.5rem 0 0 0;">
            {batch_data.get('job_title', 'Unknown Job')} at {batch_data.get('company_name', 'Unknown Company')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Resumes", batch_data.get('total_processed', 0))
    
    with col2:
        st.metric("Successfully Processed", batch_data.get('successful', 0), 
                 delta=f"{batch_data.get('successful', 0) - batch_data.get('failed', 0)}")
    
    with col3:
        st.metric("Failed", batch_data.get('failed', 0))
    
    with col4:
        success_rate = 0
        if batch_data.get('total_processed', 0) > 0:
            success_rate = (batch_data.get('successful', 0) / batch_data.get('total_processed', 1)) * 100
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    # Filter and sort options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_status = st.selectbox("Filter by Status", ["All", "Success", "Failed"])
    
    with col2:
        sort_by = st.selectbox("Sort by", ["Match %", "Name", "Date"])
    
    with col3:
        sort_order = st.selectbox("Order", ["Descending", "Ascending"])
    
    # Filter results
    filtered_results = results
    if filter_status != "All":
        filtered_results = [r for r in results if r['status'] == filter_status.lower()]
    
    # Sort results
    if sort_by == "Match %":
        filtered_results.sort(key=lambda x: x['match_percentage'], reverse=(sort_order == "Descending"))
    elif sort_by == "Name":
        filtered_results.sort(key=lambda x: x['user_name'], reverse=(sort_order == "Descending"))
    elif sort_by == "Date":
        filtered_results.sort(key=lambda x: x['upload_date'], reverse=(sort_order == "Descending"))
    
    # Display results
    st.markdown(f"### 📊 Results ({len(filtered_results)} shown)")
    
    for i, result in enumerate(filtered_results):
        with st.expander(
            f"{'✅' if result['status'] == 'success' else '❌'} "
            f"{result['user_name']} - {result['match_percentage']}% match",
            expanded=False
        ):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Resume:** {result['resume_filename']}")
                st.write(f"**Uploaded:** {result['upload_date'][:19]}")
                st.write(f"**Status:** {result['status'].title()}")
                
                if result['status'] == 'success':
                    st.write(f"**Match Percentage:** {result['match_percentage']}%")
                else:
                    st.error(f"**Error:** {result['analysis'].get('error', 'Unknown error')}")
            
            with col2:
                if result['status'] == 'success' and 'analysis' in result:
                    analysis = result['analysis']
                    overall = analysis.get('overall_assessment', {})
                    
                    st.write("**Scores:**")
                    st.write(f"- Strength: {overall.get('strength_score', 'N/A')}")
                    st.write(f"- Readability: {overall.get('readability_score', 'N/A')}")
                    st.write(f"- ATS: {overall.get('ats_compatibility', 'N/A')}")
                    
                    if st.button(f"View Details", key=f"detail_{i}"):
                        st.json(analysis)
    
    # Export functionality
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        # Download results as JSON
        results_json = json.dumps(batch_data, indent=2)
        st.download_button(
            label="📥 Download Results (JSON)",
            data=results_json,
            file_name=f"batch_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    with col2:
        # Download results as CSV
        csv_data = create_csv_from_results(results)
        st.download_button(
            label="📊 Download Results (CSV)",
            data=csv_data,
            file_name=f"batch_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

def create_csv_from_results(results):
    """Create CSV format from results"""
    import io
    
    output = io.StringIO()
    output.write("User Name,Resume File,Upload Date,Status,Match Percentage,Strength Score,Readability Score,ATS Score\n")
    
    for result in results:
        analysis = result.get('analysis', {})
        overall = analysis.get('overall_assessment', {})
        
        output.write(f"{result['user_name']},")
        output.write(f"{result['resume_filename']},")
        output.write(f"{result['upload_date'][:19]},")
        output.write(f"{result['status']},")
        output.write(f"{result['match_percentage']},")
        output.write(f"{overall.get('strength_score', 'N/A')},")
        output.write(f"{overall.get('readability_score', 'N/A')},")
        output.write(f"{overall.get('ats_compatibility', 'N/A')}\n")
    
    return output.getvalue()




def get_comprehensive_system_stats():
    """Get detailed system statistics from database without evaluations table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Basic counts
        cursor.execute('SELECT COUNT(*) FROM Students')
        stats['total_students'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM PlacementUsers')
        stats['total_placement_officers'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM Resumes')
        stats['total_resumes'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM JobDescriptions')
        stats['total_jobs'] = cursor.fetchone()[0]
        
        # Student details with resume counts
        cursor.execute('''
            SELECT s.student_id, s.username, COUNT(r.resume_id) as resume_count,
                   MAX(r.uploaded_at) as last_resume_upload
            FROM Students s
            LEFT JOIN Resumes r ON s.student_id = r.student_id
            GROUP BY s.student_id, s.username
            ORDER BY resume_count DESC, s.username
        ''')
        stats['student_details'] = cursor.fetchall()
        
        # Resume statistics (without evaluations)
        cursor.execute('''
            SELECT r.resume_id, r.name, r.email, r.uploaded_at, s.username
            FROM Resumes r
            JOIN Students s ON r.student_id = s.student_id
            ORDER BY r.uploaded_at DESC
        ''')
        stats['resume_details'] = cursor.fetchall()
        
        # Job description statistics (without evaluations)
        cursor.execute('''
            SELECT j.job_id, j.company_name, j.job_title, j.uploaded_at, p.username
            FROM JobDescriptions j
            JOIN PlacementUsers p ON j.placement_id = p.placement_id
            ORDER BY j.uploaded_at DESC
        ''')
        stats['job_details'] = cursor.fetchall()
        
        # Set evaluation-related stats to 0 since no evaluations table exists
        stats['total_evaluations'] = 0
        stats['avg_relevance_score'] = 0
        stats['verdict_distribution'] = {'High': 0, 'Medium': 0, 'Low': 0}
        stats['score_distribution'] = {
            'Excellent (90-100)': 0,
            'Very Good (80-89)': 0,
            'Good (70-79)': 0,
            'Fair (60-69)': 0,
            'Poor (<60)': 0
        }
        
        # Recent activity (last 30 days)
        try:
            cursor.execute('''
                SELECT COUNT(*) FROM Students 
                WHERE created_at > datetime('now', '-30 days')
            ''')
            result = cursor.fetchone()
            stats['new_students_30d'] = result[0] if result else 0
        except:
            # If created_at column doesn't exist, count all students as recent
            stats['new_students_30d'] = stats['total_students']
        
        cursor.execute('''
            SELECT COUNT(*) FROM Resumes 
            WHERE uploaded_at > datetime('now', '-30 days')
        ''')
        stats['new_resumes_30d'] = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM JobDescriptions 
            WHERE uploaded_at > datetime('now', '-30 days')
        ''')
        stats['new_jobs_30d'] = cursor.fetchone()[0]
        
        stats['new_evaluations_30d'] = 0  # No evaluations table
        
        # Top performing resumes (based on resume count per student)
        cursor.execute('''
            SELECT r.name, r.email, s.username, COUNT(r.resume_id) as resume_count
            FROM Resumes r
            JOIN Students s ON r.student_id = s.student_id
            GROUP BY s.student_id, r.name, r.email, s.username
            ORDER BY resume_count DESC, r.name
            LIMIT 10
        ''')
        top_resumes_raw = cursor.fetchall()
        
        # Format for display (simulate evaluation data)
        stats['top_resumes'] = []
        for resume in top_resumes_raw:
            stats['top_resumes'].append((
                resume[0],  # name
                resume[1],  # email  
                resume[2],  # username
                0,          # avg_score (placeholder)
                resume[3]   # resume_count
            ))
        
        # Most active companies
        cursor.execute('''
            SELECT j.company_name, COUNT(j.job_id) as job_count
            FROM JobDescriptions j
            GROUP BY j.company_name
            ORDER BY job_count DESC
            LIMIT 10
        ''')
        top_companies_raw = cursor.fetchall()
        
        # Format for display
        stats['top_companies'] = []
        for company in top_companies_raw:
            stats['top_companies'].append((
                company[0],  # company_name
                company[1],  # job_count
                0,           # total_evaluations (placeholder)
                0            # avg_score (placeholder)
            ))
        
        # Additional useful statistics without evaluations
        # Resume upload trends (by month)
        cursor.execute('''
            SELECT strftime('%Y-%m', uploaded_at) as month, COUNT(*) as count
            FROM Resumes 
            WHERE uploaded_at IS NOT NULL
            GROUP BY strftime('%Y-%m', uploaded_at)
            ORDER BY month DESC
            LIMIT 12
        ''')
        stats['resume_trends'] = cursor.fetchall()
        
        # Job posting trends (by month)
        cursor.execute('''
            SELECT strftime('%Y-%m', uploaded_at) as month, COUNT(*) as count
            FROM JobDescriptions 
            WHERE uploaded_at IS NOT NULL
            GROUP BY strftime('%Y-%m', uploaded_at)
            ORDER BY month DESC
            LIMIT 12
        ''')
        stats['job_trends'] = cursor.fetchall()
        
        # Company diversity
        cursor.execute('SELECT COUNT(DISTINCT company_name) FROM JobDescriptions')
        stats['unique_companies'] = cursor.fetchone()[0]
        
        # Resume format distribution (if you store file extensions)
        cursor.execute('''
            SELECT 'PDF' as format, COUNT(*) as count FROM Resumes
            UNION ALL
            SELECT 'DOCX' as format, 0 as count
            UNION ALL  
            SELECT 'DOC' as format, 0 as count
        ''')
        stats['resume_formats'] = dict(cursor.fetchall())
        
        conn.close()
        return stats
        
    except Exception as e:
        print(f"Error getting system stats: {str(e)}")
        return {}


def system_statistics_page():
    """Comprehensive system statistics page without evaluation dependencies"""
    if st.session_state.user_role != "placement":
        st.error("Access denied. This page is only for Placement Cell users.")
        return
    
    st.markdown('<h1 class="main-header">System Statistics</h1>', unsafe_allow_html=True)
    
    # Get comprehensive statistics
    with st.spinner("Loading system statistics..."):
        stats = get_comprehensive_system_stats()
    
    if not stats:
        st.error("Unable to load system statistics")
        return
    
    # Overview Dashboard
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
    ">
        <h2 style="color: white; margin: 0;">System Overview Dashboard</h2>
        <p style="color: rgba(255, 255, 255, 0.9); margin: 0.5rem 0 0 0;">
            Comprehensive analytics and insights
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Metrics Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #3b82f6;">
            <h4 style="margin: 0; color: #1e40af;">Total Students</h4>
            <h2 style="margin: 0; color: #2563eb;">{stats['total_students']}</h2>
            <p style="margin: 0; color: #64748b; font-size: 0.9rem;">+{stats.get('new_students_30d', 0)} this month</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #10b981;">
            <h4 style="margin: 0; color: #059669;">Total Resumes</h4>
            <h2 style="margin: 0; color: #10b981;">{stats['total_resumes']}</h2>
            <p style="margin: 0; color: #64748b; font-size: 0.9rem;">+{stats.get('new_resumes_30d', 0)} this month</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #f59e0b;">
            <h4 style="margin: 0; color: #d97706;">Job Descriptions</h4>
            <h2 style="margin: 0; color: #f59e0b;">{stats['total_jobs']}</h2>
            <p style="margin: 0; color: #64748b; font-size: 0.9rem;">+{stats.get('new_jobs_30d', 0)} this month</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #8b5cf6;">
            <h4 style="margin: 0; color: #7c3aed;">Unique Companies</h4>
            <h2 style="margin: 0; color: #8b5cf6;">{stats['unique_companies']}</h2>
            <p style="margin: 0; color: #64748b; font-size: 0.9rem;">Posting opportunities</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 System Overview", 
        "👥 Student Details", 
        "📄 Resume Analytics", 
        "💼 Job Analytics", 
        "🏆 Top Contributors", 
        "📈 Activity Trends"
    ])
    
    with tab1:
        st.subheader("System Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Active vs Inactive Students
            active_students = len([s for s in stats.get('student_details', []) if s[2] > 0])
            inactive_students = stats['total_students'] - active_students
            
            if stats['total_students'] > 0:
                import plotly.express as px
                import pandas as pd
                
                df_activity = pd.DataFrame({
                    'Status': ['Active (with resumes)', 'Inactive (no resumes)'],
                    'Count': [active_students, inactive_students]
                })
                fig_activity = px.pie(df_activity, values='Count', names='Status', 
                                    title="Student Activity Status",
                                    color_discrete_map={'Active (with resumes)': '#10b981', 
                                                      'Inactive (no resumes)': '#ef4444'})
                st.plotly_chart(fig_activity, use_container_width=True)
        
        with col2:
            # Resume distribution by student
            if stats.get('student_details'):
                resume_counts = [s[2] for s in stats['student_details']]
                distribution = {
                    '0 resumes': resume_counts.count(0),
                    '1 resume': resume_counts.count(1),
                    '2-3 resumes': len([c for c in resume_counts if 2 <= c <= 3]),
                    '4+ resumes': len([c for c in resume_counts if c >= 4])
                }
                
                df_dist = pd.DataFrame(list(distribution.items()), columns=['Category', 'Count'])
                fig_dist = px.bar(df_dist, x='Category', y='Count', 
                                title="Resume Distribution per Student",
                                color='Count', color_continuous_scale='Blues')
                st.plotly_chart(fig_dist, use_container_width=True)
        
        # Key system metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_resumes_per_student = stats['total_resumes'] / stats['total_students'] if stats['total_students'] > 0 else 0
            st.metric("Avg Resumes per Student", f"{avg_resumes_per_student:.1f}")
        
        with col2:
            avg_jobs_per_company = stats['total_jobs'] / stats['unique_companies'] if stats['unique_companies'] > 0 else 0
            st.metric("Avg Jobs per Company", f"{avg_jobs_per_company:.1f}")
        
        with col3:
            engagement_rate = (active_students / stats['total_students']) * 100 if stats['total_students'] > 0 else 0
            st.metric("Student Engagement Rate", f"{engagement_rate:.1f}%")
    
    with tab2:
        st.subheader("Student Details")
        
        if stats.get('student_details'):
            st.markdown(f"**Total Students: {len(stats['student_details'])}**")
            
            # Create DataFrame for better display
            import pandas as pd
            
            student_data = []
            for student in stats['student_details']:
                student_data.append({
                    'Student ID': student[0],
                    'Username': student[1], 
                    'Resume Count': student[2],
                    'Last Upload': student[3][:19] if student[3] else 'Never',
                    'Status': 'Active' if student[2] > 0 else 'Inactive'
                })
            
            df_students = pd.DataFrame(student_data)
            
            # Filter and search
            col1, col2 = st.columns(2)
            
            with col1:
                status_filter = st.selectbox("Filter by Status", ["All", "Active", "Inactive"])
            
            with col2:
                search_student = st.text_input("Search students by username")
            
            # Apply filters
            filtered_df = df_students
            if status_filter != "All":
                filtered_df = filtered_df[filtered_df['Status'] == status_filter]
            if search_student:
                filtered_df = filtered_df[filtered_df['Username'].str.contains(search_student, case=False)]
            
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
            
            # Statistics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                active_count = len([s for s in stats['student_details'] if s[2] > 0])
                st.metric("Active Students", active_count, f"{active_count/len(stats['student_details'])*100:.1f}%")
            
            with col2:
                total_uploads = sum(s[2] for s in stats['student_details'])
                st.metric("Total Resume Uploads", total_uploads)
            
            with col3:
                avg_uploads = total_uploads / len(stats['student_details']) if stats['student_details'] else 0
                st.metric("Avg Uploads/Student", f"{avg_uploads:.1f}")
            
            with col4:
                inactive_count = len([s for s in stats['student_details'] if s[2] == 0])
                st.metric("Inactive Students", inactive_count)
    
    with tab3:
        st.subheader("Resume Analytics")
        
        if stats.get('resume_details'):
            st.markdown(f"**Total Resumes: {len(stats['resume_details'])}**")
            
            # Resume data
            resume_data = []
            for resume in stats['resume_details']:
                resume_data.append({
                    'Resume ID': resume[0][:8] + '...' if len(str(resume[0])) > 8 else str(resume[0]),
                    'Candidate Name': resume[1],
                    'Email': resume[2],
                    'Username': resume[4],
                    'Upload Date': resume[3][:10] if resume[3] else 'N/A'
                })
            
            df_resumes = pd.DataFrame(resume_data)
            
            # Search functionality
            search_resume = st.text_input("Search by candidate name or email")
            if search_resume:
                df_resumes = df_resumes[
                    df_resumes['Candidate Name'].str.contains(search_resume, case=False) |
                    df_resumes['Email'].str.contains(search_resume, case=False)
                ]
            
            st.dataframe(df_resumes, use_container_width=True, hide_index=True)
            
            # Resume upload trends
            if stats.get('resume_trends'):
                st.markdown("**📈 Resume Upload Trends (Last 12 Months)**")
                
                trend_data = stats['resume_trends']
                df_trends = pd.DataFrame(trend_data, columns=['Month', 'Uploads'])
                
                fig_trends = px.line(df_trends, x='Month', y='Uploads', 
                                   title="Monthly Resume Uploads",
                                   markers=True)
                fig_trends.update_layout(xaxis_title="Month", yaxis_title="Number of Uploads")
                st.plotly_chart(fig_trends, use_container_width=True)
            
        else:
            st.info("No resume data available")
    
    with tab4:
        st.subheader("Job Description Analytics")
        
        if stats.get('job_details'):
            st.markdown(f"**Total Job Descriptions: {len(stats['job_details'])}**")
            
            # Job data
            job_data = []
            for job in stats['job_details']:
                job_data.append({
                    'Job ID': job[0][:8] + '...' if len(str(job[0])) > 8 else str(job[0]),
                    'Company': job[1],
                    'Job Title': job[2],
                    'Posted By': job[4],
                    'Upload Date': job[3][:10] if job[3] else 'N/A'
                })
            
            df_jobs = pd.DataFrame(job_data)
            
            # Search functionality
            search_job = st.text_input("Search jobs by company or title")
            if search_job:
                df_jobs = df_jobs[
                    df_jobs['Company'].str.contains(search_job, case=False) |
                    df_jobs['Job Title'].str.contains(search_job, case=False)
                ]
            
            st.dataframe(df_jobs, use_container_width=True, hide_index=True)
            
            # Company statistics
            company_stats = {}
            for job in stats['job_details']:
                company = job[1]
                if company in company_stats:
                    company_stats[company] += 1
                else:
                    company_stats[company] = 1
            
            st.markdown("**🏢 Jobs by Company**")
            
            # Top companies chart
            if company_stats:
                top_companies = sorted(company_stats.items(), key=lambda x: x[1], reverse=True)[:10]
                df_companies = pd.DataFrame(top_companies, columns=['Company', 'Job Count'])
                
                fig_companies = px.bar(df_companies, x='Company', y='Job Count',
                                     title="Top 10 Companies by Job Postings",
                                     color='Job Count', color_continuous_scale='Viridis')
                fig_companies.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_companies, use_container_width=True)
            
            # Job posting trends
            if stats.get('job_trends'):
                st.markdown("**📈 Job Posting Trends (Last 12 Months)**")
                
                job_trend_data = stats['job_trends']
                df_job_trends = pd.DataFrame(job_trend_data, columns=['Month', 'Job Postings'])
                
                fig_job_trends = px.line(df_job_trends, x='Month', y='Job Postings', 
                                       title="Monthly Job Postings",
                                       markers=True, color_discrete_sequence=['#f59e0b'])
                fig_job_trends.update_layout(xaxis_title="Month", yaxis_title="Number of Job Postings")
                st.plotly_chart(fig_job_trends, use_container_width=True)
        
        else:
            st.info("No job data available")
    
    with tab5:
        st.subheader("Top Contributors")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🏆 Most Active Students (by resume count)**")
            if stats.get('top_resumes'):
                for i, resume in enumerate(stats['top_resumes'], 1):
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
                        padding: 1rem;
                        border-radius: 10px;
                        margin: 0.5rem 0;
                        border-left: 4px solid #10b981;
                    ">
                        <h4 style="margin: 0; color: #1e40af;">#{i} {resume[0]}</h4>
                        <p style="margin: 0; color: #059669;">Resumes: {resume[4]} | @{resume[2]}</p>
                        <p style="margin: 0; color: #6b7280; font-size: 0.9rem;">{resume[1]}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No student activity data available yet")
        
        with col2:
            st.markdown("**🏢 Most Active Companies (by job postings)**")
            if stats.get('top_companies'):
                for i, company in enumerate(stats['top_companies'], 1):
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
                        padding: 1rem;
                        border-radius: 10px;
                        margin: 0.5rem 0;
                        border-left: 4px solid #3b82f6;
                    ">
                        <h4 style="margin: 0; color: #1e40af;">#{i} {company[0]}</h4>
                        <p style="margin: 0; color: #2563eb;">Job Postings: {company[1]}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No company data available yet")
        
        # Additional metrics
        st.markdown("**📊 System Health Metrics**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            participation_rate = (len([s for s in stats.get('student_details', []) if s[2] > 0]) / stats['total_students']) * 100 if stats['total_students'] > 0 else 0
            st.metric("Student Participation", f"{participation_rate:.1f}%", "Students with resumes")
        
        with col2:
            company_diversity = stats['unique_companies'] / stats['total_jobs'] if stats['total_jobs'] > 0 else 0
            st.metric("Company Diversity", f"{company_diversity:.2f}", "Unique companies per job")
        
        with col3:
            if stats['total_students'] > 0 and stats['total_jobs'] > 0:
                opportunity_ratio = stats['total_jobs'] / stats['total_students']
                st.metric("Job-to-Student Ratio", f"{opportunity_ratio:.2f}", "Jobs per student")
    
    with tab6:
        st.subheader("Activity Trends")
        
        # Recent activity summary
        st.markdown("**📈 Recent Activity (Last 30 Days)**")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #e0f2fe 0%, #b3e5fc 100%);
                padding: 1.5rem;
                border-radius: 10px;
                text-align: center;
            ">
                <h3 style="margin: 0; color: #0277bd;">{stats.get('new_students_30d', 0)}</h3>
                <p style="margin: 0; color: #455a64;">New Students</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
                padding: 1.5rem;
                border-radius: 10px;
                text-align: center;
            ">
                <h3 style="margin: 0; color: #7b1fa2;">{stats.get('new_resumes_30d', 0)}</h3>
                <p style="margin: 0; color: #455a64;">New Resumes</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
                padding: 1.5rem;
                border-radius: 10px;
                text-align: center;
            ">
                <h3 style="margin: 0; color: #f57c00;">{stats.get('new_jobs_30d', 0)}</h3>
                <p style="margin: 0; color: #455a64;">New Jobs</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            total_activity = stats.get('new_students_30d', 0) + stats.get('new_resumes_30d', 0) + stats.get('new_jobs_30d', 0)
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
                padding: 1.5rem;
                border-radius: 10px;
                text-align: center;
            ">
                <h3 style="margin: 0; color: #388e3c;">{total_activity}</h3>
                <p style="margin: 0; color: #455a64;">Total Activity</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Combined trends visualization
        if stats.get('resume_trends') and stats.get('job_trends'):
            st.markdown("**📊 Combined Activity Trends**")
            
            # Merge resume and job trends
            resume_dict = {month: count for month, count in stats['resume_trends']}
            job_dict = {month: count for month, count in stats['job_trends']}
            
            all_months = sorted(set(resume_dict.keys()) | set(job_dict.keys()), reverse=True)
            
            combined_data = []
            for month in all_months:
                combined_data.append({
                    'Month': month,
                    'Resumes': resume_dict.get(month, 0),
                    'Jobs': job_dict.get(month, 0)
                })
            
            df_combined = pd.DataFrame(combined_data)
            
            fig_combined = px.line(df_combined, x='Month', y=['Resumes', 'Jobs'],
                                 title="Resume and Job Posting Trends",
                                 labels={'value': 'Count', 'variable': 'Type'})
            fig_combined.update_layout(xaxis_title="Month", yaxis_title="Count")
            st.plotly_chart(fig_combined, use_container_width=True)
        
        # System growth indicators
        st.markdown("**🔧 System Growth Indicators**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Calculate growth rate for resumes
            recent_resumes = stats.get('new_resumes_30d', 0)
            growth_rate = (recent_resumes / stats['total_resumes']) * 100 if stats['total_resumes'] > 0 else 0
            st.metric("Resume Growth Rate", f"{growth_rate:.1f}%", "Monthly growth")
        
        with col2:
            # Calculate growth rate for jobs
            recent_jobs = stats.get('new_jobs_30d', 0)
            job_growth_rate = (recent_jobs / stats['total_jobs']) * 100 if stats['total_jobs'] > 0 else 0
            st.metric("Job Growth Rate", f"{job_growth_rate:.1f}%", "Monthly growth")
    
     # Export functionality
    st.markdown("---")
    st.subheader("📥 Export System Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export Detailed Report (JSON)", use_container_width=True):
            import json
            report_data = {
                'generated_at': datetime.now().isoformat(),
                'summary': {
                    'total_students': stats['total_students'],
                    'total_resumes': stats['total_resumes'], 
                    'total_jobs': stats['total_jobs'],
                    'unique_companies': stats['unique_companies']
                },
                'activity_trends': {
                    'resume_trends': stats.get('resume_trends', []),
                    'job_trends': stats.get('job_trends', [])
                },
                'recent_activity': {
                    'new_students_30d': stats.get('new_students_30d', 0),
                    'new_resumes_30d': stats.get('new_resumes_30d', 0),
                    'new_jobs_30d': stats.get('new_jobs_30d', 0)
                },
                'top_contributors': {
                    'top_students': stats.get('top_resumes', []),
                    'top_companies': stats.get('top_companies', [])
                }
            }
            
            report_json = json.dumps(report_data, indent=2, default=str)
            st.download_button(
                label="Download JSON Report",
                data=report_json,
                file_name=f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📄 Export Summary (CSV)", use_container_width=True):
            # Create summary CSV
            import pandas as pd
            
            summary_data = {
                'Metric': [
                    'Total Students', 
                    'Total Resumes', 
                    'Total Jobs', 
                    'Unique Companies',
                    'Active Students',
                    'Inactive Students',
                    'Student Engagement Rate (%)',
                    'Avg Resumes per Student',
                    'Avg Jobs per Company',
                    'New Students (30d)',
                    'New Resumes (30d)',
                    'New Jobs (30d)'
                ],
                'Value': [
                    stats['total_students'], 
                    stats['total_resumes'],
                    stats['total_jobs'],
                    stats['unique_companies'],
                    len([s for s in stats.get('student_details', []) if s[2] > 0]),
                    len([s for s in stats.get('student_details', []) if s[2] == 0]),
                    round((len([s for s in stats.get('student_details', []) if s[2] > 0]) / stats['total_students']) * 100, 1) if stats['total_students'] > 0 else 0,
                    round(stats['total_resumes'] / stats['total_students'], 1) if stats['total_students'] > 0 else 0,
                    round(stats['total_jobs'] / stats['unique_companies'], 1) if stats['unique_companies'] > 0 else 0,
                    stats.get('new_students_30d', 0),
                    stats.get('new_resumes_30d', 0),
                    stats.get('new_jobs_30d', 0)
                ]
            }
            
            df_summary = pd.DataFrame(summary_data)
            csv = df_summary.to_csv(index=False)
            
            st.download_button(
                label="Download CSV Summary", 
                data=csv,
                file_name=f"system_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )


class ResumeAnalyzer:
    """Advanced resume analyzer using NLP and rule-based analysis (No API required)"""
    
    def __init__(self):
        """Initialize the analyzer with predefined skills and keywords"""
        self.technical_skills = {
            'programming_languages': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby', 
                'go', 'rust', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql'
            ],
            'frameworks': [
                'react', 'angular', 'vue', 'nodejs', 'express', 'django', 'flask', 
                'spring', 'laravel', 'rails', 'bootstrap', 'jquery', 'nextjs'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle', 
                'cassandra', 'elasticsearch', 'firebase'
            ],
            'cloud_platforms': [
                'aws', 'azure', 'gcp', 'google cloud', 'digitalocean', 'heroku', 
                'vercel', 'netlify'
            ],
            'tools': [
                'git', 'docker', 'kubernetes', 'jenkins', 'ansible', 'terraform', 
                'jira', 'confluence', 'slack', 'trello'
            ],
            'data_science': [
                'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras', 
                'matplotlib', 'seaborn', 'plotly', 'jupyter'
            ]
        }
        
        self.soft_skills = [
            'leadership', 'teamwork', 'communication', 'problem solving', 'analytical',
            'creative', 'adaptable', 'organized', 'detail oriented', 'time management',
            'project management', 'collaboration', 'mentoring', 'presentation', 
            'negotiation', 'critical thinking'
        ]
        
        self.action_verbs = [
            'achieved', 'analyzed', 'built', 'created', 'designed', 'developed',
            'engineered', 'enhanced', 'established', 'executed', 'implemented',
            'improved', 'increased', 'led', 'managed', 'optimized', 'organized',
            'reduced', 'resolved', 'streamlined', 'supervised'
        ]
        
        # Common job titles and their required skills
        self.job_skill_mapping = {
            'software developer': ['programming_languages', 'frameworks', 'databases', 'tools'],
            'data scientist': ['data_science', 'programming_languages', 'databases'],
            'web developer': ['programming_languages', 'frameworks', 'databases'],
            'devops engineer': ['cloud_platforms', 'tools', 'programming_languages'],
            'project manager': ['soft_skills', 'tools'],
            'business analyst': ['soft_skills', 'databases', 'tools']
        }
    
    def extract_contact_info(self, text: str) -> Dict:
        """Extract contact information from resume"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        github_pattern = r'github\.com/[\w-]+'
        
        return {
            'emails': re.findall(email_pattern, text),
            'phones': re.findall(phone_pattern, text),
            'linkedin': re.findall(linkedin_pattern, text, re.IGNORECASE),
            'github': re.findall(github_pattern, text, re.IGNORECASE)
        }
    
    def extract_skills(self, text: str) -> Dict:
        """Extract technical and soft skills from resume"""
        text_lower = text.lower()
        found_skills = {'technical': {}, 'soft': []}
        
        # Extract technical skills
        for category, skills in self.technical_skills.items():
            found = []
            for skill in skills:
                if skill in text_lower:
                    found.append(skill)
            if found:
                found_skills['technical'][category] = found
        
        # Extract soft skills
        for skill in self.soft_skills:
            if skill in text_lower:
                found_skills['soft'].append(skill)
        
        return found_skills
    
    def analyze_experience(self, text: str) -> Dict:
        """Analyze work experience section"""
        # Look for experience indicators
        experience_patterns = [
            r'(\d+)[\+\-\s]*years?\s+(?:of\s+)?experience',
            r'experience[:\s]+(\d+)[\+\-\s]*years?',
            r'(\d+)[\+\-\s]*yrs?\s+(?:of\s+)?experience'
        ]
        
        years_experience = []
        for pattern in experience_patterns:
            matches = re.findall(pattern, text.lower())
            years_experience.extend([int(match) for match in matches])
        
        # Count action verbs usage
        action_verb_count = 0
        for verb in self.action_verbs:
            action_verb_count += len(re.findall(rf'\b{verb}\w*', text.lower()))
        
        # Look for quantified achievements
        number_patterns = [
            r'\d+%', r'\$\d+', r'\d+k', r'\d+m', r'\d+\s*million',
            r'\d+\s*thousand', r'increased.*?\d+', r'reduced.*?\d+',
            r'improved.*?\d+', r'grew.*?\d+'
        ]
        
        quantified_achievements = 0
        for pattern in number_patterns:
            quantified_achievements += len(re.findall(pattern, text.lower()))
        
        return {
            'estimated_years': max(years_experience) if years_experience else 0,
            'action_verbs_count': action_verb_count,
            'quantified_achievements': quantified_achievements,
            'has_leadership_keywords': any(keyword in text.lower() 
                                         for keyword in ['led', 'managed', 'supervised', 'mentored', 'coordinated'])
        }
    
    def analyze_education(self, text: str) -> Dict:
        """Analyze education section"""
        education_keywords = [
            'bachelor', 'master', 'phd', 'doctorate', 'degree', 'university',
            'college', 'institute', 'certification', 'diploma'
        ]
        
        education_mentions = []
        for keyword in education_keywords:
            if keyword in text.lower():
                education_mentions.append(keyword)
        
        # Look for GPA mentions
        gpa_pattern = r'gpa[:\s]*(\d+\.\d+)'
        gpa_matches = re.findall(gpa_pattern, text.lower())
        
        return {
            'education_keywords': education_mentions,
            'gpa_mentioned': len(gpa_matches) > 0,
            'gpa_values': gpa_matches
        }
    
    def calculate_ats_score(self, text: str) -> Dict:
        """Calculate ATS compatibility score"""
        score = 10
        issues = []
        
        # Check for problematic formatting
        if len(re.findall(r'[^\x00-\x7F]', text)) > 10:
            score -= 1
            issues.append("Contains special characters that may cause parsing issues")
        
        # Check for standard sections
        required_sections = ['experience', 'education', 'skills']
        section_score = 0
        for section in required_sections:
            if section in text.lower():
                section_score += 1
        
        if section_score < 2:
            score -= 2
            issues.append("Missing standard resume sections")
        
        # Check for contact information
        contact_info = self.extract_contact_info(text)
        if not contact_info['emails']:
            score -= 1
            issues.append("Missing email address")
        
        # Check readability
        readability = textstat.flesch_reading_ease(text)
        if readability < 30:
            score -= 1
            issues.append("Text may be too complex for ATS parsing")
        
        return {
            'score': max(0, score),
            'issues': issues,
            'readability': readability
        }
    
    def compare_with_job_description(self, resume_text: str, job_description: str) -> Dict:
        """Compare resume with job description using TF-IDF similarity"""
        if not job_description.strip():
            return {'similarity_score': 0, 'missing_keywords': [], 'matching_keywords': []}
        
        # Preprocess texts
        def preprocess(text):
            text = re.sub(r'[^\w\s]', ' ', text.lower())
            tokens = word_tokenize(text)
            stop_words = set(stopwords.words('english'))
            return ' '.join([word for word in tokens if word not in stop_words and len(word) > 2])
        
        resume_processed = preprocess(resume_text)
        job_processed = preprocess(job_description)
        
        # Calculate TF-IDF similarity
        vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform([resume_processed, job_processed])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        # Extract important keywords from job description
        job_words = Counter(job_processed.split())
        important_job_keywords = [word for word, count in job_words.most_common(20) if count > 1]
        
        # Find matching and missing keywords
        resume_words = set(resume_processed.split())
        matching_keywords = [kw for kw in important_job_keywords if kw in resume_words]
        missing_keywords = [kw for kw in important_job_keywords if kw not in resume_words]
        
        return {
            'similarity_score': round(similarity * 100, 2),
            'matching_keywords': matching_keywords,
            'missing_keywords': missing_keywords[:10]  # Top 10 missing keywords
        }
    
    def generate_recommendations(self, analysis_result: Dict) -> Dict:
        """Generate improvement recommendations based on analysis"""
        recommendations = {
            'immediate_actions': [],
            'short_term_goals': [],
            'long_term_development': []
        }
        
        # Immediate actions
        if analysis_result['ats_compatibility']['score'] < 8:
            recommendations['immediate_actions'].extend([
                "Improve resume formatting for better ATS compatibility",
                "Add missing contact information",
                "Use standard section headings (Experience, Education, Skills)"
            ])
        
        if analysis_result['experience']['action_verbs_count'] < 5:
            recommendations['immediate_actions'].append(
                "Add more action verbs to describe your achievements"
            )
        
        if analysis_result['experience']['quantified_achievements'] < 3:
            recommendations['immediate_actions'].append(
                "Quantify your achievements with numbers, percentages, or dollar amounts"
            )
        
        # Short-term goals
        missing_skills = analysis_result.get('missing_skills', [])
        if missing_skills:
            recommendations['short_term_goals'].append(
                f"Learn these in-demand skills: {', '.join(missing_skills[:5])}"
            )
        
        if not analysis_result['experience']['has_leadership_keywords']:
            recommendations['short_term_goals'].append(
                "Gain leadership experience and highlight it on your resume"
            )
        
        # Long-term development
        recommendations['long_term_development'].extend([
            "Pursue relevant certifications in your field",
            "Build a portfolio of projects to showcase your skills",
            "Attend industry conferences and networking events",
            "Consider advanced education or specialized training"
        ])
        
        return recommendations
    
    def analyze_resume_comprehensively(self, resume_text: str, job_description: str = "") -> Dict:
        """Perform comprehensive resume analysis"""
        
        # Basic text analysis
        word_count = len(resume_text.split())
        sentence_count = len(sent_tokenize(resume_text))
        
        # Extract various components
        contact_info = self.extract_contact_info(resume_text)
        skills = self.extract_skills(resume_text)
        experience = self.analyze_experience(resume_text)
        education = self.analyze_education(resume_text)
        ats_analysis = self.calculate_ats_score(resume_text)
        
        # Job comparison if provided
        job_match = self.compare_with_job_description(resume_text, job_description)
        
        # Calculate overall scores
        strength_score = min(10, (
            (len(skills['technical']) * 2) +
            len(skills['soft']) +
            (experience['action_verbs_count'] * 0.5) +
            (experience['quantified_achievements'] * 0.5) +
            (3 if contact_info['emails'] else 0)
        ) / 2)
        
        readability_score = min(10, ats_analysis['readability'] / 10)
        
        # Generate strengths and weaknesses
        strengths = []
        weaknesses = []
        
        if len(skills['technical']) > 0:
            strengths.append(f"Strong technical skill set with {sum(len(v) for v in skills['technical'].values())} technical skills identified")
        
        if experience['quantified_achievements'] > 2:
            strengths.append("Good use of quantified achievements to demonstrate impact")
        
        if experience['action_verbs_count'] > 8:
            strengths.append("Excellent use of action verbs to describe responsibilities")
        
        if contact_info['linkedin'] or contact_info['github']:
            strengths.append("Professional online presence with LinkedIn/GitHub profiles")
        
        # Weaknesses
        if len(skills['technical']) == 0:
            weaknesses.append("Limited technical skills mentioned")
        
        if experience['quantified_achievements'] < 2:
            weaknesses.append("Lacks quantified achievements and measurable results")
        
        if experience['action_verbs_count'] < 5:
            weaknesses.append("Could use more dynamic action verbs")
        
        if word_count < 300:
            weaknesses.append("Resume appears to be too brief")
        elif word_count > 1000:
            weaknesses.append("Resume may be too lengthy")
        
        # Generate recommendations
        recommendations = self.generate_recommendations({
            'ats_compatibility': ats_analysis,
            'experience': experience,
            'missing_skills': job_match.get('missing_keywords', [])
        })
        
        return {
            "overall_assessment": {
                "strength_score": round(strength_score, 1),
                "readability_score": round(readability_score, 1),
                "ats_compatibility": ats_analysis['score'],
                "summary": f"Resume analysis complete. Identified {sum(len(v) for v in skills['technical'].values())} technical skills and {len(skills['soft'])} soft skills."
            },
            "strengths": strengths,
            "weaknesses": weaknesses,
            "skills_analysis": {
                "technical_skills": skills['technical'],
                "soft_skills": skills['soft'],
                "total_technical": sum(len(v) for v in skills['technical'].values()),
                "total_soft": len(skills['soft'])
            },
            "experience_analysis": experience,
            "contact_info": contact_info,
            "ats_compatibility": ats_analysis,
            "job_match": job_match,
            "improvement_suggestions": recommendations,
            "resume_stats": {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "readability": ats_analysis['readability']
            }
        }


class TextAnalysisResumeAnalyzer:
    """Alternative analyzer using pure text analysis and pattern matching"""
    
    def __init__(self):
        self.skill_database = self._load_skill_database()
        self.industry_keywords = self._load_industry_keywords()
    
    def _load_skill_database(self) -> Dict:
        """Load comprehensive skill database"""
        return {
            'programming': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby',
                'go', 'rust', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql', 'html',
                'css', 'bash', 'powershell', 'perl', 'assembly'
            ],
            'frameworks_libraries': [
                'react', 'angular', 'vue', 'nodejs', 'express', 'django', 'flask',
                'spring', 'laravel', 'rails', 'bootstrap', 'jquery', 'nextjs', 'nuxt',
                'svelte', 'ember', 'backbone', 'meteor', 'gatsby'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle',
                'cassandra', 'elasticsearch', 'neo4j', 'dynamodb', 'firebase',
                'influxdb', 'couchdb'
            ],
            'cloud_devops': [
                'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes',
                'jenkins', 'git', 'github', 'gitlab', 'bitbucket', 'ansible',
                'terraform', 'chef', 'puppet', 'nagios', 'prometheus'
            ],
            'data_science_ml': [
                'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras',
                'matplotlib', 'seaborn', 'plotly', 'jupyter', 'r studio', 'tableau',
                'power bi', 'apache spark', 'hadoop', 'kafka'
            ],
            'design_tools': [
                'photoshop', 'illustrator', 'figma', 'sketch', 'indesign',
                'after effects', 'premiere pro', 'canva', 'adobe xd'
            ],
            'soft_skills': [
                'leadership', 'teamwork', 'communication', 'problem solving',
                'analytical thinking', 'creativity', 'adaptability', 'time management',
                'project management', 'collaboration', 'mentoring', 'presentation',
                'negotiation', 'critical thinking', 'decision making'
            ]
        }
    
    def _load_industry_keywords(self) -> Dict:
        """Load industry-specific keywords"""
        return {
            'software_development': [
                'agile', 'scrum', 'ci/cd', 'api', 'microservices', 'responsive design',
                'user experience', 'debugging', 'testing', 'deployment'
            ],
            'data_science': [
                'machine learning', 'data analysis', 'statistics', 'data visualization',
                'big data', 'predictive modeling', 'deep learning', 'neural networks'
            ],
            'marketing': [
                'seo', 'sem', 'content marketing', 'social media', 'email marketing',
                'analytics', 'conversion optimization', 'brand management'
            ],
            'finance': [
                'financial analysis', 'budgeting', 'forecasting', 'risk management',
                'compliance', 'audit', 'investment', 'portfolio management'
            ]
        }
    
    def extract_skills_advanced(self, text: str) -> Dict:
        """Advanced skill extraction with context awareness"""
        text_lower = text.lower()
        extracted_skills = {}
        
        for category, skills in self.skill_database.items():
            found_skills = []
            for skill in skills:
                # Use word boundaries to avoid partial matches
                pattern = rf'\b{re.escape(skill)}\b'
                if re.search(pattern, text_lower):
                    found_skills.append(skill)
            
            if found_skills:
                extracted_skills[category] = found_skills
        
        return extracted_skills
    
    def analyze_resume_structure(self, text: str) -> Dict:
        """Analyze resume structure and format"""
        sections = {
            'contact': False,
            'summary': False,
            'experience': False,
            'education': False,
            'skills': False,
            'projects': False
        }
        
        section_patterns = {
            'contact': r'(email|phone|address|linkedin)',
            'summary': r'(summary|profile|objective|about)',
            'experience': r'(experience|employment|work history|professional)',
            'education': r'(education|degree|university|college)',
            'skills': r'(skills|competencies|technologies)',
            'projects': r'(projects|portfolio|work samples)'
        }
        
        for section, pattern in section_patterns.items():
            if re.search(pattern, text.lower()):
                sections[section] = True
        
        return sections
    
    def calculate_keyword_density(self, text: str, keywords: List[str]) -> Dict:
        """Calculate keyword density for given keywords"""
        text_lower = text.lower()
        word_count = len(text.split())
        
        keyword_counts = {}
        for keyword in keywords:
            count = len(re.findall(rf'\b{re.escape(keyword)}\b', text_lower))
            density = (count / word_count) * 100 if word_count > 0 else 0
            keyword_counts[keyword] = {
                'count': count,
                'density': round(density, 2)
            }
        
        return keyword_counts
    
    def generate_skill_recommendations(self, current_skills: Dict, target_role: str = "") -> List[str]:
        """Generate skill recommendations based on current skills and target role"""
        all_current_skills = []
        for category_skills in current_skills.values():
            all_current_skills.extend(category_skills)
        
        recommendations = []
        
        # General recommendations based on missing popular skills
        popular_skills = {
            'programming': ['python', 'javascript', 'sql'],
            'cloud_devops': ['aws', 'docker', 'git'],
            'data_science_ml': ['pandas', 'numpy', 'matplotlib'],
            'soft_skills': ['leadership', 'communication', 'problem solving']
        }
        
        for category, skills in popular_skills.items():
            missing_skills = [skill for skill in skills if skill not in all_current_skills]
            if missing_skills:
                recommendations.extend(missing_skills[:2])  # Top 2 missing skills per category
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def analyze_resume_comprehensively(self, resume_text: str, job_description: str = "") -> Dict:
        """Comprehensive analysis using text processing techniques"""
        
        # Extract skills
        skills = self.extract_skills_advanced(resume_text)
        
        # Analyze structure
        structure = self.analyze_resume_structure(resume_text)
        
        # Basic statistics
        word_count = len(resume_text.split())
        char_count = len(resume_text)
        
        # Calculate scores
        skill_score = min(10, len([skill for skills_list in skills.values() for skill in skills_list]) * 0.5)
        structure_score = sum(structure.values()) * 1.67  # 6 sections max, so 1.67 per section for 10 points
        length_score = 10 if 300 <= word_count <= 800 else (8 if word_count > 200 else 5)
        
        overall_score = (skill_score + structure_score + length_score) / 3
        
        # Generate insights
        strengths = []
        weaknesses = []
        
        if len(skills) >= 3:
            strengths.append(f"Diverse skill set across {len(skills)} categories")
        
        if structure['experience'] and structure['education']:
            strengths.append("Well-structured resume with key sections")
        
        if word_count >= 400:
            strengths.append("Appropriate resume length with sufficient detail")
        
        # Weaknesses
        if len(skills) < 2:
            weaknesses.append("Limited skill diversity - consider adding more technical skills")
        
        if not structure['contact']:
            weaknesses.append("Missing clear contact information")
        
        if word_count < 300:
            weaknesses.append("Resume appears too brief - add more detail about your experience")
        
        # Recommendations
        skill_recommendations = self.generate_skill_recommendations(skills)
        
        return {
            "overall_assessment": {
                "strength_score": round(overall_score, 1),
                "readability_score": round(length_score, 1),
                "ats_compatibility": round(structure_score, 1),
                "summary": f"Analysis complete. Found {sum(len(v) for v in skills.values())} total skills across {len(skills)} categories."
            },
            "strengths": strengths,
            "weaknesses": weaknesses,
            "skills_analysis": skills,
            "structure_analysis": structure,
            "improvement_suggestions": {
                "immediate_actions": [
                    "Review and update contact information",
                    "Ensure all major resume sections are present",
                    "Add missing skills to your skill section"
                ],
                "short_term_goals": [
                    f"Learn these recommended skills: {', '.join(skill_recommendations[:5])}",
                    "Add quantifiable achievements to experience section",
                    "Optimize resume length and formatting"
                ],
                "long_term_development": [
                    "Pursue relevant certifications",
                    "Build projects to demonstrate skills",
                    "Gain experience in trending technologies"
                ]
            },
            "recommended_skills": skill_recommendations,
            "resume_stats": {
                "word_count": word_count,
                "character_count": char_count,
                "sections_present": sum(structure.values()),
                "total_skills_found": sum(len(v) for v in skills.values())
            }
        }


def extract_text_from_resume_file(file_content, file_extension):
    """Extract text from uploaded resume file"""
    try:
        if file_extension.lower() == 'pdf':
            import fitz  # PyMuPDF
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name
            
            doc = fitz.open(tmp_file_path)
            text = ""
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text += page.get_text()
            doc.close()
            os.unlink(tmp_file_path)
            return text
            
        elif file_extension.lower() in ['docx', 'doc']:
            try:
                import docx2txt
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
                    tmp_file.write(file_content)
                    tmp_file_path = tmp_file.name
                
                text = docx2txt.process(tmp_file_path)
                os.unlink(tmp_file_path)
                return text
            except ImportError:
                return "Document processing library not available. Please install python-docx2txt."
        
        else:
            # Try to decode as text
            return file_content.decode('utf-8', errors='ignore')
            
    except Exception as e:
        return f"Error extracting text: {str(e)}"


def display_analysis_results(analysis_result: Dict):
    """Display comprehensive analysis results"""
    
    st.markdown("## 📊 Resume Analysis Results")
    
    # Score Dashboard
    col1, col2, col3 = st.columns(3)
    
    overall = analysis_result.get("overall_assessment", {})
    
    with col1:
        strength_score = overall.get("strength_score", "N/A")
        st.metric("Overall Strength", f"{strength_score}/10" if strength_score != "N/A" else "N/A")
    
    with col2:
        readability = overall.get("readability_score", "N/A")
        st.metric("Readability", f"{readability}/10" if readability != "N/A" else "N/A")
    
    with col3:
        ats_score = overall.get("ats_compatibility", "N/A")
        st.metric("Structure Score", f"{ats_score}/10" if ats_score != "N/A" else "N/A")
    
    # Summary
    if overall.get("summary"):
        st.info(overall["summary"])
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Strengths & Areas", 
        "🛠️ Skills Analysis", 
        "📋 Improvement Plan",
        "📊 Statistics"
    ])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("✅ Strengths")
            strengths = analysis_result.get("strengths", [])
            for strength in strengths:
                st.success(strength)
        
        with col2:
            st.subheader("⚠️ Areas for Improvement")
            weaknesses = analysis_result.get("weaknesses", [])
            for weakness in weaknesses:
                st.warning(weakness)
    
    with tab2:
        st.subheader("🎯 Skills Analysis")
        
        skills_analysis = analysis_result.get("skills_analysis", {})
        
        if isinstance(skills_analysis, dict):
            for category, skills in skills_analysis.items():
                if isinstance(skills, list) and skills:
                    st.write(f"**{category.replace('_', ' ').title()}:**")
                    for skill in skills:
                        st.write(f"  • {skill}")
                    st.write("")
        
        # Recommended skills
        recommended_skills = analysis_result.get("recommended_skills", [])
        if recommended_skills:
            st.subheader("💡 Recommended Skills to Learn")
            for skill in recommended_skills:
                st.write(f"🎯 {skill}")
    
    with tab3:
        st.subheader("🚀 Improvement Roadmap")
        
        improvements = analysis_result.get("improvement_suggestions", {})
        
        st.markdown("### ⚡ Immediate Actions")
        immediate = improvements.get("immediate_actions", [])
        for action in immediate:
            st.write(f"1. {action}")
        
        st.markdown("### 📅 Short-term Goals (1-3 months)")
        short_term = improvements.get("short_term_goals", [])
        for goal in short_term:
            st.write(f"• {goal}")
        
        st.markdown("### 🎯 Long-term Development (3-12 months)")
        long_term = improvements.get("long_term_development", [])
        for goal in long_term:
            st.write(f"• {goal}")
    
    with tab4:
        st.subheader("📈 Resume Statistics")
        
        stats = analysis_result.get("resume_stats", {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Word Count", stats.get("word_count", "N/A"))
            st.metric("Total Skills Found", stats.get("total_skills_found", "N/A"))
        
        with col2:
            st.metric("Character Count", stats.get("character_count", "N/A"))
            st.metric("Sections Present", stats.get("sections_present", "N/A"))
        
        # Structure analysis if available
        structure = analysis_result.get("structure_analysis", {})
        if structure:
            st.subheader("📋 Resume Structure")
            for section, present in structure.items():
                status = "✅" if present else "❌"
                st.write(f"{status} {section.replace('_', ' ').title()}")
        
        # Job match analysis if available
        job_match = analysis_result.get("job_match", {})
        if job_match and job_match.get('similarity_score', 0) > 0:
            st.subheader("🎯 Job Match Analysis")
            st.metric("Similarity Score", f"{job_match.get('similarity_score', 0)}%")
            
            matching_keywords = job_match.get('matching_keywords', [])
            missing_keywords = job_match.get('missing_keywords', [])
            
            if matching_keywords:
                st.write("**Matching Keywords:**", ", ".join(matching_keywords[:10]))
            
            if missing_keywords:
                st.write("**Missing Keywords:**", ", ".join(missing_keywords[:10]))
    
    # Export functionality
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        # Create downloadable report
        report_data = {
            "analysis_date": datetime.now().isoformat(),
            "analysis_result": analysis_result
        }
        
        report_json = json.dumps(report_data, indent=2)
        st.download_button(
            label="📥 Download Analysis Report",
            data=report_json,
            file_name=f"resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    with col2:
        if st.button("🔄 Analyze Another Resume"):
            st.rerun()


def enhanced_individual_analysis_page():
    """Enhanced individual analysis page with local NLP analysis (No API required)"""
    st.markdown('<h1 class="main-header">🔍 AI-Powered Resume Analysis</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <h3>🎯 Advanced Resume Analysis</h3>
    <p>Get comprehensive insights about your resume using advanced text processing and NLP techniques. 
    No external APIs required - all analysis is done locally!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Choose analyzer type
    st.subheader("⚙️ Choose Analysis Method")
    analyzer_type = st.radio(
        "Select the type of analysis you prefer:",
        ["🧠 Advanced NLP Analysis (Recommended)", "📊 Text Pattern Analysis"],
        help="Advanced NLP uses machine learning techniques, while Text Pattern uses rule-based analysis"
    )
    
    # Initialize analyzer
    try:
        with st.spinner("Initializing analyzer..."):
            if analyzer_type == "🧠 Advanced NLP Analysis (Recommended)":
                analyzer = ResumeAnalyzer()
            else:
                analyzer = TextAnalysisResumeAnalyzer()
            st.success("✅ Analyzer ready!")
    except Exception as e:
        st.error(f"❌ Error initializing analyzer: {str(e)}")
        st.info("💡 Try installing required packages: pip install nltk scikit-learn textstat")
        return
    
    # Get data from database (assuming these functions exist)
    try:
        jobs = get_job_descriptions()
        if st.session_state.user_role == "student":
            resumes = get_user_resumes(st.session_state.user_id)
        else:
            resumes = get_user_resumes()
    except:
        # Fallback for demo purposes
        jobs = []
        resumes = []
        st.info("📝 Upload a resume file below for analysis")
    
    # File upload option if no resumes in database
    uploaded_file = None
    if not resumes:
        st.subheader("📁 Upload Resume")
        uploaded_file = st.file_uploader(
            "Choose your resume file",
            type=['pdf', 'docx', 'doc', 'txt'],
            help="Supported formats: PDF, Word documents, and text files"
        )
    
    # File selection from database
    selected_resume_id = None
    selected_job_id = None
    
    if resumes:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📄 Select Resume")
            if st.session_state.get('user_role') == "student":
                resume_options = {f"{resume[1]} - {resume[2]}": resume[0] for resume in resumes}
            else:
                resume_options = {f"{resume[1]} ({resume[4]}) - {resume[2]}": resume[0] for resume in resumes}
            
            selected_resume = st.selectbox("Choose a resume", list(resume_options.keys()))
            selected_resume_id = resume_options.get(selected_resume)
        
        with col2:
            st.subheader("💼 Select Job (Optional)")
            job_options = {"No specific job": None}
            if jobs:
                job_options.update({f"{job[1]} - {job[2]}": job[0] for job in jobs})
            
            selected_job = st.selectbox("Choose a job description", list(job_options.keys()))
            selected_job_id = job_options.get(selected_job)
    
    # Analysis options
    st.subheader("🔧 Analysis Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        detailed_analysis = st.checkbox("📊 Detailed Statistics", value=True)
    
    with col2:
        include_recommendations = st.checkbox("💡 Include Recommendations", value=True)
    
    with col3:
        compare_job = st.checkbox("🎯 Compare with Job Description", value=bool(selected_job_id))
    
    # Analysis button
    if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
        resume_text = ""
        job_description = ""
        
        # Get resume content
        if uploaded_file:
            try:
                file_content = uploaded_file.read()
                file_extension = uploaded_file.name.split('.')[-1] if '.' in uploaded_file.name else 'txt'
                resume_text = extract_text_from_resume_file(file_content, file_extension)
            except Exception as e:
                st.error(f"❌ Error processing uploaded file: {str(e)}")
                return
        
        elif selected_resume_id:
            try:
                resume_content = get_file_from_db(selected_resume_id, "resume")
                if not resume_content:
                    st.error("❌ Could not retrieve resume content")
                    return
                
                resume_filename = [r[1] for r in resumes if r[0] == selected_resume_id][0]
                file_extension = resume_filename.split('.')[-1] if '.' in resume_filename else 'pdf'
                resume_text = extract_text_from_resume_file(resume_content, file_extension)
            except Exception as e:
                st.error(f"❌ Error retrieving resume: {str(e)}")
                return
        
        else:
            st.warning("⚠️ Please upload a resume file or select one from the database")
            return
        
        # Check if resume text extraction was successful
        if "Error" in resume_text:
            st.error(resume_text)
            return
        
        if len(resume_text.strip()) < 50:
            st.warning("⚠️ Resume text seems too short. Please check if the file was processed correctly.")
            with st.expander("📋 Show extracted text"):
                st.text_area("Extracted text preview:", resume_text[:500], height=100)
        
        # Get job description if selected and comparison is enabled
        if compare_job and selected_job_id:
            try:
                job_content = get_file_from_db(selected_job_id, "job")
                if job_content:
                    job_description = extract_text_from_resume_file(job_content, 'txt')
            except Exception as e:
                st.warning(f"⚠️ Could not load job description: {str(e)}")
        
        # Perform analysis
        with st.spinner("🔍 Analyzing your resume... This may take a moment."):
            try:
                analysis_result = analyzer.analyze_resume_comprehensively(resume_text, job_description)
                
                # Display results
                display_analysis_results(analysis_result)
                
                # Success message
                st.success("✅ Analysis completed successfully!")
                
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                st.info("💡 Please try again or contact support if the problem persists.")


# Alternative simple analyzer for basic text analysis
class SimpleResumeAnalyzer:
    """Simple resume analyzer using basic text processing"""
    
    def __init__(self):
        self.common_skills = [
            'python', 'java', 'javascript', 'html', 'css', 'sql', 'git',
            'react', 'angular', 'nodejs', 'django', 'flask', 'spring',
            'aws', 'azure', 'docker', 'kubernetes', 'jenkins',
            'machine learning', 'data analysis', 'project management',
            'leadership', 'teamwork', 'communication'
        ]
    
    def count_keywords(self, text: str, keywords: List[str]) -> Dict:
        """Count occurrences of keywords in text"""
        text_lower = text.lower()
        keyword_counts = {}
        
        for keyword in keywords:
            count = text_lower.count(keyword.lower())
            if count > 0:
                keyword_counts[keyword] = count
        
        return keyword_counts
    
    def basic_analysis(self, resume_text: str) -> Dict:
        """Perform basic resume analysis"""
        word_count = len(resume_text.split())
        char_count = len(resume_text)
        
        # Count skills
        skill_counts = self.count_keywords(resume_text, self.common_skills)
        total_skills = len(skill_counts)
        
        # Basic scoring
        length_score = min(10, word_count / 50)  # 1 point per 50 words, max 10
        skill_score = min(10, total_skills)  # 1 point per skill, max 10
        
        overall_score = (length_score + skill_score) / 2
        
        # Generate basic insights
        strengths = []
        weaknesses = []
        
        if total_skills >= 5:
            strengths.append(f"Good variety of skills mentioned ({total_skills} skills found)")
        
        if word_count >= 300:
            strengths.append("Appropriate resume length")
        
        if total_skills < 3:
            weaknesses.append("Few technical skills mentioned - consider adding more")
        
        if word_count < 200:
            weaknesses.append("Resume may be too short - add more details")
        
        return {
            "overall_assessment": {
                "strength_score": round(overall_score, 1),
                "readability_score": round(length_score, 1),
                "ats_compatibility": 7.0,  # Default score
                "summary": f"Basic analysis complete. Found {total_skills} skills in {word_count} words."
            },
            "strengths": strengths,
            "weaknesses": weaknesses,
            "skills_found": skill_counts,
            "resume_stats": {
                "word_count": word_count,
                "character_count": char_count,
                "skills_count": total_skills
            },
            "improvement_suggestions": {
                "immediate_actions": [
                    "Add more technical skills relevant to your field",
                    "Ensure resume length is between 300-600 words",
                    "Include quantifiable achievements"
                ],
                "short_term_goals": [
                    "Learn trending skills in your industry",
                    "Add projects that demonstrate your abilities",
                    "Get feedback from industry professionals"
                ],
                "long_term_development": [
                    "Pursue relevant certifications",
                    "Build a strong professional network",
                    "Keep resume updated with latest experiences"
                ]
            }
        }


# CSS for better styling
st.markdown("""
<style>
.main-header {
    color: #1f77b4;
    text-align: center;
    padding: 20px 0;
    border-bottom: 2px solid #1f77b4;
    margin-bottom: 30px;
}

.info-box {
    background-color: #f0f8ff;
    border-left: 5px solid #1f77b4;
    padding: 15px;
    margin: 20px 0;
    border-radius: 5px;
}

.metric-card {
    background-color: #ffffff;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    text-align: center;
}
</style>
""",  unsafe_allow_html=True)
def main():
    """Main application function"""
    init_session_state()
    
    # Check authentication flow
    if not st.session_state.authenticated:
        if st.session_state.selected_role is None:
            # Show character selection first
            character_selection_page()
        else:
            # Show login page after role selection
            login_page()
        return
    
    # Get selected page from sidebar (authenticated users only)
    selected_page = sidebar_navigation()
    st.session_state.page = selected_page
    
    # Route to appropriate page
    if selected_page == "Dashboard":
        dashboard_page()
    elif selected_page == "Upload Resume":
        upload_resume_page()
    elif selected_page == "View Jobs":
        view_jobs_page()
    elif selected_page == "Individual Analysis":
        individual_analysis_page()
    elif selected_page == "Batch Analysis":
        enhanced_individual_analysis_page()
    elif selected_page == "Manage Resumes":
        manage_resumes_page()
    elif selected_page == "Manage Jobs":
        manage_jobs_page()
    elif selected_page == "Individual Evaluation":
        individual_analysis_page()
    elif selected_page == "Batch Evaluation":
        batch_evaluation_page()  # NEW: Add the batch evaluation page
    elif selected_page == "System Statistics":
        system_statistics_page()

    else:
        dashboard_page()

if __name__ == "__main__":

    main()

















