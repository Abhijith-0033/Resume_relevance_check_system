# Automated Resume Relevance Check System
# Complete standalone Python application without FastAPI

import os
import json
import re
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import shutil

# File processing imports
try:
    import fitz  # For PDF processing
    PDF_AVAILABLE = True
except ImportError:
    print("PyMuPDF not available. PDF processing will be limited.")
    PDF_AVAILABLE = False

try:
    import docx2txt  # For DOCX processing
    DOCX_AVAILABLE = True
except ImportError:
    print("docx2txt not available. DOCX processing will be limited.")
    DOCX_AVAILABLE = False

# ML imports for semantic matching
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    ML_AVAILABLE = True
except ImportError:
    print("scikit-learn not available. Using basic keyword matching only.")
    ML_AVAILABLE = False

class ResumeRelevanceSystem:
    """
    Complete Automated Resume Relevance Check System
    
    Features:
    - Process PDF and DOCX files
    - Extract text and structured information
    - Generate 0-100 relevance scores
    - Provide High/Medium/Low verdicts
    - Store results in SQLite database
    - Handle thousands of resumes
    """
    
    def __init__(self, data_dir: str = "resume_data"):
        self.data_dir = Path(data_dir)
        self.resume_dir = self.data_dir / "resumes"
        self.jd_dir = self.data_dir / "job_descriptions" 
        self.results_dir = self.data_dir / "results"
        self.db_path = self.data_dir / "resume_system.db"
        
        # Create directories
        self._setup_directories()
        
        # Initialize database
        self._init_database()
        
        # Initialize ML components if available
        if ML_AVAILABLE:
            self.tfidf_vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 2),
                max_features=1000,
                lowercase=True
            )
        
        # Skill categories for matching
        self.skill_categories = {
            'programming': [
                'python', 'java', 'javascript', 'c++', 'c#', 'go', 'rust', 'php', 'ruby',
                'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl'
            ],
            'web_technologies': [
                'html', 'css', 'react', 'angular', 'vue', 'nodejs', 'django', 'flask',
                'express', 'spring', 'laravel', 'bootstrap', 'jquery', 'webpack'
            ],
            'databases': [
                'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
                'cassandra', 'oracle', 'sqlite', 'dynamodb'
            ],
            'cloud_technologies': [
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform',
                'ansible', 'microservices', 'serverless'
            ],
            'data_science': [
                'machine learning', 'deep learning', 'ai', 'tensorflow', 'pytorch',
                'pandas', 'numpy', 'scikit-learn', 'tableau', 'power bi', 'spark', 'hadoop'
            ],
            'mobile': [
                'android', 'ios', 'flutter', 'react native', 'xamarin', 'ionic'
            ],
            'tools': [
                'git', 'github', 'gitlab', 'jira', 'confluence', 'slack', 'trello',
                'vs code', 'intellij', 'eclipse'
            ]
        }
        
        print(f"✅ Resume Relevance System initialized successfully!")
        print(f"📂 Data directory: {self.data_dir}")
        print(f"🗄️ Database: {self.db_path}")
    
    def _setup_directories(self):
        """Create necessary directories"""
        directories = [self.data_dir, self.resume_dir, self.jd_dir, self.results_dir]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Resumes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resumes (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                candidate_name TEXT,
                candidate_email TEXT,
                file_path TEXT NOT NULL,
                extracted_text TEXT,
                parsed_data TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Job descriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_descriptions (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                company_name TEXT,
                role_title TEXT,
                file_path TEXT NOT NULL,
                extracted_text TEXT,
                parsed_requirements TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Evaluations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evaluations (
                id TEXT PRIMARY KEY,
                resume_id TEXT NOT NULL,
                jd_id TEXT NOT NULL,
                relevance_score REAL NOT NULL,
                verdict TEXT NOT NULL,
                hard_match_score REAL,
                soft_match_score REAL,
                missing_skills TEXT,
                feedback TEXT,
                evaluation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resume_id) REFERENCES resumes (id),
                FOREIGN KEY (jd_id) REFERENCES job_descriptions (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from PDF or DOCX file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        extension = file_path.suffix.lower()
        
        if extension == '.pdf':
            return self._extract_from_pdf(str(file_path))
        elif extension in ['.docx', '.doc']:
            return self._extract_from_docx(str(file_path))
        else:
            raise ValueError(f"Unsupported file format: {extension}")
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        if not PDF_AVAILABLE:
            raise ImportError("PyMuPDF not available. Install with: pip install PyMuPDF")
        
        try:
            doc = fitz.open(file_path)
            text = ""
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text += page.get_text()
            doc.close()
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting PDF: {str(e)}")
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        if not DOCX_AVAILABLE:
            raise ImportError("docx2txt not available. Install with: pip install docx2txt")
        
        try:
            text = docx2txt.process(file_path)
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting DOCX: {str(e)}")
    
    def parse_resume(self, text: str) -> Dict[str, Any]:
        """Parse resume text and extract structured information"""
        parsed_data = {
            'contact_info': self._extract_contact_info(text),
            'skills': self._extract_skills(text),
            'experience': self._extract_experience(text),
            'education': self._extract_education(text),
            'projects': self._extract_projects(text),
            'certifications': self._extract_certifications(text)
        }
        return parsed_data
    
    def parse_job_description(self, text: str) -> Dict[str, Any]:
        """Parse job description and extract requirements"""
        parsed_data = {
            'role_title': self._extract_role_title(text),
            'required_skills': self._extract_required_skills(text),
            'preferred_skills': self._extract_preferred_skills(text),
            'experience_required': self._extract_experience_requirements(text),
            'education_requirements': self._extract_education_requirements(text),
            'responsibilities': self._extract_responsibilities(text)
        }
        return parsed_data
    
    def _extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information from resume"""
        contact_info = {}
        
        # Email extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        contact_info['email'] = emails[0] if emails else ""
        
        # Phone extraction (Indian format)
        phone_patterns = [
            r'(\+91|91)?[-.\s]?[6-9]\d{9}',
            r'\b[6-9]\d{9}\b'
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                contact_info['phone'] = phones[0]
                break
        else:
            contact_info['phone'] = ""
        
        # LinkedIn extraction
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin = re.findall(linkedin_pattern, text, re.IGNORECASE)
        contact_info['linkedin'] = linkedin[0] if linkedin else ""
        
        return contact_info
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from text"""
        found_skills = set()
        text_lower = text.lower()
        
        # Check all skill categories
        for category, skills in self.skill_categories.items():
            for skill in skills:
                if skill.lower() in text_lower:
                    found_skills.add(skill.title())
        
        # Additional skill patterns
        skill_section = re.search(r'skills?\s*:?\s*(.*?)(?=\n\n|\nexperience|\neducation|$)', 
                                text, re.IGNORECASE | re.DOTALL)
        
        if skill_section:
            skill_text = skill_section.group(1)
            # Extract comma-separated skills
            additional_skills = re.findall(r'\b[A-Za-z][A-Za-z0-9+#.\s]{1,20}\b', skill_text)
            for skill in additional_skills:
                skill = skill.strip()
                if len(skill) > 2 and not skill.isdigit():
                    found_skills.add(skill.title())
        
        return list(found_skills)
    
    def _extract_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience"""
        experience = []
        
        # Look for experience patterns
        exp_patterns = [
            r'(\d{4})\s*[-–]\s*(\d{4}|\bpresent\b|\bcurrent\b)',
            r'(\w+\s+\d{4})\s*[-–]\s*(\w+\s+\d{4}|\bpresent\b|\bcurrent\b)'
        ]
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            for pattern in exp_patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                if matches:
                    # Extract company and position
                    position_company = line.strip()
                    description = ""
                    
                    # Look for description in next few lines
                    for j in range(i + 1, min(i + 4, len(lines))):
                        if lines[j].strip() and not re.search(r'\d{4}', lines[j]):
                            description += lines[j].strip() + " "
                    
                    experience.append({
                        'position_company': position_company,
                        'duration': f"{matches[0][0]} - {matches[0][1]}",
                        'description': description.strip()
                    })
                    break
        
        return experience[:5]  # Limit to 5 most recent
    
    def _extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information"""
        education = []
        
        edu_keywords = [
            'bachelor', 'master', 'phd', 'diploma', 'b.tech', 'm.tech', 'b.sc', 'm.sc',
            'mba', 'bba', 'be', 'me', 'b.com', 'm.com', 'bca', 'mca'
        ]
        
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in edu_keywords):
                year = self._extract_year(line)
                education.append({
                    'degree': line.strip(),
                    'year': year
                })
        
        return education
    
    def _extract_projects(self, text: str) -> List[str]:
        """Extract project information"""
        projects = []
        
        # Look for project sections
        project_section = re.search(r'projects?\s*:?\s*(.*?)(?=\n\n|\n[A-Z]|\ncertification|$)', 
                                  text, re.IGNORECASE | re.DOTALL)
        
        if project_section:
            project_text = project_section.group(1)
            # Split by bullet points, numbers, or line breaks
            project_lines = re.split(r'[•\-*]\s*|\d+\.\s*|\n', project_text)
            
            for project in project_lines:
                project = project.strip()
                if len(project) > 30:  # Meaningful project descriptions
                    projects.append(project)
        
        return projects[:10]  # Limit to 10 projects
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications"""
        certifications = []
        
        cert_keywords = [
            'certified', 'certification', 'certificate', 'aws', 'azure', 'google',
            'microsoft', 'oracle', 'cisco', 'comptia', 'pmp', 'scrum'
        ]
        
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in cert_keywords):
                if len(line.strip()) > 10:  # Meaningful certification
                    certifications.append(line.strip())
        
        return certifications
    
    def _extract_role_title(self, text: str) -> str:
        """Extract role title from job description"""
        lines = text.split('\n')
        for line in lines[:5]:
            if any(keyword in line.lower() for keyword in 
                  ['developer', 'engineer', 'analyst', 'manager', 'specialist', 
                   'consultant', 'architect', 'lead', 'senior', 'junior']):
                return line.strip()
        
        # Fallback to first non-empty line
        for line in lines[:3]:
            if line.strip():
                return line.strip()
        
        return "Software Role"
    
    def _extract_required_skills(self, text: str) -> List[str]:
        """Extract required skills from job description"""
        required_skills = set()
        text_lower = text.lower()
        
        # Look for required/mandatory sections
        required_section = re.search(
            r'(required|must have|essential|mandatory|qualifications)(.*?)(?=preferred|nice to have|good to have|\n\n|responsibilities|$)',
            text, re.IGNORECASE | re.DOTALL
        )
        
        search_text = required_section.group(2) if required_section else text
        
        # Check all skill categories
        for category, skills in self.skill_categories.items():
            for skill in skills:
                if skill.lower() in search_text.lower():
                    required_skills.add(skill.title())
        
        return list(required_skills)
    
    def _extract_preferred_skills(self, text: str) -> List[str]:
        """Extract preferred skills from job description"""
        preferred_skills = set()
        
        # Look for preferred sections
        preferred_section = re.search(
            r'(preferred|nice to have|good to have|plus|bonus|additional)(.*?)(?=\n\n|\nresponsibilities|\nqualifications|$)',
            text, re.IGNORECASE | re.DOTALL
        )
        
        if preferred_section:
            search_text = preferred_section.group(2)
            
            # Check all skill categories
            for category, skills in self.skill_categories.items():
                for skill in skills:
                    if skill.lower() in search_text.lower():
                        preferred_skills.add(skill.title())
        
        return list(preferred_skills)
    
    def _extract_experience_requirements(self, text: str) -> Dict[str, Any]:
        """Extract experience requirements"""
        exp_pattern = r'(\d+)[-+\s]*years?\s*(?:of\s*)?(?:experience|exp)'
        matches = re.findall(exp_pattern, text, re.IGNORECASE)
        
        if matches:
            years = [int(match) for match in matches]
            min_years = min(years)
            max_years = max(years)
            
            return {
                'minimum_years': min_years,
                'maximum_years': max_years,
                'description': f"{min_years}+ years of experience required"
            }
        
        return {
            'minimum_years': 0,
            'maximum_years': 10,
            'description': "Experience level not specified"
        }
    
    def _extract_education_requirements(self, text: str) -> List[str]:
        """Extract education requirements"""
        education_req = []
        
        edu_keywords = [
            'bachelor', 'master', 'phd', 'diploma', 'b.tech', 'm.tech',
            'b.sc', 'm.sc', 'mba', 'degree', 'graduate'
        ]
        
        text_lower = text.lower()
        for keyword in edu_keywords:
            if keyword in text_lower:
                education_req.append(keyword.title())
        
        return list(set(education_req))
    
    def _extract_responsibilities(self, text: str) -> List[str]:
        """Extract job responsibilities"""
        responsibilities = []
        
        # Look for responsibilities section
        resp_section = re.search(
            r'(responsibilities|duties|role|what you.*do)(.*?)(?=requirements|qualifications|skills|\n\n|$)',
            text, re.IGNORECASE | re.DOTALL
        )
        
        if resp_section:
            resp_text = resp_section.group(2)
            # Split by bullet points, numbers, or line breaks
            resp_lines = re.split(r'[•\-*]\s*|\d+\.\s*|\n', resp_text)
            
            for resp in resp_lines:
                resp = resp.strip()
                if len(resp) > 20:  # Meaningful responsibilities
                    responsibilities.append(resp)
        
        return responsibilities[:10]  # Limit to 10 responsibilities
    
    def _extract_year(self, text: str) -> str:
        """Extract year from text"""
        year_pattern = r'\b(19|20)\d{2}\b'
        years = re.findall(year_pattern, text)
        return years[-1] if years else ""
    
    def calculate_relevance_score(self, resume_data: Dict, jd_data: Dict, resume_text: str, jd_text: str) -> Dict[str, Any]:
        """
        Calculate comprehensive relevance score (0-100)
        
        Scoring Components:
        - Hard Match (60%): Skills, Experience, Education, Projects
        - Soft Match (40%): Semantic similarity using TF-IDF
        """
        
        # Calculate hard match score
        hard_score = self._calculate_hard_match(resume_data, jd_data)
        
        # Calculate soft match score  
        soft_score = self._calculate_soft_match(resume_text, jd_text)
        
        # Weighted final score
        final_score = (hard_score * 0.6) + (soft_score * 0.4)
        
        # Determine verdict
        verdict = self._get_verdict(final_score)
        
        # Identify missing skills
        missing_skills = self._identify_missing_skills(resume_data, jd_data)
        
        return {
            'final_score': round(final_score, 2),
            'hard_match_score': round(hard_score, 2),
            'soft_match_score': round(soft_score, 2),
            'verdict': verdict,
            'missing_skills': missing_skills
        }
    
    def _calculate_hard_match(self, resume_data: Dict, jd_data: Dict) -> float:
        """Calculate hard match score based on structured data matching"""
        
        total_score = 0.0
        
        # Skills matching (50% of hard match)
        skills_score = self._match_skills(
            resume_data.get('skills', []),
            jd_data.get('required_skills', []) + jd_data.get('preferred_skills', [])
        )
        total_score += skills_score * 0.5
        
        # Experience matching (25% of hard match)
        exp_score = self._match_experience(
            resume_data.get('experience', []),
            jd_data.get('experience_required', {})
        )
        total_score += exp_score * 0.25
        
        # Education matching (15% of hard match)
        edu_score = self._match_education(
            resume_data.get('education', []),
            jd_data.get('education_requirements', [])
        )
        total_score += edu_score * 0.15
        
        # Projects/Certifications matching (10% of hard match)
        project_cert_score = self._match_projects_certifications(
            resume_data.get('projects', []) + resume_data.get('certifications', []),
            jd_data.get('required_skills', [])
        )
        total_score += project_cert_score * 0.1
        
        return min(total_score, 100.0)
    
    def _calculate_soft_match(self, resume_text: str, jd_text: str) -> float:
        """Calculate soft match using semantic similarity"""
        
        if not ML_AVAILABLE:
            # Fallback to simple keyword overlap
            return self._simple_text_similarity(resume_text, jd_text)
        
        try:
            # Prepare texts
            texts = [resume_text.lower(), jd_text.lower()]
            
            # Calculate TF-IDF similarity
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
            similarity = similarity_matrix[0][0]
            
            return similarity * 100
        except Exception as e:
            print(f"Error in soft match calculation: {e}")
            return self._simple_text_similarity(resume_text, jd_text)
    
    def _simple_text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity based on word overlap"""
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return (intersection / union) * 100
    
    def _match_skills(self, resume_skills: List[str], required_skills: List[str]) -> float:
        """Match skills between resume and requirements"""
        if not required_skills:
            return 80.0  # Default score if no requirements
        
        if not resume_skills:
            return 0.0
        
        resume_skills_lower = [skill.lower() for skill in resume_skills]
        required_skills_lower = [skill.lower() for skill in required_skills]
        
        matched_count = 0
        for req_skill in required_skills_lower:
            for res_skill in resume_skills_lower:
                if req_skill in res_skill or res_skill in req_skill:
                    matched_count += 1
                    break
        
        match_percentage = (matched_count / len(required_skills)) * 100
        return min(match_percentage, 100.0)
    
    def _match_experience(self, resume_exp: List[Dict], exp_requirements: Dict) -> float:
        """Match experience requirements"""
        if not exp_requirements:
            return 70.0  # Default score
        
        min_required_years = exp_requirements.get('minimum_years', 0)
        
        # Estimate years from resume experience entries
        estimated_years = len(resume_exp)  # Simple estimation
        
        if estimated_years >= min_required_years:
            return 100.0
        elif estimated_years >= min_required_years * 0.7:
            return 80.0
        elif estimated_years >= min_required_years * 0.4:
            return 60.0
        else:
            return 30.0
    
    def _match_education(self, resume_edu: List[Dict], edu_requirements: List[str]) -> float:
        """Match education requirements"""
        if not edu_requirements:
            return 80.0  # Default score
        
        if not resume_edu:
            return 20.0  # Low score for missing education
        
        resume_degrees = [edu.get('degree', '').lower() for edu in resume_edu]
        
        for req_edu in edu_requirements:
            for res_degree in resume_degrees:
                if req_edu.lower() in res_degree:
                    return 100.0
        
        # Partial match for any degree
        return 60.0
    
    def _match_projects_certifications(self, projects_certs: List[str], required_skills: List[str]) -> float:
        """Match projects and certifications with required skills"""
        if not projects_certs:
            return 40.0  # Default score
        
        if not required_skills:
            return 80.0  # If no specific requirements, having projects is good
        
        # Check for skill overlap in projects/certifications
        projects_text = ' '.join(projects_certs).lower()
        skill_matches = 0
        
        for skill in required_skills:
            if skill.lower() in projects_text:
                skill_matches += 1
        
        if skill_matches > 0:
            return min((skill_matches / len(required_skills)) * 100, 100.0)
        
        return 50.0  # Some credit for having projects/certifications
    
    def _identify_missing_skills(self, resume_data: Dict, jd_data: Dict) -> List[str]:
        """Identify skills missing from resume"""
        resume_skills = [skill.lower() for skill in resume_data.get('skills', [])]
        required_skills = jd_data.get('required_skills', [])
        
        missing_skills = []
        
        for req_skill in required_skills:
            skill_found = False
            for res_skill in resume_skills:
                if req_skill.lower() in res_skill or res_skill in req_skill.lower():
                    skill_found = True
                    break
            
            if not skill_found:
                missing_skills.append(req_skill)
        
        return missing_skills
    
    def _get_verdict(self, score: float) -> str:
        """Get verdict based on score"""
        if score >= 80:
            return "High"
        elif score >= 50:
            return "Medium"
        else:
            return "Low"
    
    def generate_feedback(self, resume_data: Dict, jd_data: Dict, evaluation: Dict) -> str:
        """Generate personalized feedback for the candidate"""
        
        feedback_sections = []
        
        # Overall assessment
        score = evaluation['final_score']
        verdict = evaluation['verdict']
        
        feedback_sections.append(f"🎯 OVERALL ASSESSMENT")
        feedback_sections.append(f"Relevance Score: {score}/100 ({verdict} Fit)")
        feedback_sections.append(f"Hard Match: {evaluation['hard_match_score']}/100")
        feedback_sections.append(f"Soft Match: {evaluation['soft_match_score']}/100")
        feedback_sections.append("")
        
        # Strengths
        strengths = self._identify_strengths(resume_data, jd_data, evaluation)
        if strengths:
            feedback_sections.append("✅ STRENGTHS:")
            for i, strength in enumerate(strengths, 1):
                feedback_sections.append(f"{i}. {strength}")
            feedback_sections.append("")
        
        # Missing skills
        missing_skills = evaluation.get('missing_skills', [])
        if missing_skills:
            feedback_sections.append("❌ MISSING SKILLS:")
            for i, skill in enumerate(missing_skills[:10], 1):  # Top 10
                feedback_sections.append(f"{i}. {skill}")
            feedback_sections.append("")
        
        # Improvement recommendations
        recommendations = self._generate_recommendations(resume_data, jd_data, evaluation)
        if recommendations:
            feedback_sections.append("💡 IMPROVEMENT RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                feedback_sections.append(f"{i}. {rec}")
            feedback_sections.append("")
        
        # Score breakdown
        feedback_sections.append("📊 SCORE BREAKDOWN:")
        feedback_sections.append(f"• Skills Match: Primary factor in evaluation")
        feedback_sections.append(f"• Experience Match: {evaluation.get('hard_match_score', 0):.1f}% hard match")
        feedback_sections.append(f"• Semantic Match: {evaluation.get('soft_match_score', 0):.1f}% content similarity")
        
        return "\n".join(feedback_sections)
    
    def _identify_strengths(self, resume_data: Dict, jd_data: Dict, evaluation: Dict) -> List[str]:
        """Identify candidate's strengths"""
        strengths = []
        
        # Skills strengths
        resume_skills = resume_data.get('skills', [])
        required_skills = jd_data.get('required_skills', [])
        
        matching_skills = []
        for req_skill in required_skills:
            for res_skill in resume_skills:
                if req_skill.lower() in res_skill.lower() or res_skill.lower() in req_skill.lower():
                    matching_skills.append(res_skill)
                    break
        
        if matching_skills:
            strengths.append(f"Strong technical skills: {', '.join(matching_skills[:5])}")
        
        # Experience strengths
        experience = resume_data.get('experience', [])
        if len(experience) >= 2:
            strengths.append(f"Relevant work experience: {len(experience)} professional roles")
        
        # Education strengths
        education = resume_data.get('education', [])
        edu_requirements = jd_data.get('education_requirements', [])
        
        if education and edu_requirements:
            for edu in education:
                degree = edu.get('degree', '').lower()
                if any(req.lower() in degree for req in edu_requirements):
                    strengths.append("Meets educational requirements")
                    break
        
        # Projects strengths
        projects = resume_data.get('projects', [])
        if len(projects) >= 3:
            strengths.append(f"Strong project portfolio: {len(projects)} documented projects")
        
        # Certifications strengths
        certifications = resume_data.get('certifications', [])
        if certifications:
            strengths.append(f"Professional certifications: {len(certifications)} credentials")
        
        return strengths[:5]  # Top 5 strengths
    
    def _generate_recommendations(self, resume_data: Dict, jd_data: Dict, evaluation: Dict) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        missing_skills = evaluation.get('missing_skills', [])
        score = evaluation['final_score']
        
        # Skill-specific recommendations
        skill_learning_map = {
            'python': "Learn Python through online courses (Coursera, edX) and practice on HackerRank",
            'javascript': "Master JavaScript fundamentals and build interactive web projects",
            'react': "Complete React.js tutorials and create responsive web applications",
            'angular': "Learn Angular framework and develop single-page applications",
            'node.js': "Study Node.js for backend development and build REST APIs",
            'sql': "Practice SQL queries on platforms like SQLBolt and LeetCode",
            'aws': "Pursue AWS certification starting with Cloud Practitioner",
            'docker': "Learn containerization through hands-on Docker projects",
            'kubernetes': "Study container orchestration and deploy applications on Kubernetes",
            'machine learning': "Complete ML courses and work on data science projects",
            'java': "Master Java programming and object-oriented concepts",
            'spring': "Learn Spring framework for enterprise Java applications",
            'mongodb': "Study NoSQL databases and practice with MongoDB",
            'git': "Master version control with Git and collaborate on GitHub"
        }
        
        # Add skill-specific recommendations
        for skill in missing_skills[:5]:  # Top 5 missing skills
            skill_lower = skill.lower()
            if skill_lower in skill_learning_map:
                recommendations.append(skill_learning_map[skill_lower])
            else:
                recommendations.append(f"Develop {skill} skills through online courses and practical projects")
        
        # General recommendations based on score
        if score < 40:
            recommendations.extend([
                "Focus on building fundamental technical skills mentioned in job requirements",
                "Create a portfolio of 3-5 relevant projects demonstrating your abilities",
                "Consider formal training or certification in core technologies",
                "Join online coding communities and participate in open-source projects"
            ])
        elif score < 60:
            recommendations.extend([
                "Enhance your resume with specific project details and quantifiable achievements",
                "Gain practical experience through internships or freelance projects",
                "Develop domain-specific knowledge in your target industry"
            ])
        elif score < 80:
            recommendations.extend([
                "Fine-tune your skills in advanced areas of your expertise",
                "Contribute to open-source projects to demonstrate collaboration skills",
                "Consider specialization in emerging technologies relevant to the role"
            ])
        else:
            recommendations.extend([
                "You're a strong candidate! Focus on showcasing your achievements",
                "Prepare for behavioral interviews and technical discussions",
                "Stay updated with latest industry trends and best practices"
            ])
        
        return recommendations[:8]  # Top 8 recommendations
    
    def add_resume(self, file_path: str, candidate_name: str = "", candidate_email: str = "") -> str:
        """Add a resume to the system and return resume ID"""
        
        try:
            # Copy file to resume directory
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Resume file not found: {file_path}")
            
            # Generate unique filename
            resume_id = str(uuid.uuid4())
            new_filename = f"{resume_id}_{file_path.name}"
            new_file_path = self.resume_dir / new_filename
            
            shutil.copy2(file_path, new_file_path)
            
            # Extract text
            extracted_text = self.extract_text_from_file(str(new_file_path))
            
            # Parse resume
            parsed_data = self.parse_resume(extracted_text)
            
            # Extract candidate info if not provided
            if not candidate_name:
                # Try to extract name from contact info or filename
                contact_info = parsed_data.get('contact_info', {})
                candidate_email = contact_info.get('email', candidate_email)
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO resumes (id, filename, candidate_name, candidate_email, file_path, extracted_text, parsed_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (resume_id, file_path.name, candidate_name, candidate_email, 
                  str(new_file_path), extracted_text, json.dumps(parsed_data)))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Resume added successfully!")
            print(f"📄 File: {file_path.name}")
            print(f"🆔 Resume ID: {resume_id}")
            print(f"📧 Email: {candidate_email}")
            print(f"🔍 Skills found: {len(parsed_data.get('skills', []))}")
            
            return resume_id
            
        except Exception as e:
            print(f"❌ Error adding resume: {str(e)}")
            return ""
    
    def add_job_description(self, file_path: str, company_name: str = "", role_title: str = "") -> str:
        """Add a job description to the system and return JD ID"""
        
        try:
            # Copy file to JD directory
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Job description file not found: {file_path}")
            
            # Generate unique filename
            jd_id = str(uuid.uuid4())
            new_filename = f"{jd_id}_{file_path.name}"
            new_file_path = self.jd_dir / new_filename
            
            shutil.copy2(file_path, new_file_path)
            
            # Extract text
            extracted_text = self.extract_text_from_file(str(new_file_path))
            
            # Parse job description
            parsed_data = self.parse_job_description(extracted_text)
            
            # Extract info if not provided
            if not role_title:
                role_title = parsed_data.get('role_title', 'Software Role')
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO job_descriptions (id, filename, company_name, role_title, file_path, extracted_text, parsed_requirements)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (jd_id, file_path.name, company_name, role_title,
                  str(new_file_path), extracted_text, json.dumps(parsed_data)))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Job description added successfully!")
            print(f"📄 File: {file_path.name}")
            print(f"🆔 JD ID: {jd_id}")
            print(f"🏢 Company: {company_name}")
            print(f"💼 Role: {role_title}")
            print(f"🔍 Required skills: {len(parsed_data.get('required_skills', []))}")
            
            return jd_id
            
        except Exception as e:
            print(f"❌ Error adding job description: {str(e)}")
            return ""
    
    def evaluate_resume(self, resume_id: str, jd_id: str) -> Dict[str, Any]:
        """Evaluate a specific resume against a job description"""
        
        try:
            # Get resume and JD from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get resume data
            cursor.execute('SELECT extracted_text, parsed_data FROM resumes WHERE id = ?', (resume_id,))
            resume_row = cursor.fetchone()
            
            if not resume_row:
                raise ValueError(f"Resume not found: {resume_id}")
            
            resume_text, resume_parsed_json = resume_row
            resume_data = json.loads(resume_parsed_json)
            
            # Get JD data
            cursor.execute('SELECT extracted_text, parsed_requirements FROM job_descriptions WHERE id = ?', (jd_id,))
            jd_row = cursor.fetchone()
            
            if not jd_row:
                raise ValueError(f"Job description not found: {jd_id}")
            
            jd_text, jd_parsed_json = jd_row
            jd_data = json.loads(jd_parsed_json)
            
            conn.close()
            
            # Calculate relevance score
            evaluation = self.calculate_relevance_score(resume_data, jd_data, resume_text, jd_text)
            
            # Generate feedback
            feedback = self.generate_feedback(resume_data, jd_data, evaluation)
            
            # Save evaluation
            evaluation_id = str(uuid.uuid4())
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO evaluations (id, resume_id, jd_id, relevance_score, verdict, 
                                       hard_match_score, soft_match_score, missing_skills, feedback)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (evaluation_id, resume_id, jd_id, evaluation['final_score'], 
                  evaluation['verdict'], evaluation['hard_match_score'], 
                  evaluation['soft_match_score'], json.dumps(evaluation['missing_skills']), feedback))
            
            conn.commit()
            conn.close()
            
            # Prepare result
            result = {
                'evaluation_id': evaluation_id,
                'resume_id': resume_id,
                'jd_id': jd_id,
                'relevance_score': evaluation['final_score'],
                'verdict': evaluation['verdict'],
                'hard_match_score': evaluation['hard_match_score'],
                'soft_match_score': evaluation['soft_match_score'],
                'missing_skills': evaluation['missing_skills'],
                'feedback': feedback,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ Evaluation completed!")
            print(f"🎯 Relevance Score: {evaluation['final_score']}/100")
            print(f"📊 Verdict: {evaluation['verdict']} Fit")
            print(f"❌ Missing Skills: {len(evaluation['missing_skills'])}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error evaluating resume: {str(e)}")
            return {}
    
    def evaluate_all_resumes_for_job(self, jd_id: str) -> List[Dict[str, Any]]:
        """Evaluate all resumes against a specific job description"""
        
        try:
            # Get all resume IDs
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM resumes')
            resume_ids = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            results = []
            
            print(f"🔄 Evaluating {len(resume_ids)} resumes for job {jd_id}...")
            
            for i, resume_id in enumerate(resume_ids, 1):
                print(f"Processing resume {i}/{len(resume_ids)}: {resume_id}")
                
                evaluation = self.evaluate_resume(resume_id, jd_id)
                if evaluation:
                    results.append(evaluation)
            
            # Sort by relevance score (highest first)
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            print(f"✅ Batch evaluation completed!")
            print(f"📊 Total evaluations: {len(results)}")
            
            return results
            
        except Exception as e:
            print(f"❌ Error in batch evaluation: {str(e)}")
            return []
    
    def get_dashboard_data(self, jd_id: str = None, min_score: int = 0, max_score: int = 100) -> Dict[str, Any]:
        """Get dashboard data with filtering options"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query based on filters
            if jd_id:
                query = '''
                    SELECT e.*, r.candidate_name, r.candidate_email, j.role_title, j.company_name
                    FROM evaluations e
                    JOIN resumes r ON e.resume_id = r.id
                    JOIN job_descriptions j ON e.jd_id = j.id
                    WHERE e.jd_id = ? AND e.relevance_score BETWEEN ? AND ?
                    ORDER BY e.relevance_score DESC
                '''
                cursor.execute(query, (jd_id, min_score, max_score))
            else:
                query = '''
                    SELECT e.*, r.candidate_name, r.candidate_email, j.role_title, j.company_name
                    FROM evaluations e
                    JOIN resumes r ON e.resume_id = r.id
                    JOIN job_descriptions j ON e.jd_id = j.id
                    WHERE e.relevance_score BETWEEN ? AND ?
                    ORDER BY e.relevance_score DESC
                '''
                cursor.execute(query, (min_score, max_score))
            
            evaluations = cursor.fetchall()
            
            # Calculate statistics
            total_applications = len(evaluations)
            high_fit = sum(1 for eval_data in evaluations if eval_data[4] == "High")  # verdict is at index 4
            medium_fit = sum(1 for eval_data in evaluations if eval_data[4] == "Medium")
            low_fit = sum(1 for eval_data in evaluations if eval_data[4] == "Low")
            
            # Prepare evaluation details
            evaluation_details = []
            for eval_data in evaluations:
                evaluation_details.append({
                    'evaluation_id': eval_data[0],
                    'resume_id': eval_data[1],
                    'jd_id': eval_data[2],
                    'relevance_score': eval_data[3],
                    'verdict': eval_data[4],
                    'candidate_name': eval_data[10],
                    'candidate_email': eval_data[11],
                    'role_title': eval_data[12],
                    'company_name': eval_data[13],
                    'evaluation_date': eval_data[9]
                })
            
            conn.close()
            
            dashboard_data = {
                'summary': {
                    'total_applications': total_applications,
                    'high_fit_count': high_fit,
                    'medium_fit_count': medium_fit,
                    'low_fit_count': low_fit,
                    'high_fit_percentage': (high_fit / total_applications * 100) if total_applications > 0 else 0,
                    'average_score': sum(eval_data[3] for eval_data in evaluations) / total_applications if total_applications > 0 else 0
                },
                'evaluations': evaluation_details,
                'filters_applied': {
                    'jd_id': jd_id,
                    'min_score': min_score,
                    'max_score': max_score
                }
            }
            
            return dashboard_data
            
        except Exception as e:
            print(f"❌ Error getting dashboard data: {str(e)}")
            return {}
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Basic counts
            cursor.execute('SELECT COUNT(*) FROM resumes')
            total_resumes = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM job_descriptions')
            total_jobs = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM evaluations')
            total_evaluations = cursor.fetchone()[0]
            
            # Verdict distribution
            cursor.execute('SELECT verdict, COUNT(*) FROM evaluations GROUP BY verdict')
            verdict_distribution = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Average scores
            cursor.execute('SELECT AVG(relevance_score) FROM evaluations')
            avg_score = cursor.fetchone()[0] or 0
            
            # Recent activity (last 7 days)
            cursor.execute("""
                SELECT COUNT(*) FROM resumes 
                WHERE upload_date > datetime('now', '-7 days')
            """)
            recent_resumes = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM evaluations 
                WHERE evaluation_date > datetime('now', '-7 days')
            """)
            recent_evaluations = cursor.fetchone()[0]
            
            conn.close()
            
            stats = {
                'overview': {
                    'total_resumes': total_resumes,
                    'total_job_descriptions': total_jobs,
                    'total_evaluations': total_evaluations,
                    'average_relevance_score': round(avg_score, 2)
                },
                'verdict_distribution': verdict_distribution,
                'recent_activity': {
                    'resumes_added_last_7_days': recent_resumes,
                    'evaluations_completed_last_7_days': recent_evaluations
                },
                'system_health': {
                    'pdf_processing': PDF_AVAILABLE,
                    'docx_processing': DOCX_AVAILABLE,
                    'ml_features': ML_AVAILABLE,
                    'database_connected': True
                }
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting system stats: {str(e)}")
            return {}
    
    def export_results(self, output_file: str = None, jd_id: str = None) -> str:
        """Export evaluation results to JSON file"""
        
        try:
            dashboard_data = self.get_dashboard_data(jd_id)
            
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = str(self.results_dir / f"evaluation_results_{timestamp}.json")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Results exported to: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Error exporting results: {str(e)}")
            return ""
    
    def list_resumes(self) -> List[Dict[str, Any]]:
        """List all resumes in the system"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, filename, candidate_name, candidate_email, upload_date
                FROM resumes ORDER BY upload_date DESC
            ''')
            
            resumes = []
            for row in cursor.fetchall():
                resumes.append({
                    'id': row[0],
                    'filename': row[1],
                    'candidate_name': row[2],
                    'candidate_email': row[3],
                    'upload_date': row[4]
                })
            
            conn.close()
            return resumes
            
        except Exception as e:
            print(f"❌ Error listing resumes: {str(e)}")
            return []
    
    def list_job_descriptions(self) -> List[Dict[str, Any]]:
        """List all job descriptions in the system"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, filename, company_name, role_title, upload_date
                FROM job_descriptions ORDER BY upload_date DESC
            ''')
            
            job_descriptions = []
            for row in cursor.fetchall():
                job_descriptions.append({
                    'id': row[0],
                    'filename': row[1],
                    'company_name': row[2],
                    'role_title': row[3],
                    'upload_date': row[4]
                })
            
            conn.close()
            return job_descriptions
            
        except Exception as e:
            print(f"❌ Error listing job descriptions: {str(e)}")
            return []


def main():
    """
    Main function demonstrating the Resume Relevance Check System
    """
    
    print("🚀 Automated Resume Relevance Check System")
    print("=" * 50)
    
    # Initialize system
    system = ResumeRelevanceSystem()
    
    print("\n📋 MENU OPTIONS:")
    print("1. Add Resume")
    print("2. Add Job Description")
    print("3. Evaluate Resume vs Job")
    print("4. Evaluate All Resumes for Job")
    print("5. View Dashboard")
    print("6. System Statistics")
    print("7. List Resumes")
    print("8. List Job Descriptions")
    print("9. Export Results")
    print("0. Exit")
    
    while True:
        try:
            choice = input("\n🔢 Enter your choice (0-9): ").strip()
            
            if choice == '0':
                print("👋 Goodbye!")
                break
                
            elif choice == '1':
                file_path = input("📄 Enter resume file path: ").strip()
                candidate_name = input("👤 Enter candidate name (optional): ").strip()
                candidate_email = input("📧 Enter candidate email (optional): ").strip()
                
                resume_id = system.add_resume(file_path, candidate_name, candidate_email)
                if resume_id:
                    print(f"✅ Resume added with ID: {resume_id}")
                    
            elif choice == '2':
                file_path = input("📄 Enter job description file path: ").strip()
                company_name = input("🏢 Enter company name (optional): ").strip()
                role_title = input("💼 Enter role title (optional): ").strip()
                
                jd_id = system.add_job_description(file_path, company_name, role_title)
                if jd_id:
                    print(f"✅ Job description added with ID: {jd_id}")
                    
            elif choice == '3':
                resume_id = input("🆔 Enter resume ID: ").strip()
                jd_id = input("🆔 Enter job description ID: ").strip()
                
                evaluation = system.evaluate_resume(resume_id, jd_id)
                if evaluation:
                    print(f"\n📊 EVALUATION RESULTS:")
                    print(f"Score: {evaluation['relevance_score']}/100")
                    print(f"Verdict: {evaluation['verdict']}")
                    print(f"Missing Skills: {len(evaluation['missing_skills'])}")
                    
                    show_feedback = input("\n📝 Show detailed feedback? (y/n): ").strip().lower()
                    if show_feedback == 'y':
                        print("\n" + evaluation['feedback'])
                        
            elif choice == '4':
                jd_id = input("🆔 Enter job description ID: ").strip()
                
                results = system.evaluate_all_resumes_for_job(jd_id)
                if results:
                    print(f"\n📊 BATCH EVALUATION RESULTS:")
                    print(f"Total Evaluated: {len(results)}")
                    
                    # Show top 5 candidates
                    print(f"\n🏆 TOP 5 CANDIDATES:")
                    for i, result in enumerate(results[:5], 1):
                        print(f"{i}. Score: {result['relevance_score']}/100 ({result['verdict']}) - {result['resume_id']}")
                        
            elif choice == '5':
                jd_id = input("🆔 Enter job description ID (optional): ").strip() or None
                min_score = int(input("📊 Enter minimum score (0-100): ").strip() or "0")
                max_score = int(input("📊 Enter maximum score (0-100): ").strip() or "100")
                
                dashboard = system.get_dashboard_data(jd_id, min_score, max_score)
                if dashboard:
                    summary = dashboard['summary']
                    print(f"\n📈 DASHBOARD SUMMARY:")
                    print(f"Total Applications: {summary['total_applications']}")
                    print(f"High Fit: {summary['high_fit_count']} ({summary['high_fit_percentage']:.1f}%)")
                    print(f"Medium Fit: {summary['medium_fit_count']}")
                    print(f"Low Fit: {summary['low_fit_count']}")
                    print(f"Average Score: {summary['average_score']:.1f}")
                    
            elif choice == '6':
                stats = system.get_system_stats()
                if stats:
                    print(f"\n📊 SYSTEM STATISTICS:")
                    overview = stats['overview']
                    print(f"Total Resumes: {overview['total_resumes']}")
                    print(f"Total Job Descriptions: {overview['total_job_descriptions']}")
                    print(f"Total Evaluations: {overview['total_evaluations']}")
                    print(f"Average Score: {overview['average_relevance_score']}")
                    
                    print(f"\nVerdict Distribution:")
                    for verdict, count in stats['verdict_distribution'].items():
                        print(f"  {verdict}: {count}")
                        
            elif choice == '7':
                resumes = system.list_resumes()
                print(f"\n📄 RESUMES ({len(resumes)}):")
                for i, resume in enumerate(resumes[:10], 1):  # Show first 10
                    print(f"{i}. {resume['filename']} - {resume['candidate_name']} ({resume['id'][:8]}...)")
                    
            elif choice == '8':
                jds = system.list_job_descriptions()
                print(f"\n💼 JOB DESCRIPTIONS ({len(jds)}):")
                for i, jd in enumerate(jds[:10], 1):  # Show first 10
                    print(f"{i}. {jd['filename']} - {jd['company_name']} ({jd['id'][:8]}...)")
                    
            elif choice == '9':
                jd_id = input("🆔 Enter job description ID (optional): ").strip() or None
                output_file = input("📁 Enter output file path (optional): ").strip() or None
                
                exported_file = system.export_results(output_file, jd_id)
                if exported_file:
                    print(f"✅ Results exported to: {exported_file}")
                    
            else:
                print("❌ Invalid choice. Please try again.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Operation cancelled. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            continue


if __name__ == "__main__":
    main()


# Installation Requirements:
"""
pip install PyMuPDF docx2txt scikit-learn numpy

Optional but recommended:
pip install spacy
python -m spacy download en_core_web_sm
"""

# Example Usage:
"""
# Initialize system
system = ResumeRelevanceSystem()

# Add resume
resume_id = system.add_resume("path/to/resume.pdf", "John Doe", "john@example.com")

# Add job description
jd_id = system.add_job_description("path/to/job_description.pdf", "Tech Corp", "Software Developer")

# Evaluate
evaluation = system.evaluate_resume(resume_id, jd_id)

# Get dashboard data
dashboard = system.get_dashboard_data()

# Export results
system.export_results("results.json")
"""