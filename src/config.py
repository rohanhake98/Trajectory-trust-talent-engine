from typing import Dict, List

# Target job description (JD) criteria
TARGET_TITLE: str = "Senior AI Engineer"
REQUIRED_SKILLS: List[str] = [
    "Python",
    "PyTorch",
    "TensorFlow",
    "Scikit-Learn",
    "MLOps",
    "Kubernetes",
    "Docker",
    "Git",
    "LLMs",
    "Transformers",
    "NLP",
    "Computer Vision",
]
TARGET_EXPERIENCE_YEARS: float = 8.0
PREFERRED_WORK_MODE: str = "hybrid"

# Weights for scoring formulas
STATIC_FIT_WEIGHTS: Dict[str, float] = {
    "title_similarity": 0.50,
    "skill_overlap": 0.30,
    "education_experience": 0.20,
}

TRAJECTORY_WEIGHTS: Dict[str, float] = {
    "career_velocity": 0.35,
    "transition_relevance": 0.25,
    "skill_acquisition_rate": 0.20,
    "time_to_role_estimate": 0.20,
}

CONVERTIBILITY_WEIGHTS: Dict[str, float] = {
    "recency": 0.20,
    "open_to_work": 0.15,
    "response_rate": 0.15,
    "interview_completion": 0.15,
    "offer_acceptance": 0.15,
    "notice_period": 0.10,
    "work_mode_relocation": 0.10,
}
