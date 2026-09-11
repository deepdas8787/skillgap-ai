"""
ai_engine.py
------------
SkillGap AI - Gemini AI Engine
"""

import os
import json
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL_NAME = "gemini-3.5-flash-lite"


class AIEngineError(Exception):
    """Raised when something goes wrong with the Gemini AI service."""
    pass


def _get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise AIEngineError(
            "No Gemini API key found. Please add GEMINI_API_KEY "
            "to your Streamlit Secrets or .env file."
        )

    try:
        return genai.Client(api_key=api_key)
    except Exception as exc:
        raise AIEngineError(
            f"Could not initialize Gemini AI client: {exc}"
        ) from exc


def _build_prompt(resume_text: str, job_description: str) -> str:
    return f"""
You are an expert technical recruiter and career coach AI
inside a product called "SkillGap AI".

Compare the student's resume with the job description.

Do NOT invent skills that are not present in the resume.
Do NOT invent requirements that are not present in the job description.
Base match percentages on actual overlap.
Be specific and useful.

RESUME:
\"\"\"
{resume_text}
\"\"\"

JOB DESCRIPTION:
\"\"\"
{job_description}
\"\"\"

Return ONLY valid JSON. Do not use markdown or explanations.

Use exactly this structure:

{{
  "job_match_percentage": 0,
  "experience_match_percentage": 0,
  "candidate_summary": "2-3 sentence summary",
  "target_role": "Target role",

  "skills_found": [
    {{
      "name": "Python",
      "category": "Programming Language"
    }}
  ],

  "skills_missing": [
    {{
      "name": "Docker",
      "why_needed": "Why this skill is required",
      "current_level": "None",
      "required_level": "Intermediate",
      "priority": "High"
    }}
  ],

  "strengths": [
    "Genuine strength based on the resume"
  ],

  "weaknesses": [
    "Genuine weakness or area to improve"
  ],

  "learning_roadmap": [
    {{
      "step_number": 1,
      "title": "Topic to learn",
      "why_it_matters": "Why it matters",
      "difficulty": "Beginner",
      "suggested_practice": "Concrete practice task",
      "estimated_time": "1 week"
    }}
  ],

  "recommended_projects": [
    {{
      "title": "Project title",
      "description": "Project description",
      "skills_practiced": ["Python", "Docker"],
      "why_it_helps": "How this closes the skill gap"
    }}
  ],

  "education_summary": "Education summary",
  "experience_summary": "Experience summary"
}}

RULES:

- skills_found must contain relevant technical and soft skills
  found in the resume and relevant to the job.
- skills_missing should contain important job skills not shown
  in the resume.
- Provide 4-8 missing skills.
- Order missing skills High, Medium, Low.
- learning_roadmap must contain 5-8 steps.
- recommended_projects must contain 2-4 projects.
- Projects must target missing skills.
- Keep everything concise and specific.
- Return ONLY the JSON object.
"""


def _extract_json(raw_text: str) -> dict:
    text = raw_text.strip()

    fence_match = re.search(
        r"```(?:json)?\s*(\{.*\})\s*```",
        text,
        re.DOTALL
    )

    if fence_match:
        text = fence_match.group(1)
    else:
        first_brace = text.find("{")
        last_brace = text.rfind("}")

        if (
            first_brace != -1
            and last_brace != -1
            and last_brace > first_brace
        ):
            text = text[first_brace:last_brace + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise AIEngineError(
            "Gemini returned an invalid response. Please try again."
        ) from exc


def _validate_result_shape(data: dict) -> dict:
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

    for pct_key in (
        "job_match_percentage",
        "experience_match_percentage"
    ):
        try:
            data[pct_key] = max(
                0,
                min(100, int(data[pct_key]))
            )
        except (ValueError, TypeError):
            data[pct_key] = 0

    return data


def analyze_resume_vs_job(
    resume_text: str,
    job_description: str
) -> dict:

    if not resume_text or not resume_text.strip():
        raise AIEngineError(
            "Resume text is empty. Please upload a valid resume."
        )

    if not job_description or not job_description.strip():
        raise AIEngineError(
            "Job description is empty. Please paste a job description."
        )

    client = _get_client()

    prompt = _build_prompt(
        resume_text,
        job_description
    )

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

        if (
            "api key not valid" in error_text
            or "api_key_invalid" in error_text
            or "401" in error_text
            or "unauthorized" in error_text
            or "permission denied" in error_text
        ):
            raise AIEngineError(
                "Gemini API authentication failed. "
                "Please check your GEMINI_API_KEY."
            ) from exc

        if (
            "quota" in error_text
            or "rate limit" in error_text
            or "429" in error_text
        ):
            raise AIEngineError(
                "Gemini API quota or rate limit reached. "
                "Please wait and try again."
            ) from exc

        if "503" in error_text or "unavailable" in error_text:
            raise AIEngineError(
                "Gemini is temporarily overloaded. "
                "Please wait a few minutes and try again."
            ) from exc

        if "404" in error_text or "not found" in error_text:
            raise AIEngineError(
                f"The Gemini model '{MODEL_NAME}' is not available "
                "for your API key/project."
            ) from exc

        raise AIEngineError(
            f"Unexpected error while calling the AI service: {exc}"
        ) from exc

    if not response:
        raise AIEngineError(
            "Gemini returned no response. Please try again."
        )

    if not getattr(response, "text", None):
        raise AIEngineError(
            "Gemini returned an empty response. Please try again."
        )

    data = _extract_json(response.text)

    return _validate_result_shape(data)
