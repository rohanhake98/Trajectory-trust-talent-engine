import pytest

from src.features import (
    calculate_convertibility_score,
    calculate_static_fit,
    calculate_title_similarity,
    calculate_trajectory_score,
)
from src.ingest import CandidateModel
from tests.test_ingest import MOCK_CANDIDATE


@pytest.fixture
def test_candidate():
    return CandidateModel(**MOCK_CANDIDATE)


def test_calculate_title_similarity():
    # Exact match
    assert calculate_title_similarity("Senior AI Engineer", "Senior AI Engineer") == 1.0
    # Case insensitive
    assert calculate_title_similarity("senior ai engineer", "SENIOR AI ENGINEER") == 1.0
    # Overlap similarity check
    sim = calculate_title_similarity("ML Engineer", "Senior AI Engineer")
    assert 0.0 <= sim <= 1.0
    # Completely empty strings
    assert calculate_title_similarity("", "Senior AI Engineer") == 0.0


def test_calculate_static_fit(test_candidate):
    score = calculate_static_fit(test_candidate)
    assert 0.0 <= score <= 1.0
    # Check that having higher years of experience increases experience sub-score
    high_exp_candidate = test_candidate.model_copy(deep=True)
    high_exp_candidate.profile.years_of_experience = 10.0
    score_high = calculate_static_fit(high_exp_candidate)
    assert score_high >= score


def test_calculate_trajectory_score(test_candidate):
    score = calculate_trajectory_score(test_candidate, role_transition_score=0.7)
    assert 0.0 <= score <= 1.0

    # Check that high graph path transition scores increase trajectory score
    score_low = calculate_trajectory_score(test_candidate, role_transition_score=0.2)
    assert score >= score_low


def test_calculate_convertibility_score(test_candidate):
    score = calculate_convertibility_score(test_candidate)
    assert 0.0 <= score <= 1.0

    # Active yesterday vs active 100 days ago should yield higher score
    active_yesterday = test_candidate.model_copy(deep=True)
    active_yesterday.redrob_signals.last_active_date = "2026-06-18"

    active_long_ago = test_candidate.model_copy(deep=True)
    active_long_ago.redrob_signals.last_active_date = "2025-01-01"

    assert calculate_convertibility_score(active_yesterday) > calculate_convertibility_score(
        active_long_ago
    )
