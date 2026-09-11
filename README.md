# 🧭 SkillGap AI

### DVPS28 — AI Skill-Gap Analyzer

> An AI skill-gap analyzer that compares a student's resume/projects against real job postings and suggests a personalized learning path.

---

## 1. Project Name
**SkillGap AI**

## 2. Problem Statement
**DVPS28 — AI Skill-Gap Analyzer**: An AI skill-gap analyzer that compares a student's resume/projects against real job postings and suggests a personalized learning path.

## 3. Problem We're Solving
Most students don't know **why** they aren't getting shortlisted for jobs. They apply to postings without knowing:
- Which specific skills the job actually requires
- How much of that they already have
- What exactly is missing
- What to learn first, and in what order

Generic "learn to code" advice doesn't help — students need a plan built from **their own resume** compared against **a real job description**.

## 4. Our Solution
SkillGap AI lets a student:
1. Upload their resume (PDF)
2. Paste a real job description
3. Get an AI-generated, personalized analysis showing their match score, the skills they have, the skills they're missing, and a step-by-step roadmap (with project ideas) to close that gap — all in a polished, downloadable report.

No part of the analysis is hardcoded or faked — every result comes from a live call to the Claude AI API using the student's actual resume text and the actual job description they pasted.

## 5. Features
- 🧠 AI-powered resume analysis (skills, projects, education, experience extraction)
- 🎯 Real, calculated Job Match percentage
- ✅ "Skills You Have" and ⚠️ "Skills You Are Missing" badge lists
- 💪 AI-generated strengths and 📈 areas to improve
- 🔍 Detailed skill-gap breakdown (why it's needed, current vs. required level, priority)
- 🗺️ Personalized, ordered learning roadmap generated from the actual missing skills
- 🛠️ 2–4 recommended portfolio projects targeting the specific gaps
- 📄 Downloadable PDF Career Report
- 🎬 One-click "Try Demo" mode for instant judge-friendly demonstrations
- 🎨 Modern, responsive, dark-themed SaaS-style UI with gradients, glass cards, and animations
- 🛡️ Friendly error handling for missing files, empty inputs, bad PDFs, and API failures

## 6. How AI Is Used
SkillGap AI uses the **Anthropic Claude API** (model: `claude-sonnet-5`) as its core intelligence layer:

1. The extracted resume text and the pasted job description are combined into a single, carefully engineered prompt (see `ai_engine.py`).
2. Claude is instructed to act as an expert technical recruiter, and to return **only structured JSON** containing: match percentages, detected skills, missing skills (with priority and required level), strengths, weaknesses, an ordered learning roadmap, and recommended projects.
3. The app parses and validates that JSON, then renders it live in the dashboard — nothing is pre-written or templated per-job.
4. The same structured result is reused to generate the downloadable PDF report.

This means the analysis is genuinely different for every resume/job combination.

## 7. Technology Stack
| Layer | Technology |
|---|---|
| Frontend + Backend | **Streamlit** (Python) |
| AI | **Anthropic Claude API** (`claude-sonnet-5`) |
| Resume parsing | **pypdf** (PDF text extraction) |
| Report generation | **fpdf2** (PDF report generation) |
| Config / secrets | **python-dotenv** (environment variables) |

## 8. Project Structure
```
skillgap-ai/
├── app.py                 # Main Streamlit app: UI, pages, dashboard, routing
├── ai_engine.py            # Talks to the Claude API, builds prompt, parses JSON result
├── resume_parser.py         # Extracts and validates text from uploaded PDF resumes
├── report_generator.py       # Builds the downloadable PDF career report
├── requirements.txt         # Python dependencies
├── .env.example            # Template for your environment variables
├── .gitignore              # Files/folders Git should ignore (including .env)
└── README.md               # This file
```

## 9. Installation

### Prerequisites
- Python 3.9 or newer installed on your computer
- An Anthropic API key (get one at https://console.anthropic.com/)

### Steps
```bash
# 1. Go into the project folder
cd skillgap-ai

# 2. (Recommended) Create a virtual environment
python -m venv venv

# 3. Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# 4. Install all dependencies
pip install -r requirements.txt
```

## 10. Environment Variables
Create a file named `.env` in the project folder (copy `.env.example` and rename it):

```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

⚠️ **Never commit your `.env` file to GitHub.** It's already listed in `.gitignore` to prevent this.

## 11. How To Run
```bash
streamlit run app.py
```
This will open the app automatically in your browser at `http://localhost:8501`.

## 12. Example Usage
1. Open the app → click **"Try Demo"** (fastest way to see it work), or
2. Go to the **Analyzer** page
3. Upload your resume PDF (drag & drop or browse)
4. Paste a real job description you're interested in (or click "Use Sample Job Description")
5. Click **"Analyze My Career 🚀"**
6. Review your Job Match %, skills found/missing, strengths, weaknesses, skill gap breakdown, learning roadmap, and recommended projects
7. Click **"Download Career Report"** to save a PDF copy

## 13. Future Improvements
- Support multiple resume formats (DOCX, TXT)
- Job description auto-fetch from a pasted job posting URL
- Track progress over time as the student completes roadmap steps
- Multi-job comparison ("which of these 3 jobs am I closest to?")
- Resume rewriting suggestions tailored to the target job
- User accounts to save past analyses and reports

---

## About This Project
Built for a college hackathon as a solution to problem statement **DVPS28 — AI Skill-Gap Analyzer**.
