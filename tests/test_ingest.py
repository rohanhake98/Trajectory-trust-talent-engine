import pytest
from src.ingest import CandidateModel
from src.normalize import normalize_skill, normalize_title

# Mock candidate dictionary matching candidate_schema.json
MOCK_CANDIDATE = {
    "candidate_id": "CAND_0000001",
    "profile": {
        "anonymized_name": "John Doe",
        "headline": "Experienced AI Engineer",
        "summary": "Building modern LLM pipelines.",
        "location": "San Francisco, CA",
        "country": "USA",
        "years_of_experience": 5.5,
        "current_title": "sr ml engineer",
        "current_company": "Tech Corp",
        "current_company_size": "201-500",
        "current_industry": "Software",
    },
    "career_history": [
        {
            "company": "Tech Corp",
            "title": "sr ml engineer",
            "start_date": "2022-01-01",
            "end_date": None,
            "duration_months": 24,
            "is_current": True,
            "industry": "Software",
            "company_size": "201-500",
            "description": "Led AI infrastructure setup.",
        }
    ],
    "education": [
        {
            "institution": "Stanford University",
            "degree": "MS",
            "field_of_study": "Computer Science",
            "start_year": 2018,
            "end_year": 2020,
            "tier": "tier_1",
        }
    ],
    "skills": [
        {"name": "pytorch", "proficiency": "expert", "endorsements": 15, "duration_months": 48},
        {"name": "python3", "proficiency": "expert", "endorsements": 25, "duration_months": 60},
    ],
    "redrob_signals": {
        "profile_completeness_score": 95.0,
        "signup_date": "2021-01-01",
        "last_active_date": "2026-06-18",
        "open_to_work_flag": True,
        "profile_views_received_30d": 120,
        "applications_submitted_30d": 5,
        "recruiter_response_rate": 0.85,
        "avg_response_time_hours": 1.2,
        "skill_assessment_scores": {"Python": 95.0, "PyTorch": 90.0},
        "connection_count": 350,
        "endorsements_received": 40,
        "notice_period_days": 30,
        "expected_salary_range_inr_lpa": {"min": 30.0, "max": 45.0},
        "preferred_work_mode": "hybrid",
        "willing_to_relocate": True,
        "github_activity_score": 85.0,
        "search_appearance_30d": 45,
        "saved_by_recruiters_30d": 12,
        "interview_completion_rate": 0.95,
        "offer_acceptance_rate": 0.80,
        "verified_email": True,
        "verified_phone": True,
        "linkedin_connected": True,
    },
}


def test_normalization_title():
    assert normalize_title("sr ml engineer") == "Senior Machine Learning Engineer"
    assert normalize_title("ai engineer") == "AI Engineer"
    assert normalize_title("senior artificial intelligence engineer") == "Senior AI Engineer"
    assert normalize_title("unrecognized title") == "Unrecognized Title"
    assert normalize_title(None) == "Unknown"


def test_normalization_skill():
    assert normalize_skill("pytorch") == "PyTorch"
    assert normalize_skill("python3") == "Python"
    assert normalize_skill("k8s") == "Kubernetes"
    assert normalize_skill("unrecognized skill") == "unrecognized skill"
    assert normalize_skill(None) == "Unknown"


def test_valid_candidate_parsing():
    # Verify candidate parses successfully with schema validations
    candidate = CandidateModel(**MOCK_CANDIDATE)
    assert candidate.candidate_id == "CAND_0000001"
    assert candidate.profile.years_of_experience == 5.5
    assert len(candidate.career_history) == 1
    assert candidate.skills[0].name == "pytorch"


def test_invalid_candidate_id_raises():
    bad_candidate = MOCK_CANDIDATE.copy()
    bad_candidate["candidate_id"] = "CAND_123"  # Invalid format

    with pytest.raises(Exception):
        CandidateModel(**bad_candidate)
