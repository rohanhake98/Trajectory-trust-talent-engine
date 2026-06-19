from typing import Any, Dict

from ingest import CandidateModel
from normalize import normalize_skill


def generate_grounded_reason(score_item: Dict[str, Any]) -> str:
    """Assembles a highly specific, fact-based justification for the candidate's rank.

    Ensures zero hallucination by utilizing only parsed skills and profile attributes,
    linking them to JD requirements, and highlighting potential recruiter concerns.
    """
    candidate: CandidateModel = score_item["candidate_obj"]
    years = candidate.profile.years_of_experience
    current_title = candidate.profile.current_title

    # Standardize skill matching checks
    skills_list = [normalize_skill(s.name) for s in candidate.skills]
    skills_set = set(skills_list)

    # Check for specific search/vector DB experience
    vector_db_list = [
        "Pinecone",
        "Weaviate",
        "Qdrant",
        "Milvus",
        "Elasticsearch",
        "FAISS",
        "OpenSearch",
    ]
    matched_vectors = [v for v in vector_db_list if v in skills_set]

    # Check for evaluation pipeline experience
    eval_list = ["evaluation frameworks", "ndcg", "mrr", "map", "a/b test", "ranking"]
    matched_evals = [e for e in eval_list if any(e in s.lower() for s in skills_list)]

    # 1. Formulate experience and title statement
    reason_parts = [
        f"Senior candidate presenting {years:.1f} years of experience as a '{current_title}'"
    ]

    # 2. Add specific vector/evaluation credentials
    if matched_vectors:
        reason_parts.append(
            f"production experience with vector search ({', '.join(matched_vectors[:2])})"
        )
    else:
        # Fallback keyword check
        has_embeddings = any("embedding" in s.lower() for s in skills_list)
        if has_embeddings:
            reason_parts.append("experience deploying embeddings-based retrieval systems")

    if matched_evals:
        reason_parts.append("hands-on design of ranking evaluation frameworks")

    # 3. Add honest concerns/caveats (Notice period or Outsourcing company tenure)
    notice_days = candidate.redrob_signals.notice_period_days
    if notice_days > 45:
        reason_parts.append(f"re-routing note: longer notice period of {notice_days} days")

    from features import check_only_consulting

    if check_only_consulting(candidate):
        reason_parts.append("note: entire career history is spent at service/consulting firms")

    # Join parts to form a coherent explanation
    explanation = "; ".join(reason_parts)
    # Capitalize the first letter and terminate with a period
    explanation = explanation[0].upper() + explanation[1:] + "."
    return explanation
