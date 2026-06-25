"""
honeypot.py — Detects fake/impossible candidate profiles.
If >10 honeypots appear in your top 100, you are DISQUALIFIED.
"""

from datetime import datetime, date


def parse_date(d):
    if not d:
        return None
    try:
        return datetime.strptime(d[:10], "%Y-%m-%d").date()
    except:
        return None


def detect_honeypot(candidate: dict) -> tuple:
    reasons = []
    profile = candidate.get("profile", {})
    skills = candidate.get("skills", [])
    career = candidate.get("career_history", [])
    today = date.today()

    # TRAP 1: Expert skill with near-zero usage duration
    expert_zero = [
        s["name"] for s in skills
        if s.get("proficiency") in ("expert", "advanced")
        and s.get("duration_months", 999) <= 2
    ]
    if len(expert_zero) >= 2:
        reasons.append(f"Expert in {len(expert_zero)} skills with <=2 months use")

    # TRAP 2: Too many expert skills (unrealistic)
    expert_count = sum(1 for s in skills if s.get("proficiency") == "expert")
    if expert_count >= 8:
        reasons.append(f"Claims expert in {expert_count} skills — unrealistic")

    # TRAP 3: Claimed duration doesn't match actual dates
    for job in career:
        start = parse_date(job.get("start_date"))
        duration_months = job.get("duration_months", 0)
        if start and duration_months:
            end = parse_date(job.get("end_date")) or today
            actual_months = (end.year - start.year) * 12 + (end.month - start.month)
            if duration_months > actual_months + 6:
                reasons.append(
                    f"Claimed {duration_months}mo at '{job.get('company')}' "
                    f"but dates only span {actual_months}mo"
                )

    # TRAP 4: Years of experience vs career history mismatch
    years_claimed = profile.get("years_of_experience", 0)
    total_career_months = sum(j.get("duration_months", 0) for j in career)
    total_career_years = total_career_months / 12
    if years_claimed > 3 and total_career_years > 0:
        if years_claimed / max(total_career_years, 1) > 2.5:
            reasons.append(
                f"Claims {years_claimed} yrs but career only totals {total_career_years:.1f} yrs"
            )

    # TRAP 5: Many expert skills but zero endorsements
    total_endorsements = sum(s.get("endorsements", 0) for s in skills)
    high_prof = [s for s in skills if s.get("proficiency") in ("expert", "advanced")]
    if len(high_prof) >= 5 and total_endorsements == 0:
        reasons.append(f"{len(high_prof)} expert skills but 0 endorsements")

    # TRAP 6: Future start dates
    for job in career:
        start = parse_date(job.get("start_date"))
        if start and start > today:
            reasons.append(f"Future start date at '{job.get('company')}'")

    is_honeypot = len(reasons) >= 2
    return is_honeypot, reasons