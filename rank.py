"""
rank.py — Main script. Reads all 100K candidates, scores them,
and produces the final submission CSV with top 100 ranked candidates.

Run: python rank.py
"""

import json
import csv
import time
from tqdm import tqdm

from honeypot import detect_honeypot
from features import compute_final_score
from reasoning import generate_reasoning

# ── CONFIG ───────────────────────────────────────────────
INPUT_FILE  = "candidates.jsonl"
OUTPUT_FILE = "submission.csv"
TOP_N       = 100

# ── STEP 1: LOAD ALL CANDIDATES ──────────────────────────
print("Loading candidates...")
start_time = time.time()

candidates = []
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            candidates.append(json.loads(line))

print(f"Loaded {len(candidates):,} candidates in {time.time()-start_time:.1f}s")

# ── STEP 2: HONEYPOT DETECTION ───────────────────────────
print("\nRunning honeypot detection...")

clean_candidates = []
honeypot_count = 0

for c in tqdm(candidates, desc="Filtering honeypots"):
    is_fake, reasons = detect_honeypot(c)
    if is_fake:
        honeypot_count += 1
    else:
        clean_candidates.append(c)

print(f"Honeypots removed: {honeypot_count:,}")
print(f"Clean candidates:  {len(clean_candidates):,}")

# ── STEP 3: SCORE EVERY CANDIDATE ────────────────────────
print("\nScoring candidates...")

scored = []
for c in tqdm(clean_candidates, desc="Scoring"):
    scores = compute_final_score(c)
    scored.append({
        "candidate": c,
        "scores":    scores,
    })

# ── STEP 4: SORT AND TAKE TOP 100 ────────────────────────
print("\nRanking top 100...")

scored.sort(key=lambda x: x["scores"]["final_score"], reverse=True)
top100 = scored[:TOP_N]

# ── STEP 5: GENERATE REASONING ───────────────────────────
print("Generating reasoning...")

results = []
for rank, item in enumerate(top100, start=1):
    c      = item["candidate"]
    scores = item["scores"]

    candidate_id = c.get("candidate_id", f"UNKNOWN_{rank}")
    final_score  = scores["final_score"]
    reasoning    = generate_reasoning(c, scores)

    results.append({
        "candidate_id": candidate_id,
        "rank":         rank,
        "score":        final_score,
        "reasoning":    reasoning,
    })

# ── STEP 6: WRITE CSV ────────────────────────────────────
print(f"\nWriting {OUTPUT_FILE}...")

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["candidate_id", "rank", "score", "reasoning"])
    writer.writeheader()
    writer.writerows(results)

# ── DONE ─────────────────────────────────────────────────
elapsed = time.time() - start_time
print(f"\n✅ Done in {elapsed:.1f} seconds")
print(f"📄 Output: {OUTPUT_FILE}")
print(f"\nTop 5 candidates:")
print("-" * 60)
for r in results[:5]:
    print(f"Rank {r['rank']:>3} | Score: {r['score']:.4f} | {r['candidate_id']}")
    print(f"         {r['reasoning'][:80]}...")
    print()