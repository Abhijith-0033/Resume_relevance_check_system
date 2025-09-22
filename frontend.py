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
from datetime import datetime
import sqlite3
import requests
from pathlib import Path
# Import your backend system
try:
    from main1 import ResumeRelevanceSystem
    BACKEND_AVAILABLE = True
except ImportError:
    st.error("Backend system not found. Please ensure resume_relevance_system.py is in the same directory.")
    BACKEND_AVAILABLE = False

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

def perform_batch_evaluation():
    """Perform batch evaluation of all resumes against selected job"""
    
    # Get all resumes
    resumes = get_user_resumes()
    job_id = st.session_state.batch_job_id
    
    if not resumes:
        st.error("No resumes available for evaluation")
        return
    
    # Initialize progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    results = []
    
    try:
        # Initialize backend system
        system = init_backend_system()
        if not system:
            st.error("Backend system not available")
            return
        
        # Add job description to backend system first
        job_content = get_file_from_db(job_id, "job")
        if not job_content:
            st.error("Could not retrieve job description")
            return
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as job_tmp:
            job_tmp.write(job_content)
            job_tmp_path = job_tmp.name
        
        try:
            backend_job_id = system.add_job_description(
                job_tmp_path, 
                st.session_state.batch_company_name, 
                st.session_state.batch_job_title
            )
            
            if not backend_job_id:
                st.error("Failed to process job description")
                return
            
            # Process each resume
            total_resumes = len(resumes)
            
            for i, resume in enumerate(resumes):
                resume_id, name, email, uploaded_at, username = resume
                
                # Update progress
                progress = (i + 1) / total_resumes
                progress_bar.progress(progress)
                status_text.text(f"Evaluating resume {i + 1}/{total_resumes}: {name}")
                
                try:
                    # Get resume content from database
                    resume_content = get_file_from_db(resume_id, "resume")
                    
                    if resume_content:
                        # Save resume temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as resume_tmp:
                            resume_tmp.write(resume_content)
                            resume_tmp_path = resume_tmp.name
                        
                        try:
                            # Add resume to backend system
                            backend_resume_id = system.add_resume(resume_tmp_path, name, email)
                            
                            if backend_resume_id:
                                # Perform evaluation
                                evaluation = system.evaluate_resume(backend_resume_id, backend_job_id)
                                
                                if evaluation:
                                    # Add candidate info to results
                                    evaluation['candidate_name'] = name
                                    evaluation['candidate_email'] = email
                                    evaluation['username'] = username
                                    evaluation['resume_id'] = resume_id
                                    evaluation['uploaded_at'] = uploaded_at
                                    results.append(evaluation)
                        
                        finally:
                            os.unlink(resume_tmp_path)
                
                except Exception as e:
                    st.warning(f"Error evaluating {name}: {str(e)}")
                    continue
        
        finally:
            os.unlink(job_tmp_path)
        
        # Sort results by relevance score (highest first)
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Store results in session state
        st.session_state.batch_results = results
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        st.success(f"✅ Batch evaluation completed! Evaluated {len(results)} resumes.")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error during batch evaluation: {str(e)}")

