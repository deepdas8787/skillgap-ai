"""
resume_parser.py
-----------------
Handles everything related to reading a resume PDF and turning it into
clean plain text that we can hand to the AI engine.

Functions:
    extract_text_from_pdf(uploaded_file)  -> (text, error)
    clean_resume_text(text)               -> str
    validate_resume_text(text)            -> (is_valid, error_message)
"""

import io
from pypdf import PdfReader


class ResumeParsingError(Exception):
    """Raised when a resume file cannot be read or is invalid."""
    pass


def extract_text_from_pdf(uploaded_file) -> str:
    """
    Extract raw text from an uploaded PDF file (Streamlit's UploadedFile object,
    or any file-like object / bytes).

    Returns the extracted text as a string.
    Raises ResumeParsingError with a friendly message if something goes wrong.
    """
    if uploaded_file is None:
        raise ResumeParsingError("No resume file was uploaded. Please upload a PDF resume.")

    try:
        # Streamlit's UploadedFile behaves like a file object, but we read bytes
        # to be safe regardless of how it's passed in.
        if hasattr(uploaded_file, "read"):
            file_bytes = uploaded_file.read()
        else:
            file_bytes = uploaded_file

        if not file_bytes:
            raise ResumeParsingError("The uploaded file appears to be empty. Please upload a valid PDF.")

        pdf_stream = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_stream)

        if len(reader.pages) == 0:
            raise ResumeParsingError("The PDF has no pages. Please upload a valid resume PDF.")

        extracted_pages = []
        for page in reader.pages:
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""
            extracted_pages.append(page_text)

        text = "\n".join(extracted_pages).strip()
        return text

    except ResumeParsingError:
        raise
    except Exception as exc:
        raise ResumeParsingError(
            "We couldn't read this PDF. It may be corrupted, password-protected, "
            "or a scanned image instead of a text-based PDF. "
            "Please try exporting your resume as a standard (non-scanned) PDF."
        ) from exc


def clean_resume_text(text: str) -> str:
    """Basic cleanup: remove extra blank lines and stray whitespace."""
    if not text:
        return ""
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def validate_resume_text(text: str):
    """
    Checks whether the extracted resume text is usable.
    Returns a tuple: (is_valid: bool, error_message: str or None)
    """
    if text is None or not text.strip():
        return False, (
            "We couldn't find any readable text in your resume. "
            "This usually happens with scanned/image-based PDFs. "
            "Please upload a text-based PDF (exported from Word, Google Docs, LaTeX, or Canva)."
        )

    word_count = len(text.split())
    if word_count < 20:
        return False, (
            "Your resume text seems too short to analyze properly "
            "(we only found a few words). Please check the file and try again."
        )

    return True, None
