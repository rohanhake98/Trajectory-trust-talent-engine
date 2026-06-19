from typing import Dict, List, Set

# Target job description (JD) criteria
TARGET_TITLE: str = "Senior AI Engineer"

# Must-have skills specified in the JD
REQUIRED_SKILLS: List[str] = [
    "Python",
    "embeddings",
    "sentence-transformers",
    "openai embeddings",
    "bge",
    "e5",
    "vector database",
    "pinecone",
    "weaviate",
    "qdrant",
    "milvus",
    "opensearch",
    "elasticsearch",
    "faiss",
    "hybrid search",
    "evaluation frameworks",
    "ndcg",
    "mrr",
    "map",
    "a/b test",
    "ranking",
]

# Nice-to-have skills specified in the JD
NICE_TO_HAVE_SKILLS: List[str] = [
    "lora",
    "qlora",
    "peft",
    "fine-tuning",
    "learning-to-rank",
    "xgboost",
    "hr-tech",
    "marketplace",
    "distributed systems",
    "inference optimization",
    "open-source",
]

# Target experience parameters
TARGET_EXPERIENCE_YEARS: float = 7.0  # Middle of the 5-9 years band, ideal 6-8
PREFERRED_WORK_MODE: str = "hybrid"

# Service companies list to identify consulting backgrounds
CONSULTING_FIRMS: Set[str] = {
    "tcs",
    "tata consultancy",
    "infosys",
    "wipro",
    "accenture",
    "cognizant",
    "capgemini",
    "hcl",
    "tech mahindra",
    "l&t",
    "lnt",
    "mindtree",
    "deloitte",
    "pwc",
    "ey",
    "kpmg",
    "ibm",
}

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
