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


def check_only_consulting(candidate: CandidateModel) -> bool:
    """Checks if a candidate has only worked at consulting/service firms."""
    if not candidate.career_history:
        return False
    consulting_count = 0
    for job in candidate.career_history:
        company_lower = job.company.lower()
        is_consulting = any(firm in company_lower for firm in config.CONSULTING_FIRMS)
        if is_consulting:
            consulting_count += 1
    return consulting_count == len(candidate.career_history)


def check_title_chaser(candidate: CandidateModel) -> bool:
    """Checks if a candidate averages less than 18 months per job (title chasers)."""
    job_changes = len(candidate.career_history)
    if job_changes < 2:
        return False
    total_months = sum(job.duration_months for job in candidate.career_history)
    avg_tenure = total_months / job_changes
    return avg_tenure < 18.0


def check_pure_research(candidate: CandidateModel) -> bool:
    """Detects candidates who have only academic/research experience with no shipping background."""
    if not candidate.career_history:
        return True

    research_keywords = ["research", "lab", "academic", "phd", "postdoc", "fellowship", "thesis"]
    production_keywords = [
        "production",
        "deploy",
        "scale",
        "ship",
        "aws",
        "gcp",
        "docker",
        "pipeline",
    ]

    research_matches = 0
    production_matches = 0

    for job in candidate.career_history:
        desc_lower = job.description.lower()
        if any(kw in desc_lower for kw in research_keywords):
            research_matches += 1
        if any(kw in desc_lower for kw in production_keywords):
            production_matches += 1

    return research_matches > 0 and production_matches == 0


def check_langchain_only(candidate: CandidateModel) -> bool:
    """Detects candidates whose AI experience is shallow and recent (LangChain only)."""
    years_exp = candidate.profile.years_of_experience
    if years_exp >= 2.0:
        return False

    skills_lower = [s.name.lower() for s in candidate.skills]
    has_toy_ai = any(
        kw in skills_lower for kw in ["langchain", "openai", "gpt", "prompt engineering"]
    )
    has_core_ml = any(
        kw in skills_lower
        for kw in [
            "scikit-learn",
            "numpy",
            "pandas",
            "classification",
            "regression",
            "nlp",
            "pytorch",
            "tensorflow",
        ]
    )

    return has_toy_ai and not has_core_ml


def calculate_static_fit(candidate: CandidateModel) -> float:
    """Computes the Static Fit sub-score [0, 1] based on current profile metrics."""
    # 1. Title Similarity
    title_sim = calculate_title_similarity(candidate.profile.current_title, config.TARGET_TITLE)

    # 2. Skill Overlap (Must-Haves & Nice-To-Haves)
    target_skills_set = {s.strip().lower() for s in config.REQUIRED_SKILLS}
    nice_skills_set = {s.strip().lower() for s in config.NICE_TO_HAVE_SKILLS}

    matched_skills_score = 0.0
    proficiency_weights = {"beginner": 0.5, "intermediate": 0.7, "advanced": 0.9, "expert": 1.0}

    for skill in candidate.skills:
        normalized_name = normalize_skill(skill.name).strip().lower()
        if normalized_name in target_skills_set:
            prof_val = proficiency_weights.get(skill.proficiency.lower(), 0.5)
            # Endorsement weight boost: up to +0.2 max for highly endorsed skills
            endorsement_boost = min(0.2, skill.endorsements / 50.0)
            matched_skills_score += min(1.0, prof_val + endorsement_boost)
        elif normalized_name in nice_skills_set:
            # Nice-to-haves add a small bonus (0.2 max per nice skill)
            prof_val = proficiency_weights.get(skill.proficiency.lower(), 0.5)
            matched_skills_score += 0.2 * prof_val

    total_possible_score = len(target_skills_set) + (0.1 * len(nice_skills_set))
    skill_overlap = matched_skills_score / max(1.0, total_possible_score)
    skill_overlap = min(1.0, skill_overlap)

    # 3. Education and Experience Band
    # Ideal experience: 5-9 years. Peak score at 7 years, decays slightly above/below.
    years_exp = candidate.profile.years_of_experience
    if 5.0 <= years_exp <= 9.0:
        experience_score = 1.0
    else:
        # Penalize distance from target band
        experience_score = max(0.2, 1.0 - 0.15 * abs(years_exp - 7.0))

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

    # Apply JD-specific downweights/penalties
    if check_only_consulting(candidate):
        static_fit *= 0.60
    if check_pure_research(candidate):
        static_fit *= 0.70
    if check_langchain_only(candidate):
        static_fit *= 0.50

    return float(static_fit)


def calculate_trajectory_score(
    candidate: CandidateModel, role_transition_score: float = 0.5
) -> float:
    """Computes the Career Trajectory score [0, 1] incorporating JD progression filters."""
    # 1. Career Velocity
    job_changes = len(candidate.career_history)
    years_exp = max(1.0, candidate.profile.years_of_experience)
    career_velocity = min(1.0, job_changes / max(1.0, years_exp / 2.0))

    # 2. Skill Acquisition Rate
    target_skills_set = {s.strip().lower() for s in config.REQUIRED_SKILLS}
    target_skills_count = sum(
        1 for s in candidate.skills if normalize_skill(s.name).strip().lower() in target_skills_set
    )
    skill_acq_rate = min(1.0, target_skills_count / max(1.0, years_exp / 2.0))

    # 3. Time to Role Estimate
    time_to_role = min(1.0, candidate.profile.years_of_experience / config.TARGET_EXPERIENCE_YEARS)

    w = config.TRAJECTORY_WEIGHTS
    trajectory = (
        (w["career_velocity"] * career_velocity)
        + (w["transition_relevance"] * role_transition_score)
        + (w["skill_acquisition_rate"] * skill_acq_rate)
        + (w["time_to_role_estimate"] * time_to_role)
    )

    # Apply JD-specific Trajectory modifiers
    if check_only_consulting(candidate):
        trajectory *= 0.60
    if check_title_chaser(candidate):
        trajectory *= 0.80

    return float(trajectory)


def calculate_convertibility_score(candidate: CandidateModel) -> float:
    """Computes candidate convertibility [0, 1] based on active engagement signals."""
    sig = candidate.redrob_signals

    # 1. Active Recency Factor (Active recently = higher availability)
    try:
        active_date = datetime.strptime(sig.last_active_date, "%Y-%m-%d")
        days_inactive = max(0, (REFERENCE_DATE - active_date).days)
        # Exponential decay: active recently -> 1.0, 180 days inactive -> ~0.002
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
