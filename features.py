"""
features.py — Scores each candidate against the JD.
"""

from datetime import date, datetime
import math


# ── JD REQUIREMENTS ──────────────────────────────────────

REQUIRED_SKILLS = [
    "embeddings", "sentence transformers", "vector database", "vector db",
    "retrieval", "information retrieval", "ranking", "ranking systems",
    "pinecone", "weaviate", "qdrant", "milvus", "faiss", "opensearch",
    "elasticsearch", "vector search", "hybrid search", "bm25",
    "python", "ndcg", "mrr", "map", "evaluation metrics",
    "semantic search", "dense retrieval", "re-ranking", "reranking",
]

BONUS_SKILLS = [
    "lora", "qlora", "fine-tuning", "fine tuning", "learning to rank",
    "recommendation system", "recommender", "a/b testing", "xgboost",
    "langchain", "openai", "rag", "llm", "gpt", "neural ranking",
]

CAREER_SIGNALS = [
    "retrieval", "ranking", "embedding", "vector", "search", "recommendation",
    "deployed", "production", "shipped", "scaled", "pipeline",
    "ranker", "reranker", "ndcg", "mrr", "evaluation", "benchmark",
    "faiss", "pinecone", "weaviate", "qdrant", "elasticsearch",
    "sentence transformer", "bert", "transformer", "llm", "language model",
]

SERVICES_COMPANIES = [
    "tcs", "tata consultancy", "infosys", "wipro", "accenture",
    "cognizant", "capgemini", "hcl", "tech mahindra", "mphasis", "hexaware",
]

NON_ENGINEER_TITLES = [
    "marketing", "sales", "hr ", "human resource", "accountant",
    "operations", "customer support", "content writer", "graphic design",
    "finance", "recruiter", "talent acquisition",
]

ARCHITECT_RISK_TITLES = [
    "architect", "vp ", "vice president", "director", "cto", "head of"
]


# ── UTILITIES ────────────────────────────────────────────

def norm(text):
    return text.lower().strip()

def days_since(date_str):
    if not date_str:
        return 365
    try:
        d = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        return (date.today() - d).days
    except:
        return 365

def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


# ── INDIVIDUAL SCORES ─────────────────────────────────────

def score_skills(candidate):
    skills = candidate.get("skills", [])
    PROF = {"beginner": 0.2, "intermediate": 0.5, "advanced": 0.8, "expert": 1.0}

    req_score = 0.0
    for skill in skills:
        name = norm(skill.get("name", ""))
        prof = PROF.get(skill.get("proficiency", "beginner"), 0.2)
        duration = skill.get("duration_months", 0)
        dur_mult = clamp(math.log1p(duration) / math.log1p(36), 0.1, 1.0)

        for req in REQUIRED_SKILLS:
            if req in name or name in req:
                req_score += prof * dur_mult
                break

    req_score = clamp(req_score / 10.0)

    bonus = 0.0
    for skill in skills:
        name = norm(skill.get("name", ""))
        for bon in BONUS_SKILLS:
            if bon in name or name in bon:
                bonus += 0.05
                break
    bonus = clamp(bonus, 0, 0.2)

    return clamp(req_score + bonus)


def score_experience(candidate):
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    years = profile.get("years_of_experience", 0)
    title = norm(profile.get("current_title", ""))

    # Years score
    if years < 3:
        years_score = 0.1
    elif years < 5:
        years_score = 0.5
    elif years <= 9:
        years_score = 1.0
    elif years <= 12:
        years_score = 0.7
    else:
        years_score = 0.4

    # Services company penalty
    services = sum(
        1 for j in career
        if any(sc in norm(j.get("company", "")) for sc in SERVICES_COMPANIES)
    )
    services_penalty = clamp(services / max(len(career), 1)) * 0.4

    # Title penalty
    title_penalty = 0.0
    for bad in NON_ENGINEER_TITLES:
        if bad in title:
            title_penalty = 0.6
            break
    for risk in ARCHITECT_RISK_TITLES:
        if risk in title:
            title_penalty = max(title_penalty, 0.2)

    # Job hopping penalty
    if career:
        avg_tenure = sum(j.get("duration_months", 12) for j in career) / len(career)
        hopping = 0.2 if avg_tenure < 10 else (0.1 if avg_tenure < 14 else 0.0)
    else:
        hopping = 0.0

    return clamp(years_score - services_penalty - title_penalty - hopping)


