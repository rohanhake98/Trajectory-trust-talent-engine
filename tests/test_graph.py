import pytest

from src.graph import build_career_graph, get_transition_score
from src.ingest import CandidateModel
from tests.test_ingest import MOCK_CANDIDATE


@pytest.fixture
def mock_candidates():
    # Candidate 1: Software Engineer -> Machine Learning Engineer -> AI Engineer
    c1 = MOCK_CANDIDATE.copy()
    c1["candidate_id"] = "CAND_0000001"
    c1["career_history"] = [
        {
            "company": "A",
            "title": "Software Engineer",
            "start_date": "2018-01-01",
            "end_date": "2020-01-01",
            "duration_months": 24,
            "is_current": False,
            "industry": "Software",
            "company_size": "201-500",
            "description": "Dev",
        },
        {
            "company": "B",
            "title": "Machine Learning Engineer",
            "start_date": "2020-02-01",
            "end_date": "2022-01-01",
            "duration_months": 24,
            "is_current": False,
            "industry": "Software",
            "company_size": "201-500",
            "description": "ML",
        },
        {
            "company": "C",
            "title": "AI Engineer",
            "start_date": "2022-02-01",
            "end_date": None,
            "duration_months": 24,
            "is_current": True,
            "industry": "Software",
            "company_size": "201-500",
            "description": "AI",
        },
    ]

    # Candidate 2: Machine Learning Engineer -> AI Engineer
    c2 = MOCK_CANDIDATE.copy()
    c2["candidate_id"] = "CAND_0000002"
    c2["career_history"] = [
        {
            "company": "B",
            "title": "Machine Learning Engineer",
            "start_date": "2020-01-01",
            "end_date": "2022-01-01",
            "duration_months": 24,
            "is_current": False,
            "industry": "Software",
            "company_size": "201-500",
            "description": "ML",
        },
        {
            "company": "C",
            "title": "AI Engineer",
            "start_date": "2022-02-01",
            "end_date": None,
            "duration_months": 24,
            "is_current": True,
            "industry": "Software",
            "company_size": "201-500",
            "description": "AI",
        },
    ]

    # Candidate 3: Software Engineer -> Data Scientist
    c3 = MOCK_CANDIDATE.copy()
    c3["candidate_id"] = "CAND_0000003"
    c3["career_history"] = [
        {
            "company": "A",
            "title": "Software Engineer",
            "start_date": "2018-01-01",
            "end_date": "2020-01-01",
            "duration_months": 24,
            "is_current": False,
            "industry": "Software",
            "company_size": "201-500",
            "description": "Dev",
        },
        {
            "company": "D",
            "title": "Data Scientist",
            "start_date": "2020-02-01",
            "end_date": None,
            "duration_months": 24,
            "is_current": True,
            "industry": "Software",
            "company_size": "201-500",
            "description": "DS",
        },
    ]

    return [CandidateModel(**c1), CandidateModel(**c2), CandidateModel(**c3)]


def test_build_career_graph(mock_candidates):
    G = build_career_graph(mock_candidates)

    # Assert nodes exist after normalization
    assert G.has_node("Software Engineer")
    assert G.has_node("Machine Learning Engineer")
    assert G.has_node("AI Engineer")
    assert G.has_node("Data Scientist")

    # Check transition frequencies (Machine Learning Engineer -> AI Engineer has freq 2)
    assert G["Machine Learning Engineer"]["AI Engineer"]["weight"] == 2
    assert G["Software Engineer"]["Machine Learning Engineer"]["weight"] == 1

    # Check costs (inverse of weight)
    assert G["Machine Learning Engineer"]["AI Engineer"]["cost"] == 0.5
    assert G["Software Engineer"]["Machine Learning Engineer"]["cost"] == 1.0


def test_get_transition_score(mock_candidates):
    G = build_career_graph(mock_candidates)

    # Self transition
    assert get_transition_score(G, "AI Engineer", "AI Engineer") == 1.0

    # Unrecognized node
    assert get_transition_score(G, "Accountant", "AI Engineer") == 0.0

    # Direct hop: ML Engineer -> AI Engineer (Cost = 0.5)
    score_direct = get_transition_score(G, "Machine Learning Engineer", "AI Engineer", gamma=1.0)
    assert 0.0 < score_direct < 1.0

    # Indirect hop: Software Engineer -> ML Engineer -> AI Engineer (Cost = 1.0 + 0.5 = 1.5)
    score_indirect = get_transition_score(G, "Software Engineer", "AI Engineer", gamma=1.0)
    assert 0.0 < score_indirect < score_direct

    # No path: Data Scientist -> AI Engineer
    assert get_transition_score(G, "Data Scientist", "AI Engineer") == 0.0
