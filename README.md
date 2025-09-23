# Resume_relevance_check_system
Resume Relevance System 🎯
An AI-powered career matching platform that helps students and placement cells analyze resume-job compatibility using advanced NLP and machine learning techniques.

🌟 Features
For Students 👨‍🎓
Resume Upload & Management: Upload and store multiple resumes with automatic contact extraction

Job Browsing: Explore available job opportunities from various companies

Individual Analysis: Get detailed AI-powered analysis of resume-job compatibility

Skill Gap Analysis: Identify missing skills and receive improvement recommendations

Match Scoring: Comprehensive scoring system with detailed feedback

For Placement Cells 🏢
Resume Management: View and manage all student resumes in the system

Job Description Management: Add and organize job descriptions from different companies

Batch Evaluation: Analyze multiple resumes against job descriptions simultaneously

System Analytics: Comprehensive statistics and reporting capabilities

Individual Evaluation: Detailed analysis of specific student-job matches

🚀 Quick Start
Prerequisites
Python 3.8+

Required packages (install via pip):

bash
pip install streamlit sqlite3 pandas plotly-express plotly nltk scikit-learn textstat pymupdf docx2txt requests
Installation
Clone or download the project files

Ensure all Python files are in the same directory

Required files: frontend.py, main1.py (backend system)

Install required packages:

bash
pip install -r requirements.txt
Download NLTK data:

python
import nltk
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('punkt_tab')
Run the application:

bash
streamlit run frontend.py
🔐 Login Credentials
Student Login
Username: abh33

Password: 12345678

Placement Cell Login
Username: placement

Password: 87654321

📋 System Architecture
Frontend
Streamlit-based web interface

Responsive design with professional styling

Real-time progress tracking

Interactive visualizations

Backend
SQLite database for data persistence

Local AI analyzers (no external API keys required)

Advanced NLP processing using NLTK and scikit-learn

File processing for PDF, DOCX, and text files

Analysis Components
Text Extraction: Automatic text extraction from various file formats

Skill Matching: Advanced pattern matching for technical and soft skills

ATS Compatibility: Resume structure and formatting analysis

Job Comparison: TF-IDF based similarity scoring

Recommendation Engine: Personalized improvement suggestions

🎯 How to Use
For Students
Login using student credentials

Upload Resume:

Upload PDF or DOCX files

Automatic contact information extraction

Multiple resume storage

Browse Jobs:

View available job descriptions

Search and filter opportunities

Analyze Matches:

Select resume and job for analysis

Get detailed compatibility scores

Receive improvement recommendations

For Placement Cells
Login using placement credentials

Manage Resumes:

View all student resumes

Search and filter functionality

Bulk operations

Manage Jobs:

Add new job descriptions

Upload files or manual entry

Organize by company and role

Batch Evaluation:

Select job description for analysis

Process multiple resumes simultaneously

Export results in multiple formats

System Analytics:

Comprehensive statistics dashboard

Activity trends and metrics

Exportable reports

🔧 Technical Features
File Processing
PDF Support: PyMuPDF for text extraction

DOCX Support: docx2txt for Word documents

Text Files: Direct processing with multiple encoding support

Error Handling: Robust file processing with fallback mechanisms

Analysis Methods
1. Advanced NLP Analyzer
Context-aware skill extraction

Experience quantification

ATS compatibility scoring

Job description similarity matching

2. Text Pattern Analyzer
Rule-based keyword matching

Structure analysis

Skill density calculations

Format compatibility checks

3. Simple Analyzer
Basic keyword counting

Length-based scoring

Quick analysis for large batches

Scoring System
Overall Score: Weighted combination of multiple factors

Strength Score: Technical and soft skill assessment

Readability Score: Content structure and clarity

ATS Score: Applicant Tracking System compatibility

Job Match Score: Relevance to specific job requirements

📊 Output Features
Individual Analysis
Visual Scorecards: Interactive gauges and metrics

Detailed Breakdown: Section-by-section analysis

Strengths & Weaknesses: Clear improvement areas

Recommendations: Actionable improvement suggestions

Export Options: JSON and text report downloads

Batch Evaluation
Progress Tracking: Real-time processing updates

Summary Statistics: Aggregate scores and metrics

Filtering & Sorting: Multiple view options

Export Formats: CSV and JSON for further analysis

Error Handling: Detailed failure reporting

🗃️ Database Schema
Main Tables
Students: User accounts and profiles

PlacementUsers: Placement officer accounts

Resumes: Student resume files and metadata

JobDescriptions: Job postings and descriptions

🔒 Security Features
Password Hashing: SHA-256 encryption

Session Management: Secure authentication flow

Data Isolation: Role-based access control

File Validation: Secure upload processing

🚨 Troubleshooting
Common Issues
Module Not Found Errors:

bash
pip install missing-package-name
NLTK Data Missing:

python
import nltk
nltk.download('required_data')
PDF Processing Errors:

Ensure PyMuPDF is installed: pip install PyMuPDF

Check file permissions and integrity

Database Connection Issues:

Verify database file exists and is accessible

Check file permissions in the application directory

Performance Tips
For Large Batches:

Use simpler analyzers for faster processing

Process during off-peak hours

Monitor system resources

File Size Considerations:

Optimal resume size: 100KB-2MB

Recommended format: PDF for best compatibility

Avoid scanned documents when possible

📈 Future Enhancements
Planned Features
Real-time Collaboration: Student-placement officer communication

Advanced Analytics: Machine learning-based predictions

Integration Support: LinkedIn and job portal APIs

Mobile Application: Native mobile app development

Multi-language Support: Internationalization features

Technical Roadmap
Cloud Deployment: AWS/Azure hosting options

API Development: RESTful API for external integrations

Advanced ML Models: Deep learning for better matching

Real-time Processing: WebSocket-based live updates

🤝 Contributing
This system is designed for educational and organizational use. For feature requests or bug reports, please contact the development team.

📄 License
This project is intended for educational and organizational use. Please ensure compliance with your institution's policies regarding data privacy and security.

Note: This system uses local processing and does not require external API keys. All analysis is performed on your local machine, ensuring data privacy and security.

For technical support or questions, please refer to the system documentation or contact your system administrator.
