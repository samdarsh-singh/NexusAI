"""
PDF generator for tailored resumes using reportlab.
Produces a clean, ATS-friendly PDF — no diff highlights.
"""

import io
from typing import List, Dict

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------

def _build_styles():
    base = getSampleStyleSheet()

    heading = ParagraphStyle(
        "SectionHeading",
        parent=base["Normal"],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1a1a1a"),
        spaceAfter=4,
        spaceBefore=10,
        fontName="Helvetica-Bold",
    )

    body = ParagraphStyle(
        "Body",
        parent=base["Normal"],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#333333"),
        spaceAfter=2,
        fontName="Helvetica",
    )

    bullet_style = ParagraphStyle(
        "BulletLine",
        parent=body,
        leftIndent=12,
        bulletIndent=0,
        spaceAfter=2,
    )

    return {"heading": heading, "body": body, "bullet": bullet_style}


# ---------------------------------------------------------------------------
# Text → flowables
# ---------------------------------------------------------------------------

SECTION_HEADING_RE = __import__("re").compile(
    r"^(SUMMARY|PROFESSIONAL SUMMARY|OBJECTIVE|PROFILE|ABOUT ME|"
    r"EXPERIENCE|WORK EXPERIENCE|PROFESSIONAL EXPERIENCE|EMPLOYMENT HISTORY|"
    r"SKILLS|TECHNICAL SKILLS|CORE COMPETENCIES|KEY SKILLS|TECHNOLOGIES|TECH STACK|"
    r"EDUCATION|ACADEMIC BACKGROUND|QUALIFICATIONS|"
    r"PROJECTS|PERSONAL PROJECTS|KEY PROJECTS|NOTABLE PROJECTS|"
    r"CERTIFICATIONS|CERTIFICATES|LICENSES)\s*$",
    __import__("re").IGNORECASE,
)


def _is_section_heading(line: str) -> bool:
    return bool(SECTION_HEADING_RE.match(line.strip()))


def _is_bullet(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith(("•", "-", "*", "–", "·"))


def text_to_flowables(text: str, styles: Dict) -> list:
    """Convert plain resume text to a list of reportlab Flowables."""
    flowables = []
    lines = text.splitlines()

    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        i += 1

        if not stripped:
            flowables.append(Spacer(1, 4))
            continue

        if _is_section_heading(stripped):
            flowables.append(Spacer(1, 6))
            flowables.append(Paragraph(stripped.upper(), styles["heading"]))
            flowables.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
            continue

        if _is_bullet(stripped):
            # Strip bullet character and render indented
            content = stripped.lstrip("•-*–· ").strip()
            # Escape HTML special chars for reportlab
            content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            flowables.append(Paragraph(f"• {content}", styles["bullet"]))
            continue

        # Regular paragraph line
        escaped = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        flowables.append(Paragraph(escaped, styles["body"]))

    return flowables


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_pdf(tailored_text: str, candidate_name: str = "") -> bytes:
    """
    Generate a PDF from tailored resume text.
    Returns raw PDF bytes.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title=f"Tailored Resume — {candidate_name}",
        author="NexusAI",
    )

    styles = _build_styles()
    flowables = text_to_flowables(tailored_text, styles)

    doc.build(flowables)
    buffer.seek(0)
    return buffer.read()
