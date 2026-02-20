"""
Resume tailoring engine.

Two-shot OpenAI strategy per section:
  Shot 1 (standard prompt)  → returns NO_SAFE_CHANGES_POSSIBLE or optimized text
  Shot 2 (retry prompt)     → only fires if Shot 1 returned nothing OR produced
                              text identical to the input (silent no-op detected)
                            → returns FAILURE_REASON (explicit) or optimized text
  Rule-based fallback       → fires when OpenAI is unavailable OR both shots
                              failed / returned FAILURE_REASON

Section flow:
  1. Parse resume into named sections
  2. For each tailorable section: two-shot OpenAI → rule-based fallback
  3. SKILLS section gets injected keywords appended (rule-based path only)
  4. Reconstruct tailored_text
  5. Recalculate ATS score
"""

import re
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Section parsing
# ---------------------------------------------------------------------------

SECTION_HEADERS = {
    "SUMMARY": re.compile(
        r"^(SUMMARY|PROFESSIONAL SUMMARY|OBJECTIVE|PROFILE|ABOUT ME)\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "EXPERIENCE": re.compile(
        r"^(EXPERIENCE|WORK EXPERIENCE|PROFESSIONAL EXPERIENCE|EMPLOYMENT HISTORY|WORK HISTORY)\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "SKILLS": re.compile(
        r"^(SKILLS|TECHNICAL SKILLS|CORE COMPETENCIES|KEY SKILLS|TECHNOLOGIES|TECH STACK)\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "EDUCATION": re.compile(
        r"^(EDUCATION|ACADEMIC BACKGROUND|QUALIFICATIONS)\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "PROJECTS": re.compile(
        r"^(PROJECTS|PERSONAL PROJECTS|KEY PROJECTS|NOTABLE PROJECTS)\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "CERTIFICATIONS": re.compile(
        r"^(CERTIFICATIONS|CERTIFICATES|LICENSES)\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
}

TAILORABLE_SECTIONS = {"EXPERIENCE", "SUMMARY", "PROJECTS", "SKILLS"}


def parse_sections(text: str) -> Dict[str, str]:
    hits: List[Tuple[int, int, str]] = []
    for name, pattern in SECTION_HEADERS.items():
        for m in pattern.finditer(text):
            hits.append((m.start(), m.end(), name))

    if not hits:
        return {"HEADER": text}

    hits.sort(key=lambda x: x[0])

    sections: Dict[str, str] = {}
    if hits[0][0] > 0:
        sections["HEADER"] = text[: hits[0][0]]

    for i, (start, end, name) in enumerate(hits):
        body_end = hits[i + 1][0] if i + 1 < len(hits) else len(text)
        key = name if name not in sections else f"{name}_{i}"
        sections[key] = text[start:body_end]

    return sections


def reconstruct_text(sections: Dict[str, str]) -> str:
    return "\n".join(sections.values())


# ---------------------------------------------------------------------------
# Shot 1 — Standard ATS prompt
# ---------------------------------------------------------------------------

_SHOT1_SYSTEM = (
    "You are a professional ATS resume optimizer for senior backend engineers.\n\n"
    "Your task is to TAILOR a resume section for a SPECIFIC job,\n"
    "WITHOUT inventing experience or lying.\n\n"
    "==================================================\n"
    "STRICT RULES (NON-NEGOTIABLE)\n"
    "==================================================\n\n"
    "- You may ONLY rephrase or slightly expand existing content\n"
    "- You may add keywords ONLY if they logically fit existing experience\n"
    "- You MUST NOT invent:\n"
    "  - new companies\n"
    "  - new tools not implied by experience\n"
    "  - years of experience\n"
    "- If a missing skill cannot be safely added, IGNORE it\n"
    "- Output MUST remain ATS-friendly (simple text, no symbols)\n\n"
    "==================================================\n"
    "OBJECTIVE\n"
    "==================================================\n\n"
    "- Improve keyword alignment with the job description\n"
    "- Preserve factual accuracy\n"
    "- Improve ATS readability\n"
    "- Make minimal but effective changes\n\n"
    "==================================================\n"
    "OUTPUT FORMAT (EXACT)\n"
    "==================================================\n\n"
    'Optimized Section:\n"""\n<final optimized text>\n"""\n\n'
    "Change Summary:\n"
    "- <what changed and why>\n"
    "- <what keyword was added or improved>\n\n"
    "If no safe improvement is possible, return:\n"
    "NO_SAFE_CHANGES_POSSIBLE"
)

_SHOT1_USER = """\
==================================================
INPUTS
==================================================

Original Resume Section:
\"\"\"
{resume_section_text}
\"\"\"

Job Description (Reference Only):
\"\"\"
{job_description}
\"\"\"

Matched Skills:
{matched_skills}

Missing Skills (DO NOT invent experience):
{missing_skills}
"""


# ---------------------------------------------------------------------------
# Shot 2 — Retry / aggressive prompt
# ---------------------------------------------------------------------------

_SHOT2_SYSTEM = (
    "You are a senior resume optimization engine.\n"
    "Your previous attempts to tailor this resume have FAILED.\n\n"
    "This time, you MUST either:\n"
    "(A) produce a measurable improvement\n"
    "OR\n"
    "(B) explicitly FAIL with a concrete explanation.\n\n"
    "SILENT NO-OP IS NOT ALLOWED.\n\n"
    "==================================================\n"
    "ABSOLUTE RULES (NO EXCEPTIONS)\n"
    "==================================================\n\n"
    "1. You MUST address AT LEAST ONE missing skill\n"
    "   OR explain why NONE can be safely added.\n\n"
    "2. You MUST modify AT LEAST ONE sentence\n"
    "   OR explicitly return FAILURE.\n\n"
    "3. You MUST NOT invent:\n"
    "   - companies\n"
    "   - tools not implied by experience\n"
    "   - years of experience\n"
    "   - responsibilities not logically supported\n\n"
    "4. Keyword alignment is REQUIRED.\n"
    "   If a missing skill appears in the JD and\n"
    "   logically fits existing experience, you MUST inject it.\n\n"
    "==================================================\n"
    "SUCCESS CRITERIA\n"
    "==================================================\n\n"
    "A response is SUCCESS only if:\n"
    "- At least one missing skill is integrated\n"
    "- OR wording is changed to improve ATS keyword density\n"
    "- AND the change is explainable\n\n"
    "Otherwise, the response is FAILURE.\n\n"
    "==================================================\n"
    "OUTPUT FORMAT (STRICT)\n"
    "==================================================\n\n"
    "If SUCCESS:\n\n"
    'Optimized Section:\n"""\n<modified section text>\n"""\n\n'
    "Changes Made:\n"
    "- <exact sentence changed>\n"
    "- <skill or keyword improved>\n"
    "- <reason>\n\n"
    "Skills Addressed:\n"
    "- <skill 1>\n"
    "- <skill 2>\n\n"
    "If FAILURE (ONLY if genuinely impossible):\n\n"
    "FAILURE_REASON:\n"
    "- <specific reason why no safe changes were possible>\n"
    "- <which missing skills were rejected and why>\n\n"
    "==================================================\n"
    "FINAL WARNING\n"
    "==================================================\n\n"
    "Returning the original text unchanged\n"
    "WITHOUT FAILURE_REASON\n"
    "IS A HARD FAILURE.\n\n"
    "Do not be conservative.\n"
    "Do not be polite.\n"
    "Do not optimize for safety.\n"
    "Optimize for ATS alignment WITH HONESTY."
)

_SHOT2_USER = """\
==================================================
INPUTS
==================================================

Resume Section (SOURCE OF TRUTH):
\"\"\"
{resume_section_text}
\"\"\"

Target Job Description:
\"\"\"
{job_description}
\"\"\"

Matched Skills (already present):
{matched_skills}

Missing Skills (ATS gaps):
{missing_skills}
"""


# ---------------------------------------------------------------------------
# Shared user message builder
# ---------------------------------------------------------------------------

def _build_user_message(template: str, section_text: str, job_description: str,
                        matched_skills: List[str], missing_skills: List[str]) -> str:
    return template.format(
        resume_section_text=section_text.strip(),
        job_description=job_description.strip()[:1500],
        matched_skills=", ".join(matched_skills) if matched_skills else "none",
        missing_skills=", ".join(missing_skills) if missing_skills else "none",
    )


# ---------------------------------------------------------------------------
# Response parsers
# ---------------------------------------------------------------------------

_OPTIMIZED_SECTION_RE = re.compile(
    r'Optimized Section:\s*"""\s*(.*?)\s*"""',
    re.DOTALL,
)


def _parse_shot1_response(raw: str) -> Optional[Tuple[str, List[str]]]:
    """
    Parse Shot 1 output.
    Returns (optimized_text, change_bullets) or None.
    None is returned when: NO_SAFE_CHANGES_POSSIBLE, parse failure.
    """
    raw = raw.strip()
    if raw.startswith("NO_SAFE_CHANGES_POSSIBLE"):
        return None

    section_match = _OPTIMIZED_SECTION_RE.search(raw)
    if not section_match:
        return None

    optimized_text = section_match.group(1).strip()

    bullets: List[str] = []
    summary_match = re.search(r"Change Summary:\s*((?:- .+\n?)+)", raw, re.DOTALL)
    if summary_match:
        bullets = [
            line.lstrip("- ").strip()
            for line in summary_match.group(1).splitlines()
            if line.strip().startswith("-")
        ]

    return optimized_text, bullets


# Shot 2 has three possible extraction zones: Changes Made + Skills Addressed,
# or FAILURE_REASON.  Returns None on FAILURE_REASON / parse failure.
def _parse_shot2_response(raw: str) -> Optional[Tuple[str, List[str], List[str]]]:
    """
    Parse Shot 2 output.
    Returns (optimized_text, change_bullets, skills_addressed) or None.
    None means FAILURE_REASON was returned or the section is unchanged.
    """
    raw = raw.strip()
    if raw.startswith("FAILURE_REASON"):
        return None

    section_match = _OPTIMIZED_SECTION_RE.search(raw)
    if not section_match:
        return None

    optimized_text = section_match.group(1).strip()

    changes: List[str] = []
    changes_match = re.search(r"Changes Made:\s*((?:- .+\n?)+)", raw, re.DOTALL)
    if changes_match:
        changes = [
            line.lstrip("- ").strip()
            for line in changes_match.group(1).splitlines()
            if line.strip().startswith("-")
        ]

    skills: List[str] = []
    skills_match = re.search(r"Skills Addressed:\s*((?:- .+\n?)+)", raw, re.DOTALL)
    if skills_match:
        skills = [
            line.lstrip("- ").strip()
            for line in skills_match.group(1).splitlines()
            if line.strip().startswith("-")
        ]

    return optimized_text, changes, skills


def _parse_shot2_failure_reasons(raw: str) -> List[str]:
    """Extract bullet reasons from a FAILURE_REASON block."""
    match = re.search(r"FAILURE_REASON:\s*((?:- .+\n?)+)", raw, re.DOTALL)
    if not match:
        return ["No safe changes possible (no further detail provided)"]
    return [
        line.lstrip("- ").strip()
        for line in match.group(1).splitlines()
        if line.strip().startswith("-")
    ]


# ---------------------------------------------------------------------------
# Two-shot OpenAI orchestrator
# ---------------------------------------------------------------------------

class _SectionResult:
    """Value object returned by the two-shot OpenAI call."""
    __slots__ = ("optimized_text", "change_bullets", "skills_addressed",
                 "shot_used", "failure_reasons")

    def __init__(
        self,
        optimized_text: Optional[str] = None,
        change_bullets: Optional[List[str]] = None,
        skills_addressed: Optional[List[str]] = None,
        shot_used: int = 0,        # 1 or 2 on success; 0 on failure
        failure_reasons: Optional[List[str]] = None,
    ):
        self.optimized_text = optimized_text
        self.change_bullets = change_bullets or []
        self.skills_addressed = skills_addressed or []
        self.shot_used = shot_used
        self.failure_reasons = failure_reasons or []

    @property
    def succeeded(self) -> bool:
        return self.optimized_text is not None


def _call_openai(
    system: str,
    user: str,
    api_key: str,
    max_tokens: int = 1200,
    temperature: float = 0.2,
) -> str:
    """Low-level OpenAI call; returns raw string content."""
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


def _optimize_section(
    section_name: str,
    section_text: str,
    job_description: str,
    matched_skills: List[str],
    missing_skills: List[str],
) -> _SectionResult:
    """
    Two-shot OpenAI optimisation for a single resume section.

    Shot 1 (standard prompt):
      - Returns result if text is meaningfully changed
      - Triggers Shot 2 if: NO_SAFE_CHANGES_POSSIBLE OR text == original

    Shot 2 (retry/aggressive prompt):
      - Returns result on SUCCESS output
      - Returns failure if FAILURE_REASON is returned
      - All failure bullets are surfaced in change_summary

    Returns _SectionResult (succeeded=False means fall through to rule-based).
    """
    try:
        from app.core.config import settings
        if not settings.OPENAI_API_KEY:
            return _SectionResult()
        api_key = settings.OPENAI_API_KEY
    except Exception:
        return _SectionResult()

    original_stripped = section_text.strip()

    # ---------- Shot 1 ----------
    shot1_raw: str = ""
    try:
        shot1_raw = _call_openai(
            system=_SHOT1_SYSTEM,
            user=_build_user_message(
                _SHOT1_USER, section_text, job_description, matched_skills, missing_skills
            ),
            api_key=api_key,
        )
    except Exception:
        return _SectionResult()  # OpenAI unavailable → rule-based

    shot1 = _parse_shot1_response(shot1_raw)

    if shot1 is not None:
        optimized_text, bullets = shot1
        # Detect silent no-op: model returned original text unchanged
        if optimized_text.strip() == original_stripped:
            shot1 = None  # treat as if it returned NO_SAFE_CHANGES_POSSIBLE

    if shot1 is not None:
        return _SectionResult(
            optimized_text=shot1[0],
            change_bullets=shot1[1],
            shot_used=1,
        )

    # ---------- Shot 2 (retry) ----------
    shot2_raw: str = ""
    try:
        shot2_raw = _call_openai(
            system=_SHOT2_SYSTEM,
            user=_build_user_message(
                _SHOT2_USER, section_text, job_description, matched_skills, missing_skills
            ),
            api_key=api_key,
            temperature=0.4,  # slightly higher — push through the conservatism
        )
    except Exception:
        return _SectionResult()

    shot2 = _parse_shot2_response(shot2_raw)

    if shot2 is not None:
        optimized_text, changes, skills = shot2
        # Guard: if the model still returned original text, treat as failure
        if optimized_text.strip() == original_stripped:
            shot2 = None

    if shot2 is not None:
        return _SectionResult(
            optimized_text=shot2[0],
            change_bullets=shot2[1],
            skills_addressed=shot2[2],
            shot_used=2,
        )

    # Both shots failed — surface FAILURE_REASON bullets if available
    failure_reasons = _parse_shot2_failure_reasons(shot2_raw)
    return _SectionResult(failure_reasons=failure_reasons)


# ---------------------------------------------------------------------------
# Skill-context matching (rule-based fallback)
# ---------------------------------------------------------------------------

SKILL_CONTEXT_MAP: Dict[str, List[str]] = {
    "kubernetes": ["deploy", "container", "docker", "k8s", "cluster", "orchestrat", "pod", "helm"],
    "docker": ["container", "image", "deploy", "compose", "microservice"],
    "terraform": ["infrastructure", "iac", "cloud", "provision", "aws", "azure", "gcp"],
    "aws": ["cloud", "ec2", "s3", "lambda", "rds", "iam", "cloudformation"],
    "azure": ["cloud", "microsoft", "devops", "pipeline", "blob"],
    "gcp": ["cloud", "google", "bigquery", "gke", "pubsub"],
    "ci/cd": ["pipeline", "jenkins", "github actions", "gitlab", "deploy", "build", "automat"],
    "jenkins": ["pipeline", "build", "ci", "deploy", "automat"],
    "github actions": ["pipeline", "workflow", "ci", "deploy", "automat"],
    "graphql": ["api", "query", "schema", "rest", "endpoint"],
    "redis": ["cache", "queue", "session", "pubsub", "memory"],
    "elasticsearch": ["search", "index", "log", "kibana", "analyt"],
    "kafka": ["stream", "message", "queue", "event", "broker"],
    "machine learning": ["model", "train", "data", "predict", "algorithm", "ml", "ai"],
    "pytorch": ["model", "train", "neural", "deep learning", "ml"],
    "tensorflow": ["model", "train", "neural", "deep learning", "ml"],
    "react": ["frontend", "ui", "component", "javascript", "web"],
    "typescript": ["javascript", "frontend", "node", "type", "ts"],
    "fastapi": ["api", "python", "rest", "endpoint", "backend"],
    "django": ["python", "web", "backend", "rest", "api"],
    "postgresql": ["database", "sql", "db", "postgres", "query"],
    "mongodb": ["database", "nosql", "document", "db"],
}


def _skill_context_keywords(skill: str) -> List[str]:
    lower = skill.lower()
    return SKILL_CONTEXT_MAP.get(lower, re.split(r"[\s\-/]+", lower))


def find_related_bullets(skill: str, section_text: str) -> List[str]:
    context_words = _skill_context_keywords(skill)
    related = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped or len(stripped) < 10:
            continue
        if any(kw in stripped.lower() for kw in context_words):
            related.append(stripped)
    return related


def _rephrase_rule_based(bullet: str, skill: str) -> str:
    return f"{bullet.rstrip('.,;:')}, leveraging {skill}"


# ---------------------------------------------------------------------------
# Skills section manipulation
# ---------------------------------------------------------------------------

def _append_skills_to_section(skills_section: str, new_skills: List[str]) -> str:
    if not new_skills:
        return skills_section
    skills_str = ", ".join(new_skills)
    lines = skills_section.rstrip().splitlines()
    if lines:
        lines[-1] = f"{lines[-1].rstrip('.,;:')}, {skills_str}"
        return "\n".join(lines) + "\n"
    return skills_section + f"\n{skills_str}\n"


# ---------------------------------------------------------------------------
# Main tailoring function
# ---------------------------------------------------------------------------

def tailor_resume(
    resume_text: str,
    job_text: str,
    missing_skills: List[str],
    matched_skills: List[str],
    ats_score_before: float,
) -> Dict[str, Any]:
    """
    Core tailoring algorithm.

    Per tailorable section (EXPERIENCE, SUMMARY, PROJECTS):
      1. Two-shot OpenAI (standard → retry on no-op/failure)
         - On success: write optimized section, record change_summary entries
         - On failure: record FAILURE_REASON bullets in change_summary, fall through
      2. Rule-based bullet injection (when both shots fail or no API key)
         - Per missing_skill: find related bullet → append keyword
         - Skills with no related bullet: logged as gap

    SKILLS section:
      - Rule-based injections always appended explicitly
      - AI is expected to update SKILLS inline when it handles the section

    Returns {tailored_text, change_summary, ats_score_before, ats_score_after}
    """
    from app.services.ats.scorer import calculate_ats_score

    sections = parse_sections(resume_text)
    change_summary: List[Dict[str, Any]] = []
    rule_based_injected_skills: List[str] = []

    experience_key = next(
        (k for k in sections if k == "EXPERIENCE" or k.startswith("EXPERIENCE_")), None
    )
    skills_key = next(
        (k for k in sections if k == "SKILLS" or k.startswith("SKILLS_")), None
    )

    # Track which sections the AI successfully handled so rule-based knows
    # whether to run at all
    ai_succeeded_for: set = set()

    # -----------------------------------------------------------------
    # Pass 1: Two-shot OpenAI per tailorable section (excluding SKILLS)
    # -----------------------------------------------------------------
    for sec_key in list(sections.keys()):
        base = sec_key.split("_")[0]
        if base not in TAILORABLE_SECTIONS or base == "SKILLS":
            continue

        section_text = sections[sec_key]
        if not section_text.strip():
            continue

        result = _optimize_section(
            section_name=base,
            section_text=section_text,
            job_description=job_text,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
        )

        if result.succeeded:
            # Preserve the section header line (e.g. "EXPERIENCE\n")
            header_line = section_text.split("\n")[0]
            sections[sec_key] = header_line + "\n" + result.optimized_text + "\n"
            ai_succeeded_for.add(base)

            shot_label = f"Shot {result.shot_used} AI"

            # Change bullets from the model
            for bullet in result.change_bullets:
                change_summary.append({
                    "section_name": base.capitalize(),
                    "before_text": "",
                    "after_text": "",
                    "reason": bullet,
                    "injected": True,
                    "skill": "ai-optimized",
                })

            # Skills explicitly addressed (Shot 2 only)
            for skill in result.skills_addressed:
                change_summary.append({
                    "section_name": base.capitalize(),
                    "before_text": "",
                    "after_text": "",
                    "reason": f"Skill addressed by {shot_label}: {skill}",
                    "injected": True,
                    "skill": skill,
                })

        else:
            # Both shots failed — surface failure reasons as gap entries
            for reason in result.failure_reasons:
                change_summary.append({
                    "section_name": f"{base.capitalize()} (AI Failed)",
                    "before_text": "",
                    "after_text": "",
                    "reason": reason,
                    "injected": False,
                    "skill": "ai-failed",
                })
            # Fall through to rule-based below for this section

    # -----------------------------------------------------------------
    # Pass 2: Rule-based bullet injection for skills AI did NOT handle
    # -----------------------------------------------------------------
    # Only skip rule-based for EXPERIENCE if AI succeeded for EXPERIENCE.
    # If AI was not available at all, ai_succeeded_for is empty → full rule-based.
    run_rule_based = "EXPERIENCE" not in ai_succeeded_for

    if run_rule_based and experience_key:
        for skill in missing_skills:
            related = find_related_bullets(skill, sections[experience_key])
            if related:
                original_bullet = related[0]
                tailored_bullet = _rephrase_rule_based(original_bullet, skill)
                sections[experience_key] = sections[experience_key].replace(
                    original_bullet, tailored_bullet, 1
                )
                rule_based_injected_skills.append(skill)
                change_summary.append({
                    "section_name": "Experience",
                    "before_text": original_bullet,
                    "after_text": tailored_bullet,
                    "reason": (
                        f"Added '{skill}' (required by JD) — "
                        "related context found; rule-based injection"
                    ),
                    "injected": True,
                    "skill": skill,
                })
            else:
                change_summary.append({
                    "section_name": "Skills Gap",
                    "before_text": "",
                    "after_text": "",
                    "reason": (
                        f"Skill gap — not injected: '{skill}'. "
                        "No related experience bullets found. "
                        "Consider adding this skill if you genuinely have it."
                    ),
                    "injected": False,
                    "skill": skill,
                })
    elif run_rule_based:
        for skill in missing_skills:
            change_summary.append({
                "section_name": "Skills Gap",
                "before_text": "",
                "after_text": "",
                "reason": (
                    f"Skill gap — not injected: '{skill}'. "
                    "No experience section found in resume."
                ),
                "injected": False,
                "skill": skill,
            })

    # -----------------------------------------------------------------
    # Pass 3: Append rule-based injected skills to SKILLS section
    # -----------------------------------------------------------------
    if rule_based_injected_skills:
        if skills_key:
            old_skills = sections[skills_key]
            new_skills = _append_skills_to_section(old_skills, rule_based_injected_skills)
            sections[skills_key] = new_skills
            change_summary.append({
                "section_name": "Skills",
                "before_text": old_skills.strip(),
                "after_text": new_skills.strip(),
                "reason": (
                    f"Appended injected keywords to Skills section: "
                    f"{', '.join(rule_based_injected_skills)}"
                ),
                "injected": True,
                "skill": "multiple",
            })
        else:
            block = "SKILLS\n" + ", ".join(rule_based_injected_skills) + "\n"
            sections["SKILLS_NEW"] = block
            change_summary.append({
                "section_name": "Skills",
                "before_text": "",
                "after_text": block.strip(),
                "reason": (
                    f"Added new Skills section: {', '.join(rule_based_injected_skills)}"
                ),
                "injected": True,
                "skill": "multiple",
            })

    # -----------------------------------------------------------------
    # Reconstruct + rescore
    # -----------------------------------------------------------------
    tailored_text = reconstruct_text(sections)
    score_result = calculate_ats_score(job_text, tailored_text)

    return {
        "tailored_text": tailored_text,
        "change_summary": change_summary,
        "ats_score_before": ats_score_before,
        "ats_score_after": score_result["overall_score"],
    }
