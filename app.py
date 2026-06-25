"""
app.py — Streamlit demo for the candidate ranking system.
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import json
from features import compute_final_score
from honeypot import detect_honeypot
from reasoning import generate_reasoning

st.set_page_config(
    page_title="Candidate Ranker — RedRob",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Intelligent Candidate Ranking System")
st.markdown("**India Runs Data & AI Challenge** — Senior AI Engineer Role")
st.divider()

# ── LOAD SUBMISSION CSV ──────────────────────────────────
@st.cache_data
def load_results():
    return pd.read_csv("submission.csv")

df = load_results()

# ── SIDEBAR ──────────────────────────────────────────────
st.sidebar.header("🔍 Filters")
min_score = st.sidebar.slider("Minimum Score", 0.0, 1.0, 0.0, 0.01)
top_n = st.sidebar.slider("Show Top N", 10, 100, 25)
search_id = st.sidebar.text_input("Search by Candidate ID")

# ── METRICS ──────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Ranked", len(df))
col2.metric("Top Score", f"{df['score'].max():.4f}")
col3.metric("Avg Score", f"{df['score'].mean():.4f}")
col4.metric("Min Score", f"{df['score'].min():.4f}")

st.divider()

# ── SCORE DISTRIBUTION CHART ─────────────────────────────
st.subheader("📊 Score Distribution")
st.bar_chart(df.set_index("rank")["score"])

st.divider()

# ── RESULTS TABLE ────────────────────────────────────────
st.subheader("🏆 Top Candidates")

filtered = df[df["score"] >= min_score].head(top_n)

if search_id:
    filtered = df[df["candidate_id"].str.contains(search_id, case=False)]
    if filtered.empty:
        st.warning(f"No candidate found with ID containing '{search_id}'")

for _, row in filtered.iterrows():
    score = row["score"]

    # Color based on score
    if score >= 0.85:
        color = "🟢"
    elif score >= 0.70:
        color = "🟡"
    else:
        color = "🔴"

    with st.expander(
        f"{color} Rank #{int(row['rank'])} — {row['candidate_id']} — Score: {score:.4f}"
    ):
        st.markdown(f"**📝 Reasoning:**")
        st.info(row["reasoning"])
        st.markdown(f"**Score:** `{score:.4f}`")

st.divider()

# ── LIVE SCORER SECTION ──────────────────────────────────
st.subheader("🔬 Live Candidate Scorer")
st.markdown("Paste a candidate ID to see their detailed breakdown:")

cand_id_input = st.text_input("Enter Candidate ID (e.g. CAND_0077337)")

if cand_id_input:
    with st.spinner("Loading candidate..."):
        found = None
        with open("candidates.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                c = json.loads(line)
                if c.get("candidate_id") == cand_id_input.strip():
                    found = c
                    break

    if found:
        is_hp, hp_reasons = detect_honeypot(found)
        scores = compute_final_score(found)
        reasoning = generate_reasoning(found, scores)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📋 Profile")
            profile = found.get("profile", {})
            st.write(f"**Title:** {profile.get('current_title','N/A')}")
            st.write(f"**Company:** {profile.get('current_company','N/A')}")
            st.write(f"**Experience:** {profile.get('years_of_experience','N/A')} years")

            st.markdown("### 🚨 Honeypot Check")
            if is_hp:
                st.error(f"⚠️ HONEYPOT DETECTED")
                for r in hp_reasons:
                    st.write(f"- {r}")
            else:
                st.success("✅ Clean profile")

        with col2:
            st.markdown("### 📊 Score Breakdown")
            score_data = {
                "Skill Match":   scores["skill_score"],
                "Experience":    scores["exp_score"],
                "Career Text":   scores["text_score"],
                "Behavioral":    scores["behavior_score"],
                "Education":     scores["edu_score"],
                "Penalty":       -scores["penalty"],
                "FINAL SCORE":   scores["final_score"],
            }
            for k, v in score_data.items():
                if k == "FINAL SCORE":
                    st.metric(k, f"{v:.4f}")
                else:
                    st.progress(max(0.0, v), text=f"{k}: {v:.4f}")

        st.markdown("### 💬 Reasoning")
        st.info(reasoning)

    else:
        st.error(f"Candidate '{cand_id_input}' not found.")

st.divider()
st.caption("Built for India Runs Data & AI Challenge 2026")