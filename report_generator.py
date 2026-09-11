"""
report_generator.py
--------------------
Builds a downloadable PDF "Career Report" summarizing the AI analysis,
using the fpdf2 library (pure Python, no external system dependencies).
"""

from datetime import datetime
from fpdf import FPDF


class ReportGenerationError(Exception):
    pass


def _safe(text: str) -> str:
    """fpdf's built-in fonts only support latin-1; replace unsupported characters."""
    if text is None:
        return ""
    return str(text).encode("latin-1", "replace").decode("latin-1")


class CareerReportPDF(FPDF):
    def header(self):
        self.set_fill_color(99, 102, 241)  # indigo
        self.rect(0, 0, 210, 22, style="F")
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 16)
        self.set_xy(10, 6)
        self.cell(0, 10, _safe("SkillGap AI — Career Report"), ln=True)
        self.set_font("Helvetica", "", 9)
        self.set_xy(10, 15)
        self.cell(0, 6, _safe(f"Generated on {datetime.now().strftime('%d %b %Y, %H:%M')}"))
        self.set_text_color(0, 0, 0)
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, title: str):
        self.ln(4)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(79, 70, 229)
        self.cell(0, 8, _safe(title), ln=True)
        self.set_draw_color(79, 70, 229)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
        self.set_text_color(0, 0, 0)

    def body_text(self, text: str, bullet: bool = False):
        self.set_font("Helvetica", "", 10.5)
        prefix = "- " if bullet else ""
        self.multi_cell(0, 6, _safe(prefix + text))
        self.ln(1)


def generate_report(
    student_name: str,
    target_role: str,
    analysis: dict,
) -> bytes:
    """
    Builds the full PDF report and returns it as raw bytes, ready to be
    handed to Streamlit's download_button.
    """
    try:
        pdf = CareerReportPDF()
        pdf.set_auto_page_break(auto=True, margin=18)
        pdf.add_page()

        # --- Profile section ---
        pdf.section_title("Student & Target Role")
        pdf.body_text(f"Student: {student_name or 'Not provided'}")
        pdf.body_text(f"Target Role: {target_role or analysis.get('target_role', 'Not specified')}")
        pdf.body_text(f"Candidate Summary: {analysis.get('candidate_summary', 'N/A')}")

        # --- Match scores ---
        pdf.section_title("Match Scores")
        pdf.body_text(f"Overall Job Match: {analysis.get('job_match_percentage', 0)}%")
        pdf.body_text(f"Experience Match: {analysis.get('experience_match_percentage', 0)}%")
        pdf.body_text(f"Skills Found: {len(analysis.get('skills_found', []))}")
        pdf.body_text(f"Skills Missing: {len(analysis.get('skills_missing', []))}")

        # --- Skills found ---
        pdf.section_title("Skills You Have")
        skills_found = analysis.get("skills_found", [])
        if skills_found:
            names = ", ".join(s.get("name", "") for s in skills_found)
            pdf.body_text(names)
        else:
            pdf.body_text("No matching skills detected.")

        # --- Skills missing ---
        pdf.section_title("Skills You Are Missing")
        for skill in analysis.get("skills_missing", []):
            pdf.set_font("Helvetica", "B", 10.5)
            pdf.multi_cell(0, 6, _safe(f"{skill.get('name', '')}  (Priority: {skill.get('priority', 'N/A')})"))
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(
                0, 6,
                _safe(
                    f"Why needed: {skill.get('why_needed', '')}\n"
                    f"Current level: {skill.get('current_level', 'None')} -> "
                    f"Required level: {skill.get('required_level', 'N/A')}"
                ),
            )
            pdf.ln(1)

        # --- Strengths ---
        pdf.section_title("Strengths")
        for item in analysis.get("strengths", []):
            pdf.body_text(item, bullet=True)

        # --- Weaknesses ---
        pdf.section_title("Areas To Improve")
        for item in analysis.get("weaknesses", []):
            pdf.body_text(item, bullet=True)

        # --- Roadmap ---
        pdf.section_title("Personalized Learning Roadmap")
        for step in analysis.get("learning_roadmap", []):
            pdf.set_font("Helvetica", "B", 10.5)
            pdf.multi_cell(
                0, 6,
                _safe(f"{step.get('step_number', '')}. {step.get('title', '')}  "
                      f"[{step.get('difficulty', '')}, {step.get('estimated_time', '')}]")
            )
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(
                0, 6,
                _safe(
                    f"Why it matters: {step.get('why_it_matters', '')}\n"
                    f"Suggested practice: {step.get('suggested_practice', '')}"
                ),
            )
            pdf.ln(1)

        # --- Projects ---
        pdf.section_title("Recommended Projects")
        for proj in analysis.get("recommended_projects", []):
            pdf.set_font("Helvetica", "B", 10.5)
            pdf.multi_cell(0, 6, _safe(proj.get("title", "")))
            pdf.set_font("Helvetica", "", 10)
            skills = ", ".join(proj.get("skills_practiced", []))
            pdf.multi_cell(
                0, 6,
                _safe(
                    f"{proj.get('description', '')}\n"
                    f"Skills practiced: {skills}\n"
                    f"Why it helps: {proj.get('why_it_helps', '')}"
                ),
            )
            pdf.ln(1)

        # --- Education / Experience ---
        pdf.section_title("Education & Experience Summary")
        pdf.body_text(f"Education: {analysis.get('education_summary', 'Not specified')}")
        pdf.body_text(f"Experience: {analysis.get('experience_summary', 'Not specified')}")

        output = pdf.output(dest="S")
        if isinstance(output, str):
            output = output.encode("latin-1", "replace")
        return bytes(output)

    except Exception as exc:
        raise ReportGenerationError(f"Could not generate the PDF report: {exc}") from exc
