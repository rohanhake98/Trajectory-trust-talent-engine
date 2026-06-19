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
    # Candidate with 3.0 years experience (lower/out-of-band score)
    low_exp_candidate = test_candidate.model_copy(deep=True)
    low_exp_candidate.profile.years_of_experience = 3.0
    score_low = calculate_static_fit(low_exp_candidate)

    # Candidate with 7.0 years experience (peak target score)
    peak_exp_candidate = test_candidate.model_copy(deep=True)
    peak_exp_candidate.profile.years_of_experience = 7.0
    score_peak = calculate_static_fit(peak_exp_candidate)

    assert 0.0 <= score_low <= 1.0
    assert 0.0 <= score_peak <= 1.0
    assert score_peak >= score_low


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


def test_jd_filters(test_candidate):
    from src.features import (
        check_langchain_only,
        check_only_consulting,
        check_pure_research,
        check_title_chaser,
    )

    # 1. Consulting check
    assert not check_only_consulting(test_candidate)
    consulting_cand = test_candidate.model_copy(deep=True)
    consulting_cand.career_history[0].company = "TCS"
    assert check_only_consulting(consulting_cand)

    # 2. Title chaser check
    chaser_cand = test_candidate.model_copy(deep=True)
    chaser_cand.career_history = [
        chaser_cand.career_history[0].model_copy(update={"duration_months": 10}),
        chaser_cand.career_history[0].model_copy(update={"duration_months": 10}),
    ]
    assert check_title_chaser(chaser_cand)

    # 3. Pure research check
    research_cand = test_candidate.model_copy(deep=True)
    research_cand.career_history[
        0
    ].description = "Conducted academic research in lab and completed PhD thesis."
    assert check_pure_research(research_cand)

    # 4. LangChain only check
    toy_cand = test_candidate.model_copy(deep=True)
    toy_cand.profile.years_of_experience = 1.0
    from ingest import SkillModel

    toy_cand.skills = [
        SkillModel(name="langchain", proficiency="expert", endorsements=5),
        SkillModel(name="openai", proficiency="expert", endorsements=5),
    ]
    assert check_langchain_only(toy_cand)