def display_batch_results():
    """Display comprehensive batch evaluation results"""
    
    results = st.session_state.batch_results
    
    if not results:
        st.info("No evaluation results available")
        return
    
    st.markdown("---")
    st.markdown('<h2 class="main-header" style="margin-bottom: 1rem;">Batch Evaluation Results</h2>', unsafe_allow_html=True)
    
    # Summary statistics
    total_evaluated = len(results)
    high_fit = len([r for r in results if r['verdict'] == 'High'])
    medium_fit = len([r for r in results if r['verdict'] == 'Medium'])
    low_fit = len([r for r in results if r['verdict'] == 'Low'])
    avg_score = sum(r['relevance_score'] for r in results) / total_evaluated
    
    # Statistics cards
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #3b82f6;">
            <h4 style="margin: 0; color: #1e40af;">Total Evaluated</h4>
            <h2 style="margin: 0; color: #2563eb;">{total_evaluated}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #10b981;">
            <h4 style="margin: 0; color: #059669;">High Fit</h4>
            <h2 style="margin: 0; color: #10b981;">{high_fit}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #f59e0b;">
            <h4 style="margin: 0; color: #d97706;">Medium Fit</h4>
            <h2 style="margin: 0; color: #f59e0b;">{medium_fit}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #ef4444;">
            <h4 style="margin: 0; color: #dc2626;">Low Fit</h4>
            <h2 style="margin: 0; color: #ef4444;">{low_fit}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #8b5cf6;">
            <h4 style="margin: 0; color: #7c3aed;">Avg Score</h4>
            <h2 style="margin: 0; color: #8b5cf6;">{avg_score:.1f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Filter and sorting options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        verdict_filter = st.selectbox("Filter by Verdict", ["All", "High", "Medium", "Low"])
    
    with col2:
        min_score = st.slider("Minimum Score", 0, 100, 0)
    
    with col3:
        sort_option = st.selectbox("Sort by", ["Relevance Score (High to Low)", "Relevance Score (Low to High)", "Name (A-Z)", "Name (Z-A)"])
    
    # Apply filters
    filtered_results = results
    
    if verdict_filter != "All":
        filtered_results = [r for r in filtered_results if r['verdict'] == verdict_filter]
    
    filtered_results = [r for r in filtered_results if r['relevance_score'] >= min_score]
    
    # Apply sorting
    if sort_option == "Relevance Score (High to Low)":
        filtered_results.sort(key=lambda x: x['relevance_score'], reverse=True)
    elif sort_option == "Relevance Score (Low to High)":
        filtered_results.sort(key=lambda x: x['relevance_score'])
    elif sort_option == "Name (A-Z)":
        filtered_results.sort(key=lambda x: x['candidate_name'])
    elif sort_option == "Name (Z-A)":
        filtered_results.sort(key=lambda x: x['candidate_name'], reverse=True)
    
    st.markdown(f"**Showing {len(filtered_results)} of {total_evaluated} candidates**")
    
    # Export functionality
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export Results (JSON)", use_container_width=True):
            results_json = json.dumps(filtered_results, indent=2, default=str)
            st.download_button(
                label="Download JSON",
                data=results_json,
                file_name=f"batch_evaluation_{st.session_state.batch_job_id[:8]}.json",
                mime="application/json",
                key="export_json"
            )
    
    with col2:
        if st.button("📄 Export Summary (CSV)", use_container_width=True):
            import pandas as pd
            
            # Create summary DataFrame
            summary_data = []
            for result in filtered_results:
                summary_data.append({
                    'Name': result['candidate_name'],
                    'Email': result['candidate_email'],
                    'Username': result['username'],
                    'Score': result['relevance_score'],
                    'Verdict': result['verdict'],
                    'Hard Match': result['hard_match_score'],
                    'Soft Match': result['soft_match_score'],
                    'Missing Skills Count': len(result['missing_skills']),
                    'Upload Date': result['uploaded_at']
                })
            
            df = pd.DataFrame(summary_data)
            csv = df.to_csv(index=False)
            
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"batch_summary_{st.session_state.batch_job_id[:8]}.csv",
                mime="text/csv",
                key="export_csv"
            )
    
    st.markdown("---")
    
    # Detailed results list
    st.subheader("Detailed Results")
    
    for i, result in enumerate(filtered_results, 1):
        # Create expandable card for each candidate
        verdict_class = f"verdict-{result['verdict'].lower()}"
        
        with st.expander(f"#{i} {result['candidate_name']} - {result['relevance_score']}/100 ({result['verdict']} Fit)", expanded=False):
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Candidate information
                st.markdown(f"""
                **👤 Candidate Information:**
                - **Name:** {result['candidate_name']}
                - **Email:** {result['candidate_email']}
                - **Username:** {result['username']}
                - **Upload Date:** {result['uploaded_at'][:19]}
                
                **📊 Evaluation Scores:**
                - **Overall Score:** {result['relevance_score']}/100
                - **Hard Match:** {result['hard_match_score']}/100
                - **Soft Match:** {result['soft_match_score']}/100
                - **Verdict:** <span class="{verdict_class}">{result['verdict']} Fit</span>
                """, unsafe_allow_html=True)
            
            with col2:
                # Score visualization (simple progress bars)
                st.markdown("**Score Breakdown:**")
                st.progress(result['relevance_score'] / 100)
                st.caption(f"Overall: {result['relevance_score']}/100")
                
                st.progress(result['hard_match_score'] / 100)
                st.caption(f"Hard Match: {result['hard_match_score']}/100")
                
                st.progress(result['soft_match_score'] / 100)
                st.caption(f"Soft Match: {result['soft_match_score']}/100")
            
            # Missing skills
            missing_skills = result.get('missing_skills', [])
            if missing_skills:
                st.markdown(f"**❌ Missing Skills ({len(missing_skills)}):**")
                skills_text = ", ".join(missing_skills[:10])  # Show first 10
                if len(missing_skills) > 10:
                    skills_text += f" ... and {len(missing_skills) - 10} more"
                st.markdown(skills_text)
            else:
                st.markdown("**✅ All required skills matched!**")
            
            # Detailed feedback
            with st.expander("📝 Detailed Feedback", expanded=False):
                feedback_lines = result['feedback'].split('\n')
                for line in feedback_lines:
                    if line.strip():
                        if any(emoji in line for emoji in ['🎯', '✅', '❌', '💡', '📊']):
                            st.markdown(f"**{line}**")
                        else:
                            st.markdown(line)
            
            # Individual actions
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button(f"📧 Contact {result['candidate_name']}", key=f"contact_{result['resume_id']}"):
                    st.info(f"Contact: {result['candidate_email']}")
            
            with col2:
                if st.button(f"📄 View Resume Details", key=f"details_{result['resume_id']}"):
                    st.info("Resume details functionality can be added here")


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

