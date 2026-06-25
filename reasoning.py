"""
reasoning.py — Generates human-readable explanation for each candidate.
Judges specifically check reasoning quality — must reference REAL data.
"""

from datetime import datetime, date


def days_since(date_str):
    if not date_str:
        return 999
    try:
        d = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        return (date.today() - d).days
    except:
        return 999


def generate_reasoning(candidate: dict, scores: dict) -> str:
    profile  = candidate.get("profile", {})
    career   = candidate.get("career_history", [])
    skills   = candidate.get("skills", [])
    sig      = candidate.get("redrob_signals", {})

    parts = []

    # ── EXPERIENCE ───────────────────────────────────────
    years = profile.get("years_of_experience", 0)
    title = profile.get("current_title", "")
    company = profile.get("current_company", "")

    if title and company:
        parts.append(f"{years} yrs exp — currently {title} at {company}.")
    elif title:
        parts.append(f"{years} yrs exp as {title}.")
    else:
        parts.append(f"{years} yrs of experience.")

    # ── TOP SKILLS ───────────────────────────────────────
    KEY_SKILLS = [
        "embedding", "vector", "retrieval", "ranking", "faiss",
        "pinecone", "weaviate", "qdrant", "elasticsearch", "python",
        "ndcg", "mrr", "semantic search", "reranking", "fine-tuning",
        "recommendation", "transformer", "bert", "llm",
    ]

    matched = []
    for s in skills:
        name = s.get("name", "").lower()
        prof = s.get("proficiency", "")
        dur  = s.get("duration_months", 0)
        for key in KEY_SKILLS:
            if key in name:
                if prof in ("expert", "advanced") and dur >= 12:
                    matched.append(s["name"])
                elif dur >= 6:
                    matched.append(s["name"])
                break

    if matched:
        parts.append(f"Strong skills: {', '.join(matched[:4])}.")

    # ── CAREER HISTORY ───────────────────────────────────
    CAREER_KEYWORDS = [
        "retrieval", "ranking", "embedding", "vector search",
        "recommendation", "deployed", "production", "pipeline",
        "ranker", "reranker", "search system", "ml system",
    ]

    career_hits = []
    for job in career:
        desc = job.get("description", "").lower()
        for kw in CAREER_KEYWORDS:
            if kw in desc:
                career_hits.append(kw)
                break

    if career_hits:
        unique_hits = list(dict.fromkeys(career_hits))[:3]
        parts.append(f"Career history shows: {', '.join(unique_hits)} work.")

    # ── BEHAVIORAL SIGNALS ───────────────────────────────
    rrr = sig.get("recruiter_response_rate", 0)
    staleness = days_since(sig.get("last_active_date", ""))
    icr = sig.get("interview_completion_rate", 0)
    notice = sig.get("notice_period_days", 999)
    github = sig.get("github_activity_score", -1)

    if rrr >= 0.7:
        parts.append(f"High recruiter response rate ({int(rrr*100)}%).")
    elif rrr <= 0.2:
        parts.append(f"Low recruiter response rate ({int(rrr*100)}%).")

    if staleness <= 7:
        parts.append("Active within last 7 days.")
    elif staleness <= 30:
        parts.append(f"Active {staleness} days ago.")
    elif staleness > 180:
        parts.append(f"Inactive for {staleness} days — availability risk.")

    if notice <= 30:
        parts.append(f"Notice period: {notice} days — immediately available.")
    elif notice > 90:
        parts.append(f"Long notice period: {notice} days.")

    if github != -1 and github >= 60:
        parts.append(f"Active GitHub (score: {github}).")

    if icr >= 0.8:
        parts.append(f"Strong interview show-up rate ({int(icr*100)}%).")

    # ── PENALTIES ────────────────────────────────────────
    if scores.get("penalty", 0) >= 0.3:
        parts.append("Warning: keyword stuffing detected — skills not backed by career history.")

    if scores.get("exp_score", 1) < 0.3:
        parts.append("Note: services-only or non-engineering background.")

    # ── FALLBACK ─────────────────────────────────────────
    if len(parts) <= 1:
        parts.append("Limited signal — profile lacks depth for this role.")

    return " ".join(parts)