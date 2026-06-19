import pytest

from src.ingest import CandidateModel
from src.shield import (
    calculate_stuffing_ratio,
    calculate_synthetic_pattern,
    calculate_trust_score,
    check_timeline_overlap,
)
from tests.test_ingest import MOCK_CANDIDATE


@pytest.fixture
def base_candidate():
    return CandidateModel(**MOCK_CANDIDATE)


def test_timeline_overlap():
    # Overlapping jobs (Job 2 starts before Job 1 ends)
    c_jobs = [
        {
            "company": "A",
            "title": "Engineer",
            "start_date": "2020-01-01",
            "end_date": "2021-12-31",
            "duration_months": 24,
            "is_current": False,
            "industry": "Software",
            "company_size": "1-10",
            "description": "desc",
        },
        {
            "company": "B",
            "title": "Engineer",
            "start_date": "2021-06-01",
            "end_date": "2022-06-01",
            "duration_months": 12,
            "is_current": False,
            "industry": "Software",
            "company_size": "1-10",
            "description": "desc",
        },
    ]
    # Parse mock objects
    from ingest import CareerHistoryModel

    history = [CareerHistoryModel(**job) for job in c_jobs]

    assert check_timeline_overlap(history) == 0.40

    # Chronological jobs (no overlap)
    c_jobs_clean = [
        {
            "company": "A",
            "title": "Engineer",
            "start_date": "2020-01-01",
            "end_date": "2021-12-31",
            "duration_months": 24,
            "is_current": False,
            "industry": "Software",
            "company_size": "1-10",
            "description": "desc",
        },
        {
            "company": "B",
            "title": "Engineer",
            "start_date": "2022-01-01",
            "end_date": "2023-01-01",
            "duration_months": 12,
            "is_current": False,
            "industry": "Software",
            "company_size": "1-10",
            "description": "desc",
        },
    ]
    history_clean = [CareerHistoryModel(**job) for job in c_jobs_clean]
    assert check_timeline_overlap(history_clean) == 0.0


def test_stuffing_ratio():
    from ingest import SkillModel

    # Under limit
    clean_skills = [
        SkillModel(name=f"Skill {i}", proficiency="expert", endorsements=2) for i in range(10)
    ]
    assert calculate_stuffing_ratio(clean_skills) == 0.0

    # Stuffed skills (count = 35, avg endorsements = 0.0)
    stuffed_skills = [
        SkillModel(name=f"Skill {i}", proficiency="beginner", endorsements=0) for i in range(35)
    ]
    assert calculate_stuffing_ratio(stuffed_skills) > 0.0


def test_synthetic_pattern(base_candidate):
    # Base candidate has 5.5 years of experience, current title is 'sr ml engineer'
    assert calculate_synthetic_pattern(base_candidate) == 0.0

    # Inflated candidate: current title is 'Senior Director AI' with 1 year experience
    inflated_candidate = base_candidate.model_copy(deep=True)
    inflated_candidate.profile.current_title = "Senior Director AI"
    inflated_candidate.profile.years_of_experience = 1.0

    assert calculate_synthetic_pattern(inflated_candidate) == 0.40


def test_calculate_trust_score(base_candidate):
    # Completely clean candidate
    assert calculate_trust_score(base_candidate) == 1.0

    # Highly anomalous candidate
    bad_candidate = base_candidate.model_copy(deep=True)
    bad_candidate.profile.current_title = "VP AI Engineering"
    bad_candidate.profile.years_of_experience = 0.5

    # Overlapping dates
    bad_candidate.career_history = [
        bad_candidate.career_history[0],
        bad_candidate.career_history[0],  # Duplicating current job creates an overlap
    ]

    # Trust score should drop
    assert calculate_trust_score(bad_candidate) < 1.0