def score_career_text(candidate):
    career = candidate.get("career_history", [])
    summary = norm(candidate.get("profile", {}).get("summary", ""))

    all_text = summary
    for job in career:
        all_text += " " + norm(job.get("description", ""))

    hits = sum(1 for signal in CAREER_SIGNALS if signal in all_text)
    return clamp(hits / 8.0)


def score_behavioral(candidate):
    sig = candidate.get("redrob_signals", {})

    rrr = sig.get("recruiter_response_rate", 0.0)

    staleness = days_since(sig.get("last_active_date", ""))
    if staleness <= 7:
        recency = 1.0
    elif staleness <= 30:
        recency = 0.8
    elif staleness <= 90:
        recency = 0.5
    elif staleness <= 180:
        recency = 0.25
    else:
        recency = 0.0

    open_work = 1.0 if sig.get("open_to_work_flag", False) else 0.3
    icr = sig.get("interview_completion_rate", 0.5)

    notice = sig.get("notice_period_days", 60)
    notice_score = 1.0 if notice <= 30 else (0.7 if notice <= 60 else (0.4 if notice <= 90 else 0.2))

    github = sig.get("github_activity_score", -1)
    github_score = 0.3 if github == -1 else clamp(github / 100.0)

    saved = sig.get("saved_by_recruiters_30d", 0)
    saved_score = clamp(saved / 10.0)

    completeness = sig.get("profile_completeness_score", 50) / 100.0

    return clamp(
        rrr            * 0.25 +
        recency        * 0.20 +
        open_work      * 0.10 +
        icr            * 0.15 +
        notice_score   * 0.10 +
        github_score   * 0.10 +
        saved_score    * 0.05 +
        completeness   * 0.05
    )


def score_education(candidate):
    education = candidate.get("education", [])
    if not education:
        return 0.3

    TIERS = {"tier_1": 1.0, "tier_2": 0.7, "tier_3": 0.5, "tier_4": 0.3}
    FIELDS = ["computer science", "cs", "machine learning", "ai",
              "data science", "information technology", "software engineering",
              "statistics", "mathematics", "electronics"]

    best_tier = 0.3
    field_bonus = 0.0
    for edu in education:
        best_tier = max(best_tier, TIERS.get(edu.get("tier", ""), 0.3))
        if any(f in norm(edu.get("field_of_study", "")) for f in FIELDS):
            field_bonus = 0.1

    return clamp(best_tier * 0.9 + field_bonus)


def keyword_stuffer_penalty(candidate):
    skills = candidate.get("skills", [])
    career = candidate.get("career_history", [])

    skill_names = [norm(s.get("name", "")) for s in skills]
    buzzwords = ["rag", "llm", "gpt", "embeddings", "vector",
                 "langchain", "openai", "pinecone", "transformer", "fine-tuning"]

    buzz_count = sum(1 for s in skill_names for bw in buzzwords if bw in s)
    career_text = " ".join(norm(j.get("description", "")) for j in career)
    career_hits = sum(1 for bw in buzzwords if bw in career_text)

    if buzz_count >= 4 and career_hits <= 1:
        return 0.4
    elif buzz_count >= 3 and career_hits == 0:
        return 0.3
    elif buzz_count >= 5 and career_hits <= 2:
        return 0.2
    return 0.0


# ── FINAL SCORE ───────────────────────────────────────────

def compute_final_score(candidate):
    skill    = score_skills(candidate)
    exp      = score_experience(candidate)
    text     = score_career_text(candidate)
    behavior = score_behavioral(candidate)
    edu      = score_education(candidate)
    penalty  = keyword_stuffer_penalty(candidate)

    raw = (
        skill    * 0.30 +
        exp      * 0.25 +
        text     * 0.20 +
        behavior * 0.18 +
        edu      * 0.07
    ) - penalty

    return {
        "final_score":     round(clamp(raw), 4),
        "skill_score":     round(skill, 4),
        "exp_score":       round(exp, 4),
        "text_score":      round(text, 4),
        "behavior_score":  round(behavior, 4),
        "edu_score":       round(edu, 4),
        "penalty":         round(penalty, 4),
    }