# Option 1: Hardcode the API key directly in the code
GEMINI_API_KEY = "YOUR_ACTUAL_API_KEY_HERE"  # Replace with your actual API key

# Option 2: Use environment variable with fallback
# GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your_fallback_key_here')

# Option 3: Read from a config file
# import json
# try:
#     with open('config.json', 'r') as f:
#         config = json.load(f)
#     GEMINI_API_KEY = config['gemini_api_key']
# except:
#     GEMINI_API_KEY = "YOUR_FALLBACK_API_KEY_HERE"

class GeminiResumeAnalyzer:
    def __init__(self, api_key: str = None):
        """Initialize Gemini API analyzer"""
        # Use provided API key or fall back to hardcoded key
        self.api_key = api_key or GEMINI_API_KEY
        genai.configure(api_key=self.api_key)
        
        # Try different model names based on current API
        try:
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except:
            try:
                self.model = genai.GenerativeModel('gemini-1.5-pro')
            except:
                try:
                    self.model = genai.GenerativeModel('models/gemini-1.5-flash')
                except:
                    # Fallback to listing available models
                    self.model = self._get_available_model()
    
    def _get_available_model(self):
        """Get the first available model for text generation"""
        try:
            # List available models
            models = genai.list_models()
            
            # Find a model that supports generateContent
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    print(f"Using model: {model.name}")
                    return genai.GenerativeModel(model.name)
            
            # If no model found, raise error
            raise Exception("No compatible models found")
            
        except Exception as e:
            print(f"Error finding available models: {str(e)}")
            # Return a fallback that will show error gracefully
            return None
    
    def analyze_resume_comprehensively(self, resume_text: str, job_description: str = "") -> Dict:
        """Comprehensive resume analysis using Gemini AI"""
        
        if self.model is None:
            return self._get_fallback_analysis()
        
        analysis_prompt = f"""
        As an expert career counselor and resume analyst, provide a comprehensive analysis of the following resume. 
        
        RESUME CONTENT:
        {resume_text}
        
        JOB DESCRIPTION (if provided):
        {job_description}
        
        Please provide a detailed JSON response with the following structure:
        
        {{
            "overall_assessment": {{
                "strength_score": "1-10 rating",
                "readability_score": "1-10 rating", 
                "ats_compatibility": "1-10 rating",
                "summary": "Brief overall assessment"
            }},
            "strengths": [
                "List of resume strengths"
            ],
            "weaknesses": [
                "List of areas needing improvement"
            ],
            "missing_skills": [
                "Skills mentioned in job description but missing from resume"
            ],
            "skill_gaps": {{
                "technical_skills": ["specific technical skills to develop"],
                "soft_skills": ["soft skills to improve"],
                "certifications": ["relevant certifications to pursue"],
                "experience_areas": ["types of experience to gain"]
            }},
            "improvement_suggestions": {{
                "immediate_actions": [
                    "Actions to take in next 1-2 weeks"
                ],
                "short_term_goals": [
                    "Goals for next 1-3 months"
                ],
                "long_term_development": [
                    "Development plans for 3-12 months"
                ]
            }},
            "resume_optimization": {{
                "format_improvements": ["specific formatting suggestions"],
                "content_enhancements": ["content improvement suggestions"],
                "keyword_optimization": ["important keywords to include"],
                "section_recommendations": ["sections to add/modify"]
            }},
            "career_guidance": {{
                "recommended_roles": ["job roles that match current skills"],
                "career_progression": ["potential career advancement paths"],
                "skill_development_priority": ["ranked list of skills to develop first"],
                "networking_suggestions": ["professional networking recommendations"]
            }},
            "learning_resources": {{
                "online_courses": [
                    {{"platform": "course platform", "course": "course name", "skill": "target skill", "duration": "time estimate", "priority": "high/medium/low"}}
                ],
                "certifications": [
                    {{"certification": "cert name", "provider": "issuing body", "relevance": "why important", "timeline": "time to complete"}}
                ],
                "books_resources": [
                    {{"title": "resource title", "type": "book/blog/website", "focus_area": "skill area"}}
                ],
                "practical_projects": [
                    {{"project": "project idea", "skills_developed": ["skills"], "timeline": "completion time"}}
                ]
            }},
            "interview_preparation": {{
                "likely_questions": ["potential interview questions based on role"],
                "skill_demonstration": ["how to showcase skills in interview"],
                "portfolio_suggestions": ["what to include in portfolio"]
            }}
        }}
        
        Provide specific, actionable, and personalized recommendations. Focus on practical steps the person can take to improve their career prospects.
        """
        
        try:
            response = self.model.generate_content(analysis_prompt)
            
            # Extract JSON from response
            response_text = response.text
            
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                analysis_result = json.loads(json_match.group())
                return analysis_result
            else:
                # If JSON extraction fails, return structured response
                return self._parse_text_response(response_text)
                
        except Exception as e:
            print(f"Error with Gemini API: {str(e)}")
            return self._get_fallback_analysis()
    
    def generate_personalized_learning_path(self, skills_analysis: Dict, career_goals: str = "") -> Dict:
        """Generate personalized learning path using Gemini"""
        
        if self.model is None:
            return {"learning_path": "AI model not available for learning path generation."}
        
        learning_prompt = f"""
        Based on the following skill analysis, create a detailed learning path:
        
        SKILL ANALYSIS:
        {json.dumps(skills_analysis, indent=2)}
        
        CAREER GOALS:
        {career_goals}
        
        Create a comprehensive learning path with:
        
        1. IMMEDIATE PRIORITIES (Next 4 weeks):
        - Top 2 skills to focus on
        - Specific daily/weekly actions
        - Resources to start immediately
        
        2. SHORT-TERM DEVELOPMENT (1-3 months):
        - Skills to develop
        - Projects to complete
        - Certifications to pursue
        
        3. MEDIUM-TERM GOALS (3-6 months):
        - Advanced skills development
        - Professional experiences to gain
        - Network building activities
        
        4. LONG-TERM VISION (6-12 months):
        - Career advancement targets
        - Leadership skills development
        - Industry expertise building
        
        For each recommendation, include:
        - Specific resources (courses, books, platforms)
        - Time investment required
        - Success metrics
        - How it contributes to career goals
        
        Format as a practical, actionable roadmap.
        """
        
        try:
            response = self.model.generate_content(learning_prompt)
            return {"learning_path": response.text}
        except Exception as e:
            print(f"Error generating learning path: {str(e)}")
            return {"learning_path": "Unable to generate personalized learning path at this time."}
    
    def get_industry_insights(self, job_description: str, resume_text: str) -> Dict:
        """Get industry-specific insights and trends"""
        
        if self.model is None:
            return {"industry_insights": "AI model not available for industry insights."}
        
        insights_prompt = f"""
        Based on this job description and resume, provide industry insights:
        
        JOB DESCRIPTION:
        {job_description}
        
        RESUME:
        {resume_text}
        
        Provide insights on:
        
        1. Industry Trends:
        - Current hot skills in this field
        - Emerging technologies to watch
        - Skills becoming obsolete
        
        2. Salary Expectations:
        - Typical salary ranges for this role
        - Factors that influence compensation
        - Geographic considerations
        
        3. Career Progression:
        - Typical career paths in this field
        - Skills needed for advancement
        - Timeline for career growth
        
        4. Market Demand:
        - Job market outlook
        - Companies actively hiring
        - Remote work opportunities
        
        5. Professional Development:
        - Key conferences/events to attend
        - Professional organizations to join
        - Thought leaders to follow
        
        Keep insights current and actionable.
        """
        
        try:
            response = self.model.generate_content(insights_prompt)
            return {"industry_insights": response.text}
        except Exception as e:
            print(f"Error getting industry insights: {str(e)}")
            return {"industry_insights": "Unable to fetch industry insights at this time."}
    
    def _parse_text_response(self, response_text: str) -> Dict:
        """Parse text response when JSON extraction fails"""
        return {
            "overall_assessment": {
                "summary": "AI analysis completed - see detailed feedback below",
                "strength_score": "7",
                "readability_score": "7",
                "ats_compatibility": "7"
            },
            "detailed_analysis": response_text,
            "strengths": ["Analysis provided by AI"],
            "weaknesses": ["See detailed analysis"],
            "improvement_suggestions": {
                "immediate_actions": ["Review detailed AI analysis"],
                "short_term_goals": ["Follow AI recommendations"],
                "long_term_development": ["Implement suggested improvements"]
            }
        }
    
    def _get_fallback_analysis(self) -> Dict:
        """Fallback analysis when API fails"""
        return {
            "overall_assessment": {
                "summary": "Unable to connect to AI analysis service",
                "strength_score": "N/A",
                "readability_score": "N/A", 
                "ats_compatibility": "N/A"
            },
            "strengths": ["Resume uploaded successfully"],
            "weaknesses": ["AI analysis temporarily unavailable"],
            "improvement_suggestions": {
                "immediate_actions": ["Try analysis again later"],
                "short_term_goals": ["Review resume manually"],
                "long_term_development": ["Consider professional resume review"]
            },
            "error": "API service unavailable"
        }

