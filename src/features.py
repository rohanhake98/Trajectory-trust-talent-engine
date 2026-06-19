import math
from datetime import datetime

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import config
from ingest import CandidateModel
from normalize import normalize_skill, normalize_title

# Reference date matching the current environment execution context
REFERENCE_DATE = datetime(2026, 6, 19)


def calculate_title_similarity(current_title: str, target_title: str) -> float:
    """Calculates TF-IDF cosine similarity between candidate title and target title."""
    if not current_title or not target_title:
        return 0.0
    c_title = normalize_title(current_title).lower()
    t_title = normalize_title(target_title).lower()

    if c_title == t_title:
        return 1.0

    vectorizer = TfidfVectorizer()
    try:
        tfidf = vectorizer.fit_transform([c_title, t_title])
        sim = cosine_similarity(tfidf[0:1], tfidf[1:2])
        return float(sim[0][0])
    except ValueError:
        return 0.0


def calculate_static_fit(candidate: CandidateModel) -> float:
    """Computes the Static Fit sub-score [0, 1] based on current profile metrics."""
    # 1. Title Similarity
    title_sim = calculate_title_similarity(candidate.profile.current_title, config.TARGET_TITLE)

    # 2. Skill Overlap
    target_skills_set = set(config.REQUIRED_SKILLS)
    matched_skills_score = 0.0

    proficiency_weights = {"beginner": 0.5, "intermediate": 0.7, "advanced": 0.9, "expert": 1.0}

    for skill in candidate.skills:
        normalized_name = normalize_skill(skill.name)
        if normalized_name in target_skills_set:
            prof_val = proficiency_weights.get(skill.proficiency.lower(), 0.5)
            # Endorsement weight boost: up to +0.2 max for highly endorsed skills
            endorsement_boost = min(0.2, skill.endorsements / 50.0)
            matched_skills_score += min(1.0, prof_val + endorsement_boost)

    skill_overlap = matched_skills_score / max(1, len(target_skills_set))
    skill_overlap = min(1.0, skill_overlap)

    # 3. Education and Experience Band
    exp_ratio = candidate.profile.years_of_experience / config.TARGET_EXPERIENCE_YEARS
    experience_score = min(1.0, exp_ratio)

    education_tier_weights = {
        "tier_1": 1.0,
        "tier_2": 0.8,
        "tier_3": 0.6,
        "tier_4": 0.4,
        "unknown": 0.3,
    }

    highest_edu_score = 0.3
    for edu in candidate.education:
        edu_score = education_tier_weights.get(edu.tier.lower(), 0.3)
        if edu_score > highest_edu_score:
            highest_edu_score = edu_score

    edu_exp_score = (0.7 * experience_score) + (0.3 * highest_edu_score)

    # Aggregate weighted score
    w = config.STATIC_FIT_WEIGHTS
    static_fit = (
        (w["title_similarity"] * title_sim)
        + (w["skill_overlap"] * skill_overlap)
        + (w["education_experience"] * edu_exp_score)
    )
    return float(static_fit)


def calculate_trajectory_score(
    candidate: CandidateModel, role_transition_score: float = 0.5
) -> float:
    """Computes the Career Trajectory score [0, 1]."""
    # 1. Career Velocity
    # Heuristic: count number of job changes or title shifts relative to total work experience
    job_changes = len(candidate.career_history)
    years_exp = max(1.0, candidate.profile.years_of_experience)

    # Upward movement indicator: title contains senior keyword while earlier ones did not
    career_velocity = min(1.0, job_changes / max(1.0, years_exp / 2.0))

    # 2. Skill Acquisition Rate
    # Target skills divided by total years of experience
    target_skills_set = set(config.REQUIRED_SKILLS)
    target_skills_count = sum(
        1 for s in candidate.skills if normalize_skill(s.name) in target_skills_set
    )
    skill_acq_rate = min(1.0, target_skills_count / max(1.0, years_exp / 2.0))

    # 3. Time to Role Estimate
    # Closeness to target years of experience
    time_to_role = min(1.0, candidate.profile.years_of_experience / config.TARGET_EXPERIENCE_YEARS)

    # Transition relevance is computed by the graph network path, passed in as role_transition_score
    w = config.TRAJECTORY_WEIGHTS
    trajectory = (
        (w["career_velocity"] * career_velocity)
        + (w["transition_relevance"] * role_transition_score)
        + (w["skill_acquisition_rate"] * skill_acq_rate)
        + (w["time_to_role_estimate"] * time_to_role)
    )
    return float(trajectory)


def calculate_convertibility_score(candidate: CandidateModel) -> float:
    """Computes candidate convertibility [0, 1] based on active engagement signals."""
    sig = candidate.redrob_signals

    # 1. Active Recency Factor
    try:
        active_date = datetime.strptime(sig.last_active_date, "%Y-%m-%d")
        days_inactive = max(0, (REFERENCE_DATE - active_date).days)
        # Exponential decay: active recently -> 1.0, 90 days inactive -> ~0.05
        recency = math.exp(-days_inactive / 30.0)
    except (ValueError, TypeError):
        recency = 0.1

    # 2. Open to Work
    open_to_work = 1.0 if sig.open_to_work_flag else 0.2

    # 3. Notice Period Factor (lower notice period is better)
    notice_period = 1.0 - (sig.notice_period_days / 180.0)
    notice_period = max(0.0, min(1.0, notice_period))

    # 4. Response & Completion Rates
    response_rate = sig.recruiter_response_rate
    interview_complete = sig.interview_completion_rate

    # Offer acceptance (if -1, default to 0.5)
    offer_acceptance = sig.offer_acceptance_rate
    if offer_acceptance == -1:
        offer_acceptance = 0.5

    # 5. Work Mode and Relocation Fit
    work_mode_match = 0.2
    if sig.preferred_work_mode.lower() == config.PREFERRED_WORK_MODE:
        work_mode_match = 1.0
    elif sig.preferred_work_mode.lower() in ["remote", "flexible"]:
        work_mode_match = 0.8

    if not work_mode_match and sig.willing_to_relocate:
        work_mode_match = 0.6

    w = config.CONVERTIBILITY_WEIGHTS
    convertibility = (
        (w["recency"] * recency)
        + (w["open_to_work"] * open_to_work)
        + (w["response_rate"] * response_rate)
        + (w["interview_completion"] * interview_complete)
        + (w["offer_acceptance"] * offer_acceptance)
        + (w["notice_period"] * notice_period)
        + (w["work_mode_relocation"] * work_mode_match)
    )
    return float(convertibility)
