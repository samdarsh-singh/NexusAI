
from typing import Dict, Any, List
from app.services.skills.extraction import extract_skills, flatten_skills
from app.services.scoring.ats_logic import extract_keywords  # Re-use Spacy noun extraction
import re

def calculate_experience_score(job_text: str, resume_text: str) -> float:
    """
    Heuristic to check if resume meets years of experience.
    Looks for "X+ years" patterns.
    """
    # Find required years in Job
    req_years = 0
    # Match patterns like "5+ years", "3-5 years", "min 4 years"
    matches = re.findall(r'(\d+)\+?\s*[-to]*\s*(\d*)?\s*years', job_text.lower())
    if matches:
        # Take the maximum required year found as the "seniority level" assumption
        # e.g., "5+ years" -> 5
        nums = []
        for m in matches:
            if m[0]: nums.append(int(m[0]))
            if m[1]: nums.append(int(m[1]))
        if nums:
            req_years = max(nums)
            
    # Find profile years (Total experience assumption)
    # This is hard to extract perfectly from text without structured data, 
    # so we assume a baseline or look for "Experience" section dates.
    # For now, we'll do a keyword match on high seniority words if no explicit years found.
    
    if req_years == 0:
        return 100.0 # No strict requirement found
        
    # Heuristic: Check for specific "years" mentions in resume near "experience"
    # Simplified: Check for "Senior", "Lead", "Staff" if job requires high years (5+)
    resume_lower = resume_text.lower()
    
    if req_years >= 5:
        if "senior" in resume_lower or "lead" in resume_lower or "staff" in resume_lower or "architect" in resume_lower:
            return 100.0
        return 50.0 # Penalty for junior title on senior role
    
    return 100.0 # Assume valid for junior roles

def calculate_ats_score(job_text: str, resume_text: str) -> Dict[str, Any]:
    """
    Deterministic Weighted Scoring System.
    Weights:
    - Hard Skills (Languages, Frameworks, Tools): 60%
    - Keywords (Nouns/Context): 25%
    - Experience/semantic (Heuristic): 15%
    """
    
    # 1. Skill Extraction
    job_skills_map = extract_skills(job_text)
    resume_skills_map = extract_skills(resume_text)
    
    job_flat = flatten_skills(job_skills_map)
    resume_flat = flatten_skills(resume_skills_map)
    
    # Skill Match Score (60%)
    if not job_flat:
        skill_score = 100.0 # No hard skills required?
    else:
        matched_skills = job_flat.intersection(resume_flat)
        missing_skills = job_flat - resume_flat
        skill_score = (len(matched_skills) / len(job_flat)) * 100
    
    # 2. Keyword Context Score (25%) - Using Spacy Nouns
    # Re-using existing logic but keeping it light
    job_kws = set(extract_keywords(job_text))
    resume_kws = set(extract_keywords(resume_text))
    
    if not job_kws:
        kw_score = 0.0
    else:
        matched_kws = job_kws.intersection(resume_kws)
        kw_score = (len(matched_kws) / len(job_kws)) * 100

    # 3. Experience / Heuristic Score (15%)
    exp_score = calculate_experience_score(job_text, resume_text)
    
    # Final Weighted Score
    final_score = (skill_score * 0.60) + (kw_score * 0.25) + (exp_score * 0.15)
    
    return {
        "overall_score": round(final_score, 1),
        "breakdown": {
            "skill_match": round(skill_score, 1),
            "keyword_match": round(kw_score, 1),
            "experience_match": round(exp_score, 1)
        },
        "matched_skills": list(job_flat.intersection(resume_flat)),
        "missing_skills": list(job_flat - resume_flat),
        "job_skills": list(job_flat)
    }
