
import re
from typing import Set, Dict, List

# Knowledge Base of Skills (Deterministic)
SKILL_DB = {
    "Languages": {"Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "Swift", "Kotlin", "PHP", "Ruby", "SQL", "HTML", "CSS"},
    "Frameworks": {"React", "Angular", "Vue", "Next.js", "Django", "FastAPI", "Flask", "Spring Boot", ".NET", "Express", "Node.js", "Laravel", "Rails", "Tailwind"},
    "Databases": {"PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra", "DynamoDB", "Firebase", "Oracle", "SQL Server"},
    "Cloud & DevOps": {"AWS", "Azure", "GCP", "Docker", "Kubernetes", "Jenkins", "GitLab CI", "Terraform", "Ansible", "Linux", "Nginx"},
    "AI/Data": {"Pandas", "NumPy", "PyTorch", "TensorFlow", "Scikit-learn", "Keras", "OpenCV", "NLP", "LLM", "Generative AI", "RAG", "Spark", "Kafka", "Airflow"}
}

def normalize_text(text: str) -> str:
    return text.lower().replace('/', ' ').replace(',', ' ').replace('.', ' ')

def extract_skills(text: str) -> Dict[str, List[str]]:
    """
    Extracts structured skills from text mapping to the SKILL_DB.
    Returns: {"Languages": ["Python", ...], "Frameworks": [...]}
    """
    if not text:
        return {}
        
    normalized_text = normalize_text(text)
    extracted = {}
    
    for category, skills in SKILL_DB.items():
        found_skills = set()
        for skill in skills:
            # Regex boundary match to avoid partial matches (e.g. "Go" in "Good")
            # Escape skill for regex (e.g. C++)
            escaped_skill = re.escape(skill.lower())
            
            # Special case for C++ / C#
            if skill in ["C++", "C#", ".NET"]:
                 if skill.lower() in normalized_text: # Simple check for these chars
                     found_skills.add(skill)
            else:
                # Word boundary check
                if re.search(r'\b' + escaped_skill + r'\b', normalized_text):
                    found_skills.add(skill)
        
        if found_skills:
            extracted[category] = list(found_skills)
            
    return extracted

def flatten_skills(skills_dict: Dict[str, List[str]]) -> Set[str]:
    """Flattens the categorized skills into a single set of strings."""
    flat = set()
    for cat_list in skills_dict.values():
        flat.update(cat_list)
    return flat
