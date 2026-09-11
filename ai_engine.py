"""
ai_engine.py
------------
This file talks to the Google Gemini API (FREE tier, no credit card required)
to do the actual "AI brain work" of SkillGap AI:

    - Reads the resume text + job description
    - Asks Gemini to compare them
    - Gets back a structured JSON result with match %, skills, gaps,
      strengths, weaknesses, a learning roadmap, and project recommendations

No fake/hardcoded results are used anywhere in this file — every analysis
is generated live by the AI model based on the actual resume and job text
that is passed in.

NOTE: This uses the newer "google-genai" SDK (import: `from google import genai`),
NOT the older/deprecated "google-generativeai" package. The newer SDK correctly
supports Google's current API key format (keys starting with "AQ.").
"""

import os
import json
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load variables from a local .env file (used only for local development).
load_dotenv()

MODEL_NAME = "gemini-2.5-flash"


class AIEngineError(Exception):
    """Raised for any problem talking to the AI or parsing its response."""
    pass


def _get_client() -> genai.Client:
    """
    Creates the Gemini API client using the GEMINI_API_KEY environment
    variable. Never hardcode the key in source code.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise AIEngineError(
            "No API key found. Please set the GEMINI_API_KEY environment "
            "variable (see .env.example) before running the app. "
            "Get a free key at https://aistudio.google.com/app/apikey"
        )
    try:
        return genai.Client(api_key=api_key)
    except Exception as exc:
        raise AIEngineError(f"Could not initialize the AI client: {exc}") from exc


def _build_prompt(resume_text: str, job_description: str) -> str:
    """Builds the instruction prompt sent to Gemini."""
    return f"""You are an expert technical recruiter and career coach AI embedded in a
product called "SkillGap AI". A student has uploaded their resume and pasted
a real job description. Your job is to carefully compare the two and produce
a detailed, honest, and genuinely useful analysis.

Do NOT invent skills that are not reasonably implied by the resume text.
Do NOT invent job requirements that are not reasonably implied by the job description.
Base match percentages on the real overlap and gaps you find — do not default to
a generic round number, be specific and justified.

RESUME TEXT:
\"\"\"
{resume_text}
\"\"\"

JOB DESCRIPTION:
\"\"\"
{job_description}
\"\"\"

Respond with ONLY a valid JSON object (no markdown fences, no commentary before
or after) with EXACTLY this structure:

{{
  "job_match_percentage": <integer 0-100>,
  "experience_match_percentage": <integer 0-100>,
  "candidate_summary": "<2-3 sentence summary of the candidate>",
  "target_role": "<short name of the role being targeted, inferred from the JD>",
  "skills_found": [
    {{"name": "<skill>", "category": "<Programming Language|Framework|Database|Tool|Cloud|Soft Skill|Other>"}}
  ],
  "skills_missing": [
    {{
      "name": "<skill>",
      "why_needed": "<why the job requires this skill, 1 sentence>",
      "current_level": "<None|Beginner|Intermediate>",
      "required_level": "<Beginner|Intermediate|Advanced>",
      "priority": "<High|Medium|Low>"
    }}
  ],
  "strengths": [
    "<AI-generated explanation of a genuine strength, 1-2 sentences each>"
  ],
  "weaknesses": [
    "<AI-generated explanation of a genuine weakness/area to improve, 1-2 sentences each>"
  ],
  "learning_roadmap": [
    {{
      "step_number": 1,
      "title": "<what to learn>",
      "why_it_matters": "<why this step matters for the target job>",
      "difficulty": "<Beginner|Intermediate|Advanced>",
      "suggested_practice": "<a concrete practice task or exercise>",
      "estimated_time": "<e.g. '1 week', '3-5 days'>"
    }}
  ],
  "recommended_projects": [
    {{
      "title": "<project title>",
      "description": "<1-2 sentence description>",
      "skills_practiced": ["<skill1>", "<skill2>"],
      "why_it_helps": "<why building this closes the candidate's skill gap>"
    }}
  ],
  "education_summary": "<short summary of education found in resume, or 'Not specified' if none>",
  "experience_summary": "<short summary of work/project experience found in resume>"
}}

Rules:
- "skills_found" should include ALL relevant technical AND soft skills detected in the resume that are also relevant to this job (aim for a thorough but non-redundant list).
- "skills_missing" should include skills required/preferred by the job description that are NOT evidenced in the resume (aim for 4-8 items, ordered by priority, High first).
- "learning_roadmap" must have between 5 and 8 ordered steps, built specifically from the missing skills, in a logical learning order (foundational topics first).
- "recommended_projects" must have between 2 and 4 projects, each directly targeting the missing skills.
- Keep all text concise and specific to THIS resume and THIS job description — never generic filler.
- Return ONLY the JSON object, nothing else.
"""


def _extract_json(raw_text: str) -> dict:
    """
    Gemini should return pure JSON, but this defensively strips markdown
    code fences or stray text if the model adds any, then parses it.
    """
    text = raw_text.strip()

    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)
    else:
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            text = text[first_brace:last_brace + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise AIEngineError(
            "The AI returned a response we couldn't understand. "
            "Please try clicking 'Analyze My Career' again."
        ) from exc


def _validate_result_shape(data: dict) -> dict:
    """Makes sure required keys exist, filling in safe defaults if missing."""
    defaults = {
        "job_match_percentage": 0,
        "experience_match_percentage": 0,
        "candidate_summary": "",
        "target_role": "",
        "skills_found": [],
        "skills_missing": [],
        "strengths": [],
        "weaknesses": [],
        "learning_roadmap": [],
        "recommended_projects": [],
        "education_summary": "Not specified",
        "experience_summary": "Not specified",
    }
    for key, default_value in defaults.items():
        if key not in data or data[key] is None:
            data[key] = default_value

    for pct_key in ("job_match_percentage", "experience_match_percentage"):
        try:
            data[pct_key] = max(0, min(100, int(data[pct_key])))
        except (ValueError, TypeError):
            data[pct_key] = 0

    return data


def analyze_resume_vs_job(resume_text: str, job_description: str) -> dict:
    """
    Main entry point: sends the resume + job description to Gemini and
    returns a structured dictionary with the full analysis.

    Raises AIEngineError on any failure (missing key, network/API error,
    or an unparseable response) with a friendly, specific message.
    """
    if not resume_text or not resume_text.strip():
        raise AIEngineError("Resume text is empty — please upload a valid resume first.")
    if not job_description or not job_description.strip():
        raise AIEngineError("Job description is empty — please paste a job description first.")

    client = _get_client()
    prompt = _build_prompt(resume_text, job_description)

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=4096,
            ),
        )
    except Exception as exc:
        error_text = str(exc).lower()
        if "api key not valid" in error_text or "api_key_invalid" in error_text or "permission" in error_text or "401" in error_text:
            raise AIEngineError(
                "Authentication with the AI service failed. Please check that your "
                "GEMINI_API_KEY is correct, freshly copied, and active."
            ) from exc
        if "quota" in error_text or "rate" in error_text or "429" in error_text:
            raise AIEngineError(
                "The free AI quota has been used up for now, or too many requests were "
                "sent at once. Please wait a minute and try again."
            ) from exc
        raise AIEngineError(f"Unexpected error while calling the AI service: {exc}") from exc

    if not response or not getattr(response, "text", None):
        raise AIEngineError("The AI returned an empty response. Please try again.")

    raw_text = response.text

    data = _extract_json(raw_text)
    data = _validate_result_shape(data)
    return data
