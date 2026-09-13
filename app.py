"""
app.py
------
SkillGap AI — main Streamlit application.

Run with:
    streamlit run app.py
"""

import json
import streamlit as st

from resume_parser import (
    extract_text_from_pdf,
    clean_resume_text,
    validate_resume_text,
    ResumeParsingError,
)
from ai_engine import analyze_resume_vs_job, chat_with_assistant, transcribe_audio, AIEngineError
from report_generator import generate_report, ReportGenerationError

# --------------------------------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="SkillGap AI — Turn Your Resume Into Your Career Roadmap",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------------------------------
# SAMPLE / DEMO DATA
# --------------------------------------------------------------------------
SAMPLE_JOB_DESCRIPTION = """Software Developer — Backend (Python)

We are looking for a Backend Software Developer to join our growing engineering team.

Responsibilities:
- Design, build, and maintain RESTful APIs using Django or FastAPI
- Work with PostgreSQL and Redis for data storage and caching
- Write clean, tested, maintainable Python code
- Containerize services using Docker and deploy via CI/CD pipelines
- Collaborate with frontend engineers consuming your APIs
- Monitor and improve application performance and reliability

Requirements:
- Strong proficiency in Python
- Experience with Django or Flask (Django preferred) and REST API design
- Working knowledge of PostgreSQL or another relational database
- Familiarity with Docker and containerized deployments
- Understanding of Git and collaborative version control workflows
- Basic understanding of cloud platforms (AWS or GCP)
- Good communication and problem-solving skills

Nice to have:
- Experience with Celery or background task queues
- Exposure to CI/CD tools (GitHub Actions, Jenkins)
- Familiarity with unit testing frameworks (pytest)
"""

SAMPLE_RESUME_TEXT = """John Student
Aspiring Software Developer | Computer Science Undergraduate

EDUCATION
B.Tech in Computer Science, ABC Institute of Technology (2022 - 2026)
Relevant coursework: Data Structures, Algorithms, Operating Systems, DBMS

TECHNICAL SKILLS
Languages: Python, Java, C++, JavaScript, SQL
Web: HTML, CSS, Flask, basic React
Tools: Git, GitHub, VS Code, Postman
Databases: MySQL (basic)

PROJECTS
Personal Expense Tracker (Flask, SQLite)
- Built a web app to track daily expenses with login and charts
- Implemented CRUD operations using Flask and SQLite

Student Result Management System (Java, MySQL)
- Console-based application to manage student records
- Used JDBC to connect to a MySQL database

Portfolio Website (HTML, CSS, JavaScript)
- Built and deployed a personal portfolio website on GitHub Pages

EXPERIENCE
Summer Intern, Local Startup (2 months)
- Assisted in fixing bugs in an internal Flask-based admin tool
- Wrote basic unit tests using pytest

SOFT SKILLS
Team collaboration, problem solving, time management, quick learner

ACHIEVEMENTS
- Winner, college-level hackathon (2024)
- Solved 150+ problems on LeetCode / HackerRank
"""

