"""
app.py — Streamlit demo for Intelligent Candidate Ranking System
"""

import streamlit as st
import pandas as pd
import json
import random
from features import compute_final_score
from honeypot import detect_honeypot
from reasoning import generate_reasoning

st.set_page_config(
    page_title="Candidate Ranker",
    page_icon="",
    layout="wide"
)

# ── LOAD DATA ────────────────────────────────────────────
@st.cache_data
def load_results():
    return pd.read_csv("submission.csv")

@st.cache_data
def load_candidate(cand_id):
    with open("candidates.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            c = json.loads(line)
            if c.get("candidate_id") == cand_id:
                return c
    return None

df = load_results()

# ── HEADER ───────────────────────────────────────────────
st.markdown("#  Intelligent Candidate Ranking System")
st.markdown("**India Runs Data & AI Challenge 2026** — Senior AI Engineer Role")
st.divider()

# ── TOP METRICS ──────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Processed", "100,000")
c2.metric("Honeypots Removed", "~80+")
c3.metric("Final Ranked", "100")
c4.metric("Top Score", f"{df['score'].max():.4f}")
c5.metric("Runtime", "45.9s")
st.divider()

# ── TWO TABS ─────────────────────────────────────────────
tab1, tab2 = st.tabs([" Top 100 Rankings", "🔬 Candidate Inspector"])

# ════════════════════════════════════════════════════════
# TAB 1 — RANKINGS TABLE
# ════════════════════════════════════════════════════════
with tab1:

    st.markdown("### Top 100 Ranked Candidates")
    st.caption("Sorted by final score. Click any row to inspect that candidate in detail.")

    # Filter controls
    col1, col2 = st.columns([1, 2])
    with col1:
        top_n = st.slider("Show top N candidates", 10, 100, 25)
    with col2:
        search = st.text_input("🔍 Search by Candidate ID", placeholder="e.g. CAND_0077337")

    # Filter data
    if search:
        view = df[df["candidate_id"].str.contains(search, case=False)]
    else:
        view = df.head(top_n)

    if view.empty:
        st.warning("No candidates found.")
    else:
        # Display each candidate as a clean card
        for _, row in view.iterrows():
            score = row["score"]
            rank = int(row["rank"])

            if score >= 0.85:
                badge = " Strong Fit"
                color = "green"
            elif score >= 0.70:
                badge = " Good Fit"
                color = "orange"
            else:
                badge = " Moderate Fit"
                color = "red"

            with st.expander(
                f"**Rank #{rank}** — {row['candidate_id']} — Score: `{score:.4f}` — {badge}"
            ):
                st.markdown(f"** Why this candidate:**")
                st.info(row["reasoning"])

                # Button to inspect this candidate in detail
                if st.button(f"Inspect {row['candidate_id']} in detail →", key=f"btn_{rank}"):
                    st.session_state["inspect_id"] = row["candidate_id"]
                    st.session_state["active_tab"] = "inspector"
                    st.rerun()

# ════════════════════════════════════════════════════════
# TAB 2 — CANDIDATE INSPECTOR
# ════════════════════════════════════════════════════════
with tab2:

    st.markdown("###  Candidate Inspector")
    st.caption("See the full score breakdown for any candidate in the dataset.")

    # Input row
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        cand_input = st.text_input(
            "Enter Candidate ID",
            value=st.session_state.get("inspect_id", ""),
            placeholder="e.g. CAND_0077337"
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(" Random Top 10"):
            top_ids = df.head(10)["candidate_id"].tolist()
            st.session_state["inspect_id"] = random.choice(top_ids)
            st.rerun()

    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(" Show #1 Ranked"):
            st.session_state["inspect_id"] = df.iloc[0]["candidate_id"]
            st.rerun()

    # Use session state if set
    final_id = st.session_state.get("inspect_id", cand_input).strip()

    if final_id:
        with st.spinner(f"Loading {final_id}..."):
            candidate = load_candidate(final_id)

        if not candidate:
            st.error(f"Candidate '{final_id}' not found.")
        else:
            scores     = compute_final_score(candidate)
            reasoning  = generate_reasoning(candidate, scores)
            is_hp, hp_reasons = detect_honeypot(candidate)
            profile    = candidate.get("profile", {})
            sig        = candidate.get("redrob_signals", {})
            skills     = candidate.get("skills", [])
            career     = candidate.get("career_history", [])

            # ── ROW 1: Profile + Honeypot ──────────────────
            st.divider()
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 👤 Profile")
                st.markdown(f"**Name/ID:** {final_id}")
                st.markdown(f"**Title:** {profile.get('current_title', 'N/A')}")
                st.markdown(f"**Company:** {profile.get('current_company', 'N/A')}")
                st.markdown(f"**Experience:** {profile.get('years_of_experience', 'N/A')} years")
                st.markdown(f"**Summary:** {profile.get('summary', 'N/A')[:200]}...")

            with col2:
                st.markdown("####  Fraud Check")
                if is_hp:
                    st.error(" HONEYPOT DETECTED — this profile is suspicious")
                    for r in hp_reasons:
                        st.markdown(f"- {r}")
                else:
                    st.success("Clean profile — no fraud signals detected")

                # Rank info if in top 100
                match = df[df["candidate_id"] == final_id]
                if not match.empty:
                    rank_val = int(match.iloc[0]["rank"])
                    st.info(f"This candidate is ranked **#{rank_val}** in your top 100")
                else:
                    st.warning("This candidate did not make the top 100")

            # ── ROW 2: Score Breakdown ──────────────────────
            st.divider()
            st.markdown("####  Score Breakdown")

            score_cols = st.columns(6)
            score_cols[0].metric(" Final Score",  f"{scores['final_score']:.4f}")
            score_cols[1].metric(" Skill Match",  f"{scores['skill_score']:.4f}")
            score_cols[2].metric(" Experience",   f"{scores['exp_score']:.4f}")
            score_cols[3].metric(" Career Text",  f"{scores['text_score']:.4f}")
            score_cols[4].metric(" Behavioral",   f"{scores['behavior_score']:.4f}")
            score_cols[5].metric(" Education",    f"{scores['edu_score']:.4f}")

            if scores["penalty"] > 0:
                st.warning(f" Keyword stuffer penalty applied: −{scores['penalty']:.4f}")

            # Score bars
            bar_data = {
                "Skill Match":  scores["skill_score"],
                "Experience":   scores["exp_score"],
                "Career Text":  scores["text_score"],
                "Behavioral":   scores["behavior_score"],
                "Education":    scores["edu_score"],
            }
            st.bar_chart(bar_data)

            # ── ROW 3: Reasoning ───────────────────────────
            st.divider()
            st.markdown("####  Why This Candidate Was Ranked Here")
            st.info(reasoning)

            # ── ROW 4: Skills ──────────────────────────────
            st.divider()
            st.markdown("####  Skills")
            skill_cols = st.columns(4)
            for i, sk in enumerate(skills[:12]):
                skill_cols[i % 4].markdown(
                    f"**{sk.get('name')}** — {sk.get('proficiency','?')} "
                    f"({sk.get('duration_months', 0)} months)"
                )

            # ── ROW 5: Behavioral Signals ──────────────────
            st.divider()
            st.markdown("####  Behavioral Signals")
            b1, b2, b3, b4 = st.columns(4)
            b1.metric("Recruiter Response", f"{sig.get('recruiter_response_rate',0):.0%}")
            b2.metric("Last Active",        sig.get("last_active_date", "N/A"))
            b3.metric("Interview Rate",     f"{sig.get('interview_completion_rate',0):.0%}")
            b4.metric("Notice Period",      f"{sig.get('notice_period_days','?')} days")