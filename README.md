# Intelligent Candidate Ranking System
### India Runs Data & AI Challenge 2026 — Submission by Madhav

---

##  Problem Statement

Recruiters go through hundreds of profiles and still miss the right person — not because the talent isn't there, but because keyword filters can't see what actually matters.

This system ranks 100,000 candidate profiles against a **Senior AI Engineer (Founding Team)** job description — the way a great recruiter would. Not by matching keywords, but by understanding who genuinely fits the role.

---

##  Results

| Metric | Value |
|---|---|
| Total Candidates Processed | 100,000 |
| Honeypots Detected & Removed | ~80+ |
| Final Ranked Candidates | 100 |
| Top Score | 0.9399 |
| Runtime | < 60 seconds |
| RAM Usage | < 4 GB |
| API Calls During Ranking | 0 |

**Top 5 Candidates:**
| Rank | Candidate | Company | Score |
|---|---|---|---|
| 1 | CAND_0077337 | Paytm | 0.9399 |
| 2 | CAND_0071974 | Netflix | 0.9281 |
| 3 | CAND_0081846 | Razorpay | 0.9158 |
| 4 | CAND_0002025 | Apple | 0.8985 |
| 5 | CAND_0018499 | Zomato | 0.8737 |

---

##  Architecture

```
candidates.jsonl  (100,000 profiles)
        │
        ▼
┌─────────────────────┐
│  Honeypot Detector  │  ← removes ~80 fake/impossible profiles
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  Feature Extractor  │  ← builds 5 scores per candidate
│                     │
│  • Skill Score      │  ← matches required skills weighted by proficiency + duration
│  • Experience Score │  ← years, company type, title, job-hopping
│  • Career Text Score│  ← reads actual job descriptions for real signals
│  • Behavioral Score │  ← redrob signals: response rate, recency, github, etc.
│  • Education Score  │  ← institution tier + relevant field
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│   Scoring Engine    │  ← weighted formula → final score 0.0 to 1.0
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  Keyword Stuffer    │  ← penalizes AI buzzwords not backed by career history
│  Penalty Module     │
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│   Top 100 Ranking   │  ← sort by final score, take top 100
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  Reasoning Generator│  ← generates 2-3 sentence explanation per candidate
└─────────────────────┘
        │
        ▼
   submission.csv
```

---

## Scoring Formula

```
Final Score =
    (Skill Match Score    × 0.30)
  + (Experience Score     × 0.25)
  + (Career Text Score    × 0.20)
  + (Behavioral Score     × 0.18)
  + (Education Score      × 0.07)
  - (Keyword Stuffer Penalty)
```

### Feature Details

**1. Skill Match Score (30%)**
- Checks for required skills: embeddings, vector DBs, retrieval systems, ranking, Python, NDCG, etc.
- Weighted by proficiency level (beginner → expert) AND duration_months
- A skill listed as "expert" with 1 month of use scores far lower than "intermediate" with 24 months
- This directly catches keyword stuffers

**2. Experience Score (25%)**
- Peak score for 5–9 years (per JD requirement)
- Heavy penalty for services-only background (TCS, Infosys, Wipro, Accenture, etc.)
- Penalty for non-engineering titles (marketing, HR, sales)
- Penalty for job-hopping (avg tenure < 10 months)
- Penalty for architect/VP titles who may not actively code

**3. Career Text Score (20%)**
- Reads free-text job description fields in career history
- Searches for real signals: "deployed", "production", "vector search", "ranking pipeline", etc.
- Catches hidden gems — candidates who did the work but didn't list it formally as a skill
- This is the key differentiator from pure keyword-matching systems

**4. Behavioral Score (18%)**
- Uses 23 redrob_signals fields
- Recruiter response rate (25% weight) — most important hirability signal
- Last active date recency (20%) — inactive 6+ months = down-ranked
- Interview completion rate (15%) — do they show up?
- Notice period (10%) — shorter = more available
- GitHub activity score (10%) — real engineering signal
- Open to work flag, profile completeness, saved by recruiters

**5. Education Score (7%)**
- Institution tier (Tier 1 = IIT/IISc level → Tier 4)
- Relevant field bonus (CS, ML, Data Science, Statistics, etc.)

---

## Trap Detection

### Honeypot Detection
Profiles are flagged as honeypots and excluded if they have 2+ of:
- Claims "expert" proficiency in a skill with ≤2 months of use
- Claims "expert" in 8+ skills (unrealistically broad)
- Claimed job duration doesn't match actual start/end dates
- Years of experience claimed far exceeds career history total
- 5+ expert skills with zero endorsements
- Future start dates in career history

### Keyword Stuffer Penalty
Candidates who list AI buzzwords (RAG, LLM, GPT, embeddings, vector) in skills but whose career history descriptions never mention this work receive a score penalty of up to 0.4.

---

## Project Structure

```
redrob-ranker/
├── rank.py           # Main pipeline — run this to produce submission.csv
├── features.py       # All feature extraction and scoring logic
├── honeypot.py       # Fake profile detection
├── reasoning.py      # Generates human-readable reasoning per candidate
├── app.py            # Streamlit demo app
├── submission.csv    # Final ranked output (top 100)
├── requirements.txt  # Python dependencies
└── README.md
```

---

## How to Run

### Requirements
- Python 3.8+
- CPU only (no GPU needed)
- ~4 GB RAM
- Runtime: ~60 seconds for 100K candidates

### Setup
```bash
git clone https://github.com/madhav1431-create/redrob-candidate-ranker.git
cd redrob-candidate-ranker
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

### Run the Ranker
```bash
# Place candidates.jsonl in the same folder
python rank.py
# Output: submission.csv
```

### Run the Demo App
```bash
streamlit run app.py
# Opens at http://localhost:8501
```

---

##  Demo App Features

- **Score Distribution Chart** — visual overview of all 100 ranked candidates
- **Filterable Results** — filter by minimum score, top N, or search by candidate ID
- **Live Candidate Scorer** — enter any candidate ID from the full 100K dataset to see their complete score breakdown and reasoning
- **Honeypot Checker** — instantly shows whether a candidate triggered fraud detection

---

##  Technical Constraints Met

| Constraint | Status |
|---|---|
| CPU only | ✅ |
| No GPU | ✅ |
| RAM < 16 GB | ✅ (~4 GB used) |
| Runtime < 5 minutes | ✅ (~60 seconds) |
| No hosted LLM API calls | ✅ |
| Exactly 100 candidates | ✅ |
| Required CSV format | ✅ |

---

##  Future Improvements

- Add semantic similarity using local sentence-transformers model for deeper JD-to-career-text matching
- Train a learning-to-rank model on historical hiring decisions
- Add cross-validation of scores using multiple JD framings
- Build a recruiter feedback loop to refine weights over time

---

##  Author

**Madhav**
Submission for India Runs Data & AI Challenge 2026
