import re
from typing import Optional

TITLE_MAPPINGS = [
    (r"(?i)\b(senior|sr\.?)\s+(ai|artificial intelligence)\s+engineer\b", "Senior AI Engineer"),
    (r"(?i)\b(ai|artificial intelligence)\s+engineer\b", "AI Engineer"),
    (
        r"(?i)\b(senior|sr\.?)\s+(ml|machine learning)\s+engineer\b",
        "Senior Machine Learning Engineer",
    ),
    (r"(?i)\b(ml|machine learning)\s+engineer\b", "Machine Learning Engineer"),
    (r"(?i)\b(senior|sr\.?)\s+software\s+engineer\b", "Senior Software Engineer"),
    (r"(?i)\bsoftware\s+engineer\b", "Software Engineer"),
    (r"(?i)\bdata\s+scientist\b", "Data Scientist"),
    (r"(?i)\b(senior|sr\.?)\s+data\s+scientist\b", "Senior Data Scientist"),
    (r"(?i)\bbackend\s+engineer\b", "Backend Engineer"),
    (r"(?i)\bfrontend\s+engineer\b", "Frontend Engineer"),
    (r"(?i)\bfull\s*stack\s+engineer\b", "Full Stack Engineer"),
    (r"(?i)\bdevops\s+engineer\b", "DevOps Engineer"),
]

SKILL_MAPPINGS = {
    "python": "Python",
    "python3": "Python",
    "py": "Python",
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",
    "scikit-learn": "Scikit-Learn",
    "sklearn": "Scikit-Learn",
    "mlops": "MLOps",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "docker": "Docker",
    "git": "Git",
    "aws": "AWS",
    "gcp": "GCP",
    "azure": "Azure",
    "sql": "SQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mongodb": "MongoDB",
    "nlp": "NLP",
    "natural language processing": "NLP",
    "cv": "Computer Vision",
    "computer vision": "Computer Vision",
    "llm": "LLMs",
    "llms": "LLMs",
    "large language models": "LLMs",
    "transformers": "Transformers",
}


def normalize_title(title: Optional[str]) -> str:
    """Canonicalizes raw job titles into standardized professional titles."""
    if not title:
        return "Unknown"
    cleaned = title.strip()
    for pattern, canonical in TITLE_MAPPINGS:
        if re.search(pattern, cleaned):
            return canonical
    # Title formatting fallback: Title Case
    return cleaned.title()


def normalize_skill(skill: Optional[str]) -> str:
    """Canonicalizes raw skill names (e.g. PyTorch, python3) into standard names."""
    if not skill:
        return "Unknown"
    cleaned = skill.strip().lower()
    if cleaned in SKILL_MAPPINGS:
        return SKILL_MAPPINGS[cleaned]
    # Skill formatting fallback: strip trailing/leading spaces and return
    return skill.strip()
