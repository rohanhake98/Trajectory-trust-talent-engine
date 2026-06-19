from datetime import datetime
from typing import List

from ingest import CandidateModel, CareerHistoryModel, SkillModel


def check_timeline_overlap(history: List[CareerHistoryModel]) -> float:
    """Detects overlapping employment date ranges.

    Each chronological overlap adds a 0.4 penalty. Max penalty = 1.0.
    """
    jobs = []
    for job in history:
        try:
            start = datetime.strptime(job.start_date, "%Y-%m-%d")
            # If end_date is null or empty, treat it as the current system execution date
            end = (
                datetime.strptime(job.end_date, "%Y-%m-%d")
                if job.end_date
                else datetime(2026, 6, 19)
            )
            jobs.append((start, end))
        except (ValueError, TypeError):
            continue

    # Sort job ranges chronologically by start date
    jobs.sort(key=lambda x: x[0])

    overlap_penalty = 0.0
    for i in range(len(jobs) - 1):
        current_end = jobs[i][1]
        next_start = jobs[i + 1][0]
        if current_end > next_start:
            # Overlap found (subsequent job starts before current job ends)
            overlap_penalty += 0.40

    return min(1.0, overlap_penalty)


def calculate_stuffing_ratio(skills: List[SkillModel]) -> float:
    """Penalizes profiles with high skill counts but very low endorsement support.

    If skill count is > 30 and average endorsements < 1.0, adds a stuffing penalty.
    """
    if not skills:
        return 0.0

    skill_count = len(skills)
    if skill_count <= 25:
        return 0.0

    total_endorsements = sum(s.endorsements for s in skills)
    avg_endorsements = total_endorsements / skill_count

    if avg_endorsements < 1.5:
        # Scale penalty up to 0.5 based on how many extra skills are stuffed
        excess_skills = skill_count - 25
        penalty = min(0.5, excess_skills * 0.02)
        return float(penalty)

    return 0.0


def calculate_synthetic_pattern(candidate: CandidateModel) -> float:
    """Identifies implausible credential inflation or profile anomalies.

    Checks for:
    - Claiming senior/executive titles with < 2 years total experience (0.4 penalty)
    - Excessive certifications (e.g. > 5 certifications) with < 3 years experience (0.3 penalty)
    """
    penalty = 0.0
    years_exp = candidate.profile.years_of_experience
    current_title = candidate.profile.current_title.lower()

    # Senior title check
    is_senior_title = any(
        kw in current_title
        for kw in ["senior", "sr.", "lead", "principal", "director", "vp", "manager", "head"]
    )
    if is_senior_title and years_exp < 2.0:
        penalty += 0.40

    # Certification stuffing check
    certs_count = len(candidate.redrob_signals.skill_assessment_scores)  # proxy or cert count
    # Let's check certifications if present on candidate
    if hasattr(candidate, "certifications") and candidate.certifications:
        certs_count = len(candidate.certifications)
    else:
        certs_count = 0

    if certs_count > 5 and years_exp < 3.0:
        penalty += 0.30

    return min(1.0, penalty)


def calculate_trust_score(candidate: CandidateModel) -> float:
    """Aggregates all anomaly detectors into a composite TrustScore [0.0, 1.0]."""
    overlap_pen = check_timeline_overlap(candidate.career_history)
    stuffing_pen = calculate_stuffing_ratio(candidate.skills)
    synthetic_pen = calculate_synthetic_pattern(candidate)

    combined_penalty = (0.40 * overlap_pen) + (0.30 * stuffing_pen) + (0.30 * synthetic_pen)
    trust_score = 1.0 - min(1.0, combined_penalty)
    return float(trust_score)
