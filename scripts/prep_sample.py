"""
scripts/prep_sample.py
======================
One-time helper: converts sample_candidates.json (array of 50 objects)
into sample_candidates.jsonl (one JSON object per line) for dry-run testing.

Run from repo root:
    python scripts/prep_sample.py
"""

import json
import os

SRC = r"e:\redrob_ai\[PUB] India_runs_data_and_ai_challenge\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\sample_candidates.json"
DST = r"e:\redrob_ai\semantic-candidate-discovery-engine\data\sample_candidates.jsonl"

os.makedirs(os.path.dirname(DST), exist_ok=True)

with open(SRC, encoding="utf-8") as f:
    candidates = json.load(f)

with open(DST, "w", encoding="utf-8") as f:
    for c in candidates:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")

print(f"Written {len(candidates)} candidates to: {DST}")
