import csv
import json
import os

import pytest

from src.ranker import process_and_rank
from tests.test_ingest import MOCK_CANDIDATE


@pytest.fixture
def mock_jsonl_file(tmp_path):
    # Create 3 mock candidates with varying properties
    c1 = MOCK_CANDIDATE.copy()
    c1["candidate_id"] = "CAND_0000001"
    c1["profile"] = c1["profile"].copy()
    c1["profile"]["current_title"] = "Senior AI Engineer"
    c1["profile"]["years_of_experience"] = 7.0

    c2 = MOCK_CANDIDATE.copy()
    c2["candidate_id"] = "CAND_0000002"
    c2["profile"] = c2["profile"].copy()
    c2["profile"]["current_title"] = "Machine Learning Engineer"
    c2["profile"]["years_of_experience"] = 3.0

    # Candidate 3 is a honeypot (timeline overlap)
    c3 = MOCK_CANDIDATE.copy()
    c3["candidate_id"] = "CAND_0000003"
    c3["career_history"] = [
        c1["career_history"][0],
        c1["career_history"][0],  # duplicate dates -> overlap penalty
    ]

    file_path = tmp_path / "candidates_test.jsonl"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(c1) + "\n")
        f.write(json.dumps(c2) + "\n")
        f.write(json.dumps(c3) + "\n")

    return str(file_path)


def test_process_and_rank(mock_jsonl_file, tmp_path):
    csv_out = tmp_path / "submission.csv"
    results = process_and_rank(mock_jsonl_file, export_csv_path=str(csv_out))

    # 3 candidates processed, should output up to 100 (which is 3 in this mock run)
    assert len(results) == 3

    # Verify ranking monotonicity
    assert results[0]["rank"] == 1
    assert results[1]["rank"] == 2
    assert results[2]["rank"] == 3
    assert results[0]["score"] >= results[1]["score"] >= results[2]["score"]

    # Candidate 3 (honeypot) must score lower than Candidate 1 (its clean baseline)
    scores = {r["candidate_id"]: r["score"] for r in results}
    assert scores["CAND_0000001"] > scores["CAND_0000003"]

    # Verify exported CSV matches requirements
    assert os.path.exists(csv_out)
    with open(csv_out, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ["candidate_id", "rank", "score", "reasoning"]

        row1 = next(reader)
        assert row1[0] == "CAND_0000001"  # Top candidate ID
        assert row1[1] == "1"  # Rank 1