# --------------------------------------------------------------------------
# SESSION STATE INIT
# --------------------------------------------------------------------------
defaults = {
    "page": "home",
    "resume_text": "",
    "resume_filename": "",
    "job_description": "",
    "analysis": None,
    "student_name": "",
    "error_message": None,
    "chat_history": [],
    "chat_error": None,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def go_to(page_name: str):
    st.session_state.page = page_name


# --------------------------------------------------------------------------
# GLOBAL STYLES
# --------------------------------------------------------------------------
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif;
        }

        #MainMenu, footer, header {visibility: hidden;}

        .main {
            background: radial-gradient(circle at 10% 0%, #1b1030 0%, #0f0c29 45%, #0a0a12 100%);
        }

        .block-container {
            padding-top: 1.5rem;
            max-width: 1200px;
        }

        /* ---------- HERO ---------- */
        .hero-wrap {
            text-align: center;
            padding: 60px 10px 30px 10px;
            animation: fadeInUp 0.9s ease;
        }
        .hero-badge {
            display: inline-block;
            padding: 6px 16px;
            border-radius: 999px;
            background: rgba(129, 140, 248, 0.15);
            border: 1px solid rgba(129, 140, 248, 0.4);
            color: #c7d2fe;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.3px;
            margin-bottom: 22px;
        }
        .hero-title {
            font-size: 52px;
            font-weight: 800;
            line-height: 1.15;
            background: linear-gradient(90deg, #a5b4fc, #f0abfc 55%, #fbcfe8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 18px;
        }
        .hero-sub {
            font-size: 18px;
            color: #cbd5e1;
            max-width: 720px;
            margin: 0 auto 34px auto;
            line-height: 1.6;
        }

        /* ---------- CARDS ---------- */
        .glass-card {
            background: linear-gradient(160deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
            border: 1px solid rgba(255,255,255,0.09);
            border-radius: 18px;
            padding: 26px 24px;
            height: 100%;
            transition: transform 0.25s ease, border-color 0.25s ease;
        }
        .glass-card:hover {
            transform: translateY(-4px);
            border-color: rgba(165, 180, 252, 0.5);
        }
        .card-icon { font-size: 30px; margin-bottom: 10px; display:block; }
        .card-title { font-size: 17px; font-weight: 700; color: #f1f5f9; margin-bottom: 6px; }
        .card-text { font-size: 14px; color: #94a3b8; line-height: 1.5; }

        .step-number {
            font-size: 34px;
            font-weight: 800;
            background: linear-gradient(90deg, #818cf8, #f472b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* ---------- SECTION TITLES ---------- */
        .section-title {
            font-size: 30px;
            font-weight: 800;
            color: #f8fafc;
            text-align: center;
            margin-top: 10px;
            margin-bottom: 6px;
        }
        .section-sub {
            text-align: center;
            color: #94a3b8;
            font-size: 15px;
            margin-bottom: 34px;
        }

        /* ---------- BADGES ---------- */
        .badge {
            display: inline-block;
            padding: 7px 14px;
            margin: 4px 6px 4px 0;
            border-radius: 999px;
            font-size: 13.5px;
            font-weight: 600;
        }
        .badge-have {
            background: rgba(52, 211, 153, 0.15);
            border: 1px solid rgba(52, 211, 153, 0.5);
            color: #6ee7b7;
        }
        .badge-missing {
            background: rgba(248, 113, 113, 0.15);
            border: 1px solid rgba(248, 113, 113, 0.5);
            color: #fca5a5;
        }

        /* ---------- METRIC / SCORE CARDS ---------- */
        .metric-card {
            background: linear-gradient(160deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02));
            border: 1px solid rgba(255,255,255,0.09);
            border-radius: 18px;
            padding: 22px;
            text-align: center;
        }
        .metric-value {
            font-size: 40px;
            font-weight: 800;
            background: linear-gradient(90deg, #818cf8, #f472b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .metric-label {
            font-size: 14px;
            color: #94a3b8;
            font-weight: 600;
            margin-top: 4px;
        }

        .match-hero {
            background: linear-gradient(135deg, rgba(99,102,241,0.25), rgba(236,72,153,0.2));
            border: 1px solid rgba(165,180,252,0.4);
            border-radius: 22px;
            padding: 34px;
            text-align: center;
        }
        .match-hero .metric-value { font-size: 64px; }

        /* ---------- ROADMAP ---------- */
        .roadmap-item {
            background: rgba(255,255,255,0.04);
            border-left: 4px solid #818cf8;
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 14px;
        }
        .roadmap-title { font-size: 16px; font-weight: 700; color: #f1f5f9; }
        .roadmap-meta { font-size: 12.5px; color: #a5b4fc; font-weight: 600; margin-bottom: 6px;}
        .roadmap-body { font-size: 14px; color: #cbd5e1; line-height: 1.5; }

        /* ---------- PRIORITY TAGS ---------- */
        .tag-high { color: #fca5a5; font-weight: 700; }
        .tag-medium { color: #fcd34d; font-weight: 700; }
        .tag-low { color: #93c5fd; font-weight: 700; }

        .gap-card {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 14px;
            padding: 18px 20px;
            margin-bottom: 12px;
        }

        div.stButton > button {
            background: linear-gradient(90deg, #6366f1, #ec4899);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.55rem 0.8rem;
            font-weight: 700;
            font-size: 14px;
            white-space: normal;
            line-height: 1.25;
            transition: all 0.2s ease;
        }
        div.stButton > button:hover {
            filter: brightness(1.12);
            transform: translateY(-1px);
        }
        @media (max-width: 600px) {
            div.stButton > button {
                font-size: 12.5px;
                padding: 0.5rem 0.4rem;
            }
        }

        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(18px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .fade-in { animation: fadeInUp 0.6s ease; }

        section[data-testid="stFileUploaderDropzone"] {
            background: rgba(255,255,255,0.03);
            border: 1.5px dashed rgba(165,180,252,0.4);
            border-radius: 14px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# TOP NAV
# --------------------------------------------------------------------------
st.markdown("### 🧭 SkillGap AI")
n1, n2, n3 = st.columns(3)
with n1:
    if st.button("🏠 Home", use_container_width=True):
        go_to("home")
with n2:
    if st.button("📊 Analyzer", use_container_width=True):
        go_to("analyzer")
with n3:
    if st.button("🤖 Assistant", use_container_width=True):
        go_to("assistant")

st.markdown("<hr style='border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)


# ==========================================================================
# HOME PAGE
# ==========================================================================
def render_home():
    st.markdown(
        """
        <div class="hero-wrap">
            <div class="hero-badge">✨ AI-Powered Career Intelligence</div>
            <div class="hero-title">Turn Your Resume Into<br>Your Career Roadmap</div>
            <div class="hero-sub">
                Upload your resume, compare it with your dream job, discover your skill gaps,
                and get an AI-powered learning path — built specifically for you.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([3, 2, 2])
    with c2:
        if st.button("🚀 Analyze My Resume", use_container_width=True):
            go_to("analyzer")
    with c3:
        if st.button("🎬 Try Demo", use_container_width=True):
            st.session_state.resume_text = SAMPLE_RESUME_TEXT
            st.session_state.resume_filename = "demo_resume.pdf"
            st.session_state.job_description = SAMPLE_JOB_DESCRIPTION
            st.session_state.student_name = "John Student (Demo)"
            go_to("analyzer")

    st.markdown("<div style='height:50px;'></div>", unsafe_allow_html=True)

    # ---------------- HOW IT WORKS ----------------
    st.markdown('<div class="section-title">How It Works</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Four simple steps from resume to roadmap</div>',
        unsafe_allow_html=True,
    )
    steps = [
        ("01", "📄", "Upload Resume", "Drop in your PDF resume — we extract and read the content instantly."),
        ("02", "📋", "Add Job Description", "Paste a real job posting you're targeting, or try our sample."),
        ("03", "🤖", "AI Finds Skill Gaps", "Claude compares both and identifies exactly what's missing."),
        ("04", "🗺️", "Get Personalized Roadmap", "Receive a step-by-step learning path built just for you."),
    ]
    cols = st.columns(4)
    for col, (num, icon, title, text) in zip(cols, steps):
        with col:
            st.markdown(
                f"""
                <div class="glass-card fade-in">
                    <div class="step-number">{num}</div>
                    <div class="card-icon">{icon}</div>
                    <div class="card-title">{title}</div>
                    <div class="card-text">{text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:50px;'></div>", unsafe_allow_html=True)

    # ---------------- FEATURES ----------------
    st.markdown('<div class="section-title">Features</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Everything you need to close the gap between where you are and where you want to be</div>',
        unsafe_allow_html=True,
    )
    features = [
        ("🧠", "AI Resume Analysis", "Deep parsing of skills, projects, education and experience from your resume."),
        ("🎯", "Job Match Score", "A real, calculated percentage showing how well you fit a specific job posting."),
        ("🔍", "Skill Gap Detection", "Pinpoints exactly which skills you're missing, with priority levels."),
        ("🗺️", "Personalized Learning Path", "An ordered roadmap built from your actual gaps, not generic advice."),
        ("🛠️", "Project Recommendations", "Concrete portfolio projects designed to close your specific gaps."),
        ("📊", "Career Report", "A polished, downloadable PDF report you can share or revisit anytime."),
    ]
    for row_start in range(0, len(features), 3):
        cols = st.columns(3)
        for col, (icon, title, text) in zip(cols, features[row_start:row_start + 3]):
            with col:
                st.markdown(
                    f"""
                    <div class="glass-card fade-in">
                        <div class="card-icon">{icon}</div>
                        <div class="card-title">{title}</div>
                        <div class="card-text">{text}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("<div style='height:50px;'></div>", unsafe_allow_html=True)

    # ---------------- EXAMPLE DASHBOARD PREVIEW ----------------
    st.markdown('<div class="section-title">See It In Action</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">A preview of what your results dashboard looks like</div>',
        unsafe_allow_html=True,
    )
    p1, p2, p3, p4 = st.columns(4)
    preview_metrics = [
        ("72%", "JOB MATCH"),
        ("12", "Skills Found"),
        ("5", "Skills Missing"),
        ("78%", "Experience Match"),
    ]
    for col, (val, label) in zip([p1, p2, p3, p4], preview_metrics):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{val}</div>
                    <div class="metric-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="glass-card" style="text-align:center; margin-top: 18px;">
            <div class="card-text">
                ⬆️ This is a static preview. Click <b>Analyze My Resume</b> or <b>Try Demo</b> above to
                generate your own real, AI-powered results.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)


# ==========================================================================
# ANALYZER PAGE
# ==========================================================================
def render_analyzer():
    st.markdown('<div class="section-title">Resume & Job Analyzer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Upload your resume and paste a job description to get started</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.error_message:
        st.error(st.session_state.error_message)

    left, right = st.columns(2)

    with left:
        st.markdown("#### 📄 Your Resume")
        st.session_state.student_name = st.text_input(
            "Your name (for the report)", value=st.session_state.student_name, placeholder="e.g. John Student"
        )
        uploaded_file = st.file_uploader(
            "Drag and drop your resume PDF here, or click to browse",
            type=["pdf"],
            accept_multiple_files=False,
        )
        if uploaded_file is not None:
            try:
                raw_text = extract_text_from_pdf(uploaded_file)
                cleaned = clean_resume_text(raw_text)
                is_valid, err = validate_resume_text(cleaned)
                if not is_valid:
                    st.session_state.error_message = err
                else:
                    st.session_state.resume_text = cleaned
                    st.session_state.resume_filename = uploaded_file.name
                    st.session_state.error_message = None
            except ResumeParsingError as exc:
                st.session_state.error_message = str(exc)

        if st.session_state.resume_filename:
            st.success(f"✅ Loaded: **{st.session_state.resume_filename}**")
            with st.expander("Preview extracted resume text"):
                st.text_area(
                    "Extracted text",
                    value=st.session_state.resume_text,
                    height=220,
                    disabled=True,
                    label_visibility="collapsed",
                )
        else:
            st.info("No resume uploaded yet.")

    with right:
        st.markdown("#### 📋 Job Description")
        if st.button("📎 Use Sample Job Description"):
            st.session_state.job_description = SAMPLE_JOB_DESCRIPTION

        st.session_state.job_description = st.text_area(
            "Paste the job description here",
            value=st.session_state.job_description,
            height=340,
            placeholder="Paste a real job posting here...",
            label_visibility="collapsed",
        )

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    center = st.columns([3, 3, 3])
    with center[1]:
        analyze_clicked = st.button("Analyze My Career 🚀", use_container_width=True)

    if analyze_clicked:
        st.session_state.error_message = None

        if not st.session_state.resume_text.strip():
            st.session_state.error_message = "Please upload a resume before analyzing."
        elif not st.session_state.job_description.strip():
            st.session_state.error_message = "Please paste a job description before analyzing."
        else:
            with st.spinner("🤖 AI is analyzing your resume against the job description..."):
                try:
                    result = analyze_resume_vs_job(
                        st.session_state.resume_text,
                        st.session_state.job_description,
                    )
                    st.session_state.analysis = result
                    st.session_state.error_message = None
                except AIEngineError as exc:
                    st.session_state.error_message = str(exc)
                    st.session_state.analysis = None

    if st.session_state.error_message:
        st.error(st.session_state.error_message)

    if st.session_state.analysis:
        st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
        render_dashboard(st.session_state.analysis)


# ==========================================================================
# RESULTS DASHBOARD
# ==========================================================================
def render_dashboard(analysis: dict):
    st.markdown('<hr style="border-color: rgba(255,255,255,0.08);">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Your Results Dashboard</div>', unsafe_allow_html=True)

    match = analysis.get("job_match_percentage", 0)
    exp_match = analysis.get("experience_match_percentage", 0)
    skills_found = analysis.get("skills_found", [])
    skills_missing = analysis.get("skills_missing", [])

    # ---- Top match hero ----
    st.markdown(
        f"""
        <div class="match-hero">
            <div class="metric-label" style="font-size:16px; letter-spacing:1px;">JOB MATCH</div>
            <div class="metric-value">{match}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(match / 100)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{len(skills_found)}</div>'
            f'<div class="metric-label">Skills Found</div></div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{len(skills_missing)}</div>'
            f'<div class="metric-label">Skills Missing</div></div>',
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{exp_match}%</div>'
            f'<div class="metric-label">Experience Match</div></div>',
            unsafe_allow_html=True,
        )

    if analysis.get("candidate_summary"):
        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
        st.info(f"**Summary:** {analysis['candidate_summary']}")

    # ---- Skills found / missing ----
    st.markdown("<div style='height:26px;'></div>", unsafe_allow_html=True)
    st.markdown("#### ✅ Skills You Have")
    if skills_found:
        badges_html = "".join(
            f'<span class="badge badge-have">{s.get("name","")}</span>' for s in skills_found
        )
        st.markdown(badges_html, unsafe_allow_html=True)
    else:
        st.write("No strongly matching skills were detected.")

    st.markdown("<div style='height:22px;'></div>", unsafe_allow_html=True)
    st.markdown("#### ⚠️ Skills You Are Missing")
    if skills_missing:
        badges_html = "".join(
            f'<span class="badge badge-missing">{s.get("name","")}</span>' for s in skills_missing
        )
        st.markdown(badges_html, unsafe_allow_html=True)
    else:
        st.write("Great news — no major missing skills detected!")

    # ---- Strengths / Weaknesses ----
    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
    col_s, col_w = st.columns(2)
    with col_s:
        st.markdown("#### 💪 Your Strengths")
        for item in analysis.get("strengths", []):
            st.markdown(f"- {item}")
    with col_w:
        st.markdown("#### 📈 Areas To Improve")
        for item in analysis.get("weaknesses", []):
            st.markdown(f"- {item}")

    # ---- Skill Gap Analysis ----
    st.markdown("<div style='height:34px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-title" style="font-size:24px;">Skill Gap Analysis</div>', unsafe_allow_html=True)
    priority_class = {"High": "tag-high", "Medium": "tag-medium", "Low": "tag-low"}
    for skill in skills_missing:
        pr = skill.get("priority", "Medium")
        css_class = priority_class.get(pr, "tag-medium")
        st.markdown(
            f"""
            <div class="gap-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-size:17px; font-weight:700; color:#f1f5f9;">{skill.get('name','')}</div>
                    <div class="{css_class}">Priority: {pr}</div>
                </div>
                <div style="color:#cbd5e1; font-size:14px; margin:8px 0;">{skill.get('why_needed','')}</div>
                <div style="color:#94a3b8; font-size:13.5px;">
                    Current: <b>{skill.get('current_level','None')}</b> &nbsp;→&nbsp;
                    Required: <b>{skill.get('required_level','N/A')}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---- Roadmap ----
    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-title" style="font-size:24px;">Personalized Learning Roadmap</div>', unsafe_allow_html=True)
    for step in analysis.get("learning_roadmap", []):
        st.markdown(
            f"""
            <div class="roadmap-item">
                <div class="roadmap-meta">STEP {step.get('step_number','')} · {step.get('difficulty','')} · {step.get('estimated_time','')}</div>
                <div class="roadmap-title">{step.get('title','')}</div>
                <div class="roadmap-body">
                    <b>Why it matters:</b> {step.get('why_it_matters','')}<br>
                    <b>Practice:</b> {step.get('suggested_practice','')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---- Projects ----
    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-title" style="font-size:24px;">Recommended Projects</div>', unsafe_allow_html=True)
    proj_cols = st.columns(2)
    for i, proj in enumerate(analysis.get("recommended_projects", [])):
        with proj_cols[i % 2]:
            skills_html = "".join(
                f'<span class="badge badge-have">{s}</span>' for s in proj.get("skills_practiced", [])
            )
            st.markdown(
                f"""
                <div class="glass-card" style="margin-bottom:16px;">
                    <div class="card-title">🛠️ {proj.get('title','')}</div>
                    <div class="card-text" style="margin-bottom:10px;">{proj.get('description','')}</div>
                    <div style="margin-bottom:10px;">{skills_html}</div>
                    <div class="card-text"><b>Why it helps:</b> {proj.get('why_it_helps','')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ---- Career report download ----
    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-title" style="font-size:24px;">Career Report</div>', unsafe_allow_html=True)
    st.write("Download a complete PDF report of this analysis to keep or share.")
    try:
        pdf_bytes = generate_report(
            student_name=st.session_state.student_name or "Not provided",
            target_role=analysis.get("target_role", ""),
            analysis=analysis,
        )
        st.download_button(
            label="📥 Download Career Report",
            data=pdf_bytes,
            file_name="SkillGap_AI_Career_Report.pdf",
            mime="application/pdf",
            use_container_width=False,
        )
    except ReportGenerationError as exc:
        st.error(str(exc))


# ==========================================================================
# HELPER — text-to-speech "Read Aloud" widget (uses the browser's built-in
# speech engine, no extra service or API needed)
# ==========================================================================
def render_read_aloud_button(text: str, key: str):
    import streamlit.components.v1 as components
    safe_text = json.dumps(text)
    components.html(
        f"""
        <button id="btn-{key}" style="
            background: linear-gradient(90deg, #6366f1, #ec4899);
            color: white; border: none; border-radius: 10px;
            padding: 6px 14px; font-weight: 700; font-size: 13px;
            cursor: pointer; font-family: Inter, sans-serif;">
            🔊 Read Aloud
        </button>
        <script>
            const btn = document.getElementById("btn-{key}");
            btn.onclick = function() {{
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance({safe_text});
                utterance.rate = 1.0;
                window.speechSynthesis.speak(utterance);
            }};
        </script>
        """,
        height=45,
    )


# ==========================================================================
# AI ASSISTANT (CHAT) PAGE
# ==========================================================================
def render_assistant():
    st.markdown('<div class="section-title">🤖 AI Career Assistant</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Ask anything about careers, skills, resumes, or your analysis results — by typing or speaking</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.analysis:
        st.info(
            "💡 I have access to your latest analysis, so feel free to ask things like "
            "'Which skill should I learn first?' or 'Why is my match score low?'"
        )

    # Render existing chat history
    for i, turn in enumerate(st.session_state.chat_history):
        with st.chat_message("user" if turn["role"] == "user" else "assistant"):
            st.markdown(turn["content"])
            if turn["role"] == "assistant":
                render_read_aloud_button(turn["content"], key=f"read_{i}")

    if st.session_state.chat_error:
        st.error(st.session_state.chat_error)

    # ---- Voice input ----
    st.markdown("##### 🎤 Or speak your question")
    try:
        from streamlit_mic_recorder import mic_recorder
        audio = mic_recorder(
            start_prompt="🎤 Start recording",
            stop_prompt="⏹️ Stop recording",
            just_once=True,
            use_container_width=True,
            key="voice_recorder",
        )
    except ImportError:
        audio = None
        st.caption("Voice input needs the `streamlit-mic-recorder` package (see requirements.txt).")

    voice_message = None
    if audio and audio.get("bytes"):
        with st.spinner("🎧 Transcribing your voice..."):
            try:
                voice_message = transcribe_audio(audio["bytes"], mime_type="audio/wav")
            except AIEngineError as exc:
                st.session_state.chat_error = str(exc)
                st.error(str(exc))

    # ---- Text input ----
    typed_message = st.chat_input("Ask your AI career assistant something...")

    user_message = voice_message or typed_message

    if user_message:
        st.session_state.chat_history.append({"role": "user", "content": user_message})
        with st.chat_message("user"):
            st.markdown(user_message)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    reply = chat_with_assistant(
                        st.session_state.chat_history,
                        latest_analysis=st.session_state.analysis,
                    )
                    st.markdown(reply)
                    render_read_aloud_button(reply, key=f"read_new_{len(st.session_state.chat_history)}")
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    st.session_state.chat_error = None
                except AIEngineError as exc:
                    st.session_state.chat_error = str(exc)
                    st.error(str(exc))

    if st.session_state.chat_history:
        if st.button("🗑️ Clear conversation"):
            st.session_state.chat_history = []
            st.session_state.chat_error = None
            st.rerun()


# ==========================================================================
# ROUTER
# ==========================================================================
if st.session_state.page == "home":
    render_home()
elif st.session_state.page == "analyzer":
    render_analyzer()
elif st.session_state.page == "assistant":
    render_assistant()
