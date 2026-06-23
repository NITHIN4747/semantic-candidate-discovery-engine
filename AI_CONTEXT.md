# 0. System Prompt & Hackathon Master Context (Read First)

**Project:** Semantic Candidate Discovery Engine (Production-Grade)
**Initiative:** INDIA RUNS Hackathon (Track 1: Data & AI Challenge) | Hack2skill x Redrob AI
**Team:** TrioLogic (Nithin: Cloud Arch, Raghul: Data Science, Thibish: UI/UX)
**Repository Target:** `https://github.com/NITHIN4747/semantic-candidate-discovery-engine.git`

---

## 🎯 The Mission

We are building a production-grade, Zero-Trust cloud architecture that replaces legacy
lexical/keyword ATS systems with a High-Dimensional Semantic Proximity engine. The system
maps raw job descriptions and candidate profiles into vector embeddings to find conceptual
alignment, bypassing keyword-matching entirely.

---

## 🏗️ The Cloud Architecture (Target Environment)

This codebase will be deployed to a highly secure AWS environment:

- **Routing:** AWS API Gateway → VPC Link → Network Load Balancer (NLB) → EC2 Private Subnet.
- **Compute:** Dockerized FastAPI/Flask application running on EC2.
- **Database:** Amazon RDS PostgreSQL (private subnet) utilizing the `pgvector` extension for
  spatial vector queries.
- **Security Posture:** Passwordless DB auth via IAM (`rds-db:connect`), IMDSv2 (hop limit = 2),
  and NitroTPM hardware attestation for decrypting models at rest.

---

## ⚠️ THE SANDBOX RULES (CRITICAL AI INSTRUCTIONS)

The Hack2Skill evaluation environment enforces strict constraints. Any code generated for
this repository **MUST** adhere to these immutable rules:

### Rule 1 — Hardware & Execution Limits
The ranking pipeline (`rank.py`) must execute in **≤ 5 minutes** on a machine with
**CPU-only** constraints and **16 GB RAM**. No GPUs are available.

### Rule 2 — Total Offline Execution
The ranking script must run completely offline.
**NO EXTERNAL APIs** (OpenAI, Anthropic, Gemini, Cohere, Hugging Face Inference API, etc.)
are permitted during ranking.

### Rule 3 — Local LLM Strategy
Use highly efficient, CPU-friendly sentence-transformers:
- Preferred: `sentence-transformers/all-MiniLM-L6-v2` (384 dims, ~80 MB, very fast on CPU)
- Alternative: `BAAI/bge-small-en-v1.5` (higher quality, still CPU-feasible)

Model weights **must be pre-downloaded and bundled** into the Docker container.
They must not be fetched at runtime.

### Rule 4 — Algorithmic Determinism (NO NUMPY)
The Cosine Similarity math engine must be written **from first principles** using:
- Native Python `for` loops
- The standard `math` library only

**Do NOT import `numpy`, `scipy`, or `sklearn`** for any core ranking mathematics.

Reference implementation (this exact pattern is required):

```python
import math

def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for i in range(len(vec_a)):
        dot   += vec_a[i] * vec_b[i]
        norm_a += vec_a[i] * vec_a[i]
        norm_b += vec_b[i] * vec_b[i]
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))
```

### Rule 5 — Memory-Safe Ingestion
The input dataset (`candidates.jsonl`) is **~487 MB**. The code must stream this file
line-by-line using a generator pattern. Do **not** load the entire JSONL into memory at once.

```python
# CORRECT — streaming pattern
def iter_candidates(path: str):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

# WRONG — never do this
candidates = json.load(open("candidates.jsonl"))          # will OOM
candidates = [json.loads(l) for l in open("candidates.jsonl")]  # also OOM
```

### Rule 6 — Data Privacy & Repository Hygiene
The following file patterns are **strictly added to `.gitignore`** and must never be
committed to the repository:

```
data/*.csv
data/*.json
data/*.jsonl
*.jsonl
*.env
.env*
```

---

## 📊 Strict Output File Constraints (`submission.csv`)

The engine's final output must perfectly pass `validate_submission.py`. The generated
`submission.csv` must contain:

| Field | Constraint |
|-------|-----------|
| **Rows** | Exactly 101 rows: 1 header + 100 data rows |
| **Columns** | `candidate_id`, `rank`, `score`, `reasoning` |
| `rank` | Unique integers 1–100, no gaps, no duplicates |
| `score` | Float, **strictly non-increasing** by rank |
| **Tie-breaker** | Equal scores → ascending `candidate_id` alphabetically |
| `reasoning` | Short human-readable string per candidate |
| **Encoding** | UTF-8 |

Validate before submission:
```bash
python validate_submission.py your_team_id.csv
```

---

## 🗂️ Candidate Data Schema (from `candidate_schema.json`)

Each line in `candidates.jsonl` is a JSON object with:

```
candidate_id          string   CAND_XXXXXXX (7 digits)
profile               object   name, headline, summary, location, years_of_experience,
                               current_title, current_company, current_industry
career_history        array    up to 10 jobs (title, company, industry, description, duration_months)
education             array    up to 5 entries (institution, degree, field, tier: tier_1–tier_4)
skills                array    name, proficiency (beginner→expert), endorsements, duration_months
certifications        array    name, issuer, year
languages             array    language, proficiency
redrob_signals        object   23 platform signals including:
                               - open_to_work_flag (bool)
                               - recruiter_response_rate (0–1)
                               - github_activity_score (0–100, -1 if no GitHub)
                               - interview_completion_rate (0–1)
                               - offer_acceptance_rate (0–1, -1 if no history)
                               - notice_period_days (0–180)
                               - expected_salary_range_inr_lpa {min, max}
                               - preferred_work_mode (remote/hybrid/onsite/flexible)
                               - skill_assessment_scores {skill: 0–100}
                               - profile_completeness_score (0–100)
```

---

## 🔁 The Full Ranking Pipeline

```
[Job Description Text]
        │
        ▼
[Local Sentence Transformer] → [JD Vector: float[384]]
                                         │
                                         ▼
[candidates.jsonl] ──stream──► [Build candidate text blob]
                                [title + summary + skills + career]
                                         │
                                         ▼
                               [Local Sentence Transformer] → [Candidate Vector: float[384]]
                                         │
                                         ▼
                               [cosine_similarity(jd_vec, cand_vec)]  ← raw Python loops
                                         │
                                         ▼
                               [Maintain top-100 min-heap]
                                         │
                                         ▼
                               [Sort → write submission.csv]
```

---

## 🌿 Branch & Commit Protocol

**Branch prefixes:**
- `infra/...` — Nithin (Cloud Architect)
- `data/...` — Raghul (Data Scientist)
- `ui/...` `integration/...` — Thibish (UI/UX Engineer)

**Commit format:** `[TYPE] Short description`
- `[FEAT]` — New capability
- `[FIX]` — Bug or logic correction
- `[INFRA]` — VPC, security groups, deployment
- `[DOCS]` — README, architecture docs

**PR Policy:** Squash and Merge only. At least 1 review required.

---

## ✅ Final Deliverables Checklist

- [ ] `submission.csv` — 100 ranked candidates (validated by `validate_submission.py`)
- [ ] `submission_metadata.yaml` — filled from template
- [ ] GitHub repo — clean, no raw data, reproducible
- [ ] Sandbox/Live Demo URL — HuggingFace Spaces / Streamlit Cloud
- [ ] PDF Architecture Pitch Deck — NitroTPM, pgvector, zero-trust
- [ ] Demo Video — live system under load

**Deadline: June 30, 2026**
