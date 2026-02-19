from typing import Dict, Any, List, Tuple
import spacy
from collections import Counter
import math
from app.core.config import settings
import openai

# Load Spacy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Spacy model not found. Downloading...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def extract_keywords(text: str) -> List[str]:
    """
    Extracts nouns and entities from text using Spacy.
    """
    doc = nlp(text.lower())
    keywords = [token.lemma_ for token in doc if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop]
    # Also entities
    entities = [ent.text.lower() for ent in doc.ents]
    return list(set(keywords + entities))

def calculate_keyword_score(job_description: str, resume_text: str) -> Tuple[float, Dict[str, Any], Dict[str, Any]]:
    """
    Calculates score based on keyword overlap.
    Returns: (score, missing_keywords, matched_keywords)
    """
    job_keywords = extract_keywords(job_description)
    resume_keywords = extract_keywords(resume_text)
    
    if not job_keywords:
        return 0, {}, {}

    job_counter = Counter(job_keywords)
    resume_counter = Counter(resume_keywords)
    
    matched = []
    missing = []
    
    hits = 0
    total_important = len(job_keywords) # Simplified: Treat all extracted nouns as important for now
    
    for kw in job_keywords:
        if resume_counter[kw] > 0:
            hits += 1
            matched.append(kw)
        else:
            missing.append(kw)
            
    score = (hits / total_important) * 100 if total_important > 0 else 0
    
    return score, {"count": len(missing), "top_5": missing[:5]}, {"count": len(matched), "top_5": matched[:5]}

def get_embedding(text: str) -> List[float]:
    """Generates embedding using OpenAI or Fake fallback."""
    if not settings.OPENAI_API_KEY:
        # Mock embedding
        return [0.1] * 1536
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.embeddings.create(input=text, model="text-embedding-3-small")
        return response.data[0].embedding
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return [0.0] * 1536

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot_product = sum(a*b for a, b in zip(v1, v2))
    magnitude_v1 = math.sqrt(sum(a*a for a in v1))
    magnitude_v2 = math.sqrt(sum(b*b for b in v2))
    if magnitude_v1 * magnitude_v2 == 0:
        return 0
    return dot_product / (magnitude_v1 * magnitude_v2)

def calculate_semantic_score(job_description: str, resume_text: str) -> float:
    """
    Calculates semantic similarity using embeddings.
    """
    v1 = get_embedding(job_description[:8000]) # Truncate for token limits
    v2 = get_embedding(resume_text[:8000])
    similarity = cosine_similarity(v1, v2)
    return max(0, similarity * 100) # Ensure 0-100 range

def score_resume(job_description: str, resume_text: str) -> Dict[str, Any]:
    """
    Main scoring function combining Keyword and Semantic scores.
    """
    kw_score, missing, matched = calculate_keyword_score(job_description, resume_text)
    sem_score = calculate_semantic_score(job_description, resume_text)
    
    # Hybrid Weight
    final_score = (kw_score * 0.6) + (sem_score * 0.4)
    
    return {
        "overall_score": round(final_score, 2),
        "keyword_score": round(kw_score, 2),
        "semantic_score": round(sem_score, 2),
        "missing_keywords": missing,
        "matched_keywords": matched,
        "insights": f"Strong match on {len(matched['top_5'])} keywords." if kw_score > 50 else "High skill gap detected."
    }