# Simplified configuration function
def get_gemini_api_key():
    """Get Gemini API key - now uses hardcoded key"""
    return GEMINI_API_KEY

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

def display_gemini_analysis_results(analysis_result: Dict, learning_path: Dict = None, industry_insights: Dict = None):
    """Display comprehensive Gemini analysis results"""
    
    # Overall Assessment
    st.markdown("## 🔍 AI-Powered Resume Analysis")
    
    if "error" in analysis_result:
        st.error("AI analysis service is currently unavailable. Please try again later.")
        return
    
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
        st.metric("ATS Compatibility", f"{ats_score}/10" if ats_score != "N/A" else "N/A")
    
    # Summary
    if overall.get("summary"):
        st.info(overall["summary"])
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Strengths & Gaps", 
        "🎯 Improvement Plan", 
        "📚 Learning Resources",
        "🚀 Career Guidance",
        "📝 Resume Optimization",
        "🎤 Interview Prep"
    ])
    
    with tab1:
        st.subheader("Resume Strengths")
        strengths = analysis_result.get("strengths", [])
        for strength in strengths:
            st.success(f"✅ {strength}")
        
        st.subheader("Areas for Improvement")
        weaknesses = analysis_result.get("weaknesses", [])
        for weakness in weaknesses:
            st.warning(f"⚠️ {weakness}")
        
        # Skill gaps breakdown
        skill_gaps = analysis_result.get("skill_gaps", {})
        if skill_gaps:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Technical Skills to Develop")
                tech_skills = skill_gaps.get("technical_skills", [])
                for skill in tech_skills:
                    st.write(f"• {skill}")
                
                st.subheader("Certifications to Pursue")
                certs = skill_gaps.get("certifications", [])
                for cert in certs:
                    st.write(f"🏆 {cert}")
            
            with col2:
                st.subheader("Soft Skills to Improve")
                soft_skills = skill_gaps.get("soft_skills", [])
                for skill in soft_skills:
                    st.write(f"• {skill}")
                
                st.subheader("Experience Areas")
                exp_areas = skill_gaps.get("experience_areas", [])
                for area in exp_areas:
                    st.write(f"💼 {area}")
    
    with tab2:
        st.subheader("Your Personalized Improvement Plan")
        
        improvements = analysis_result.get("improvement_suggestions", {})
        
        st.markdown("### 🚀 Immediate Actions (Next 1-2 weeks)")
        immediate = improvements.get("immediate_actions", [])
        for action in immediate:
            st.write(f"1. {action}")
        
        st.markdown("### ⏰ Short-term Goals (1-3 months)")
        short_term = improvements.get("short_term_goals", [])
        for goal in short_term:
            st.write(f"• {goal}")
        
        st.markdown("### 🎯 Long-term Development (3-12 months)")
        long_term = improvements.get("long_term_development", [])
        for goal in long_term:
            st.write(f"• {goal}")
        
        # Display learning path if available
        if learning_path and learning_path.get("learning_path"):
            st.markdown("### 📋 Detailed Learning Roadmap")
            st.markdown(learning_path["learning_path"])
    
    with tab3:
        st.subheader("Curated Learning Resources")
        
        resources = analysis_result.get("learning_resources", {})
        
        # Online Courses
        courses = resources.get("online_courses", [])
        if courses:
            st.markdown("### 💻 Recommended Online Courses")
            for course in courses:
                with st.expander(f"{course.get('course', 'Course')} - {course.get('priority', 'Medium')} Priority"):
                    st.write(f"**Platform:** {course.get('platform', 'N/A')}")
                    st.write(f"**Target Skill:** {course.get('skill', 'N/A')}")
                    st.write(f"**Duration:** {course.get('duration', 'N/A')}")
        
        # Certifications
        certifications = resources.get("certifications", [])
        if certifications:
            st.markdown("### 🏆 Certification Recommendations")
            for cert in certifications:
                st.write(f"**{cert.get('certification', 'Certification')}**")
                st.write(f"Provider: {cert.get('provider', 'N/A')}")
                st.write(f"Relevance: {cert.get('relevance', 'N/A')}")
                st.write(f"Timeline: {cert.get('timeline', 'N/A')}")
                st.write("---")
        
        # Books and Resources
        books = resources.get("books_resources", [])
        if books:
            st.markdown("### 📚 Reading List")
            for book in books:
                st.write(f"• **{book.get('title', 'Resource')}** ({book.get('type', 'Resource')})")
                st.write(f"  Focus: {book.get('focus_area', 'General')}")
        
        # Practical Projects
        projects = resources.get("practical_projects", [])
        if projects:
            st.markdown("### 🛠️ Hands-on Projects")
            for project in projects:
                st.write(f"**Project:** {project.get('project', 'Project')}")
                st.write(f"Skills: {', '.join(project.get('skills_developed', []))}")
                st.write(f"Timeline: {project.get('timeline', 'N/A')}")
                st.write("---")
    
    with tab4:
        st.subheader("Career Development Guidance")
        
        career = analysis_result.get("career_guidance", {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 💼 Recommended Job Roles")
            roles = career.get("recommended_roles", [])
            for role in roles:
                st.write(f"• {role}")
            
            st.markdown("### 📈 Career Progression Paths")
            progression = career.get("career_progression", [])
            for path in progression:
                st.write(f"• {path}")
        
        with col2:
            st.markdown("### 🎯 Skill Development Priority")
            priorities = career.get("skill_development_priority", [])
            for i, skill in enumerate(priorities, 1):
                st.write(f"{i}. {skill}")
            
            st.markdown("### 🤝 Networking Suggestions")
            networking = career.get("networking_suggestions", [])
            for suggestion in networking:
                st.write(f"• {suggestion}")
        
        # Display industry insights if available
        if industry_insights and industry_insights.get("industry_insights"):
            st.markdown("### 🌟 Industry Insights & Trends")
            st.markdown(industry_insights["industry_insights"])
    
    with tab5:
        st.subheader("Resume Optimization Tips")
        
        optimization = analysis_result.get("resume_optimization", {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎨 Format Improvements")
            format_tips = optimization.get("format_improvements", [])
            for tip in format_tips:
                st.write(f"• {tip}")
            
            st.markdown("### 🔑 Keyword Optimization")
            keywords = optimization.get("keyword_optimization", [])
            for keyword in keywords:
                st.write(f"• {keyword}")
        
        with col2:
            st.markdown("### ✏️ Content Enhancements")
            content = optimization.get("content_enhancements", [])
            for enhancement in content:
                st.write(f"• {enhancement}")
            
            st.markdown("### 📋 Section Recommendations")
            sections = optimization.get("section_recommendations", [])
            for section in sections:
                st.write(f"• {section}")
    
    with tab6:
        st.subheader("Interview Preparation")
        
        interview = analysis_result.get("interview_preparation", {})
        
        st.markdown("### ❓ Likely Interview Questions")
        questions = interview.get("likely_questions", [])
        for question in questions:
            st.write(f"• {question}")
        
        st.markdown("### 🎯 How to Demonstrate Your Skills")
        demonstrations = interview.get("skill_demonstration", [])
        for demo in demonstrations:
            st.write(f"• {demo}")
        
        st.markdown("### 📁 Portfolio Suggestions")
        portfolio = interview.get("portfolio_suggestions", [])
        for suggestion in portfolio:
            st.write(f"• {suggestion}")
    
    # Export functionality
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📧 Email Analysis Report"):
            st.info("Email functionality coming soon!")
    
    with col2:
        # Create downloadable report
        report_data = {
            "analysis_date": datetime.now().isoformat(),
            "analysis_result": analysis_result,
            "learning_path": learning_path,
            "industry_insights": industry_insights
        }
        
        report_json = json.dumps(report_data, indent=2)
        st.download_button(
            label="📥 Download Full Report",
            data=report_json,
            file_name=f"ai_resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

def enhanced_individual_analysis_page():
    """Enhanced individual analysis page with Gemini AI - no manual API key required"""
    st.markdown('<h1 class="main-header">AI-Powered Resume Analysis</h1>', unsafe_allow_html=True)
    
    # Initialize analyzer with hardcoded API key
    try:
        with st.spinner("Initializing AI analyzer..."):
            analyzer = GeminiResumeAnalyzer()  # No need to pass API key
            if analyzer.model is None:
                st.error("Failed to initialize AI model. Please check your API key configuration.")
                return
            st.success("AI analyzer ready!")
    except Exception as e:
        st.error(f"Error initializing AI analyzer: {str(e)}")
        st.info("Please check your API key configuration in the code.")
        return
    
    # Get data from database
    jobs = get_job_descriptions()
    if st.session_state.user_role == "student":
        resumes = get_user_resumes(st.session_state.user_id)
    else:
        resumes = get_user_resumes()
    
    if not resumes:
        st.warning("No resumes available for analysis")
        return
    
    # File selection
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Select Resume")
        if st.session_state.user_role == "student":
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
        include_learning_path = st.checkbox("Generate Learning Path", value=True)
    
    with col2:
        include_industry_insights = st.checkbox("Include Industry Insights", value=True)
    
    with col3:
        career_goals = st.text_input("Career Goals (Optional)", placeholder="e.g., Senior Developer, Team Lead")
    
    # Analysis button
    if st.button("🚀 Start AI Analysis", type="primary", use_container_width=True):
        if selected_resume_id:
            with st.spinner("AI is analyzing your resume... This may take a few moments."):
                try:
                    # Get resume content
                    resume_content = get_file_from_db(selected_resume_id, "resume")
                    if not resume_content:
                        st.error("Could not retrieve resume content")
                        return
                    
                    # Extract text from resume
                    resume_filename = [r[1] for r in resumes if r[0] == selected_resume_id][0]
                    file_extension = resume_filename.split('.')[-1] if '.' in resume_filename else 'pdf'
                    resume_text = extract_text_from_resume_file(resume_content, file_extension)
                    
                    if "Error" in resume_text:
                        st.error(resume_text)
                        return
                    
                    if len(resume_text.strip()) < 50:
                        st.warning("Resume text seems too short. Please check if the file was processed correctly.")
                        st.text_area("Extracted text preview:", resume_text[:500], height=100)
                    
                    # Get job description if selected
                    job_description = ""
                    if selected_job_id:
                        job_content = get_file_from_db(selected_job_id, "job")
                        if job_content:
                            job_description = extract_text_from_resume_file(job_content, 'txt')
                    
                    # Perform AI analysis
                    analysis_result = analyzer.analyze_resume_comprehensively(resume_text, job_description)
                    
                    # Generate learning path if requested
                    learning_path = None
                    if include_learning_path:
                        skills_analysis = analysis_result.get("skill_gaps", {})
                        learning_path = analyzer.generate_personalized_learning_path(skills_analysis, career_goals)
                    
                    # Get industry insights if requested
                    industry_insights = None
                    if include_industry_insights and job_description:
                        industry_insights = analyzer.get_industry_insights(job_description, resume_text)
                    
                    # Display results
                    display_gemini_analysis_results(analysis_result, learning_path, industry_insights)
                    
                except Exception as e:
                    st.error(f"Error during AI analysis: {str(e)}")
                    st.info("Please try again or contact support if the problem persists.")
        else:
            st.warning("Please select a resume to analyze")

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
        enhanced_individual_analysis_page()
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

