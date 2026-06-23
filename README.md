# Semantic Candidate Discovery Engine

**Team:** TrioLogic — Nithin (Cloud Architect), Raghul (Data Science), Thibish (UI/UX)
**Initiative:** INDIA RUNS Hackathon (Track 1: Data & AI Challenge) | Hack2skill × Redrob AI
**Deadline:** June 30, 2026

> ⚠️ **AI Coding Assistants:** Read [`AI_CONTEXT.md`](../AI_CONTEXT.md) before generating any code.
> It contains the non-negotiable sandbox constraints for this project.

---

## What This Is

A production-grade **Semantic Candidate Discovery & Ranking Engine** that:
- Converts job descriptions and candidate profiles into **dense vector embeddings** using a locally hosted sentence-transformer model
- Computes **Cosine Similarity** using raw Python loops (no NumPy — sandbox constraint)
- Streams the 487 MB `candidates.jsonl` file memory-safely
- Outputs a ranked CSV of the top 100 candidates

---

## Quickstart

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Download the embedding model (one-time, requires internet)
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### 3. Place the dataset
```bash
# Copy candidates.jsonl into the data/ folder (it is gitignored)
cp /path/to/candidates.jsonl ./data/candidates.jsonl
```

### 4. Run the ranker
```bash
python rank.py --candidates ./data/candidates.jsonl --out ./submission.csv
```

### 5. Validate submission
```bash
python validate_submission.py submission.csv
```

---

## Project Structure

```
semantic-candidate-discovery-engine/
├── AI_CONTEXT.md              ← AI guardrail primer (read first!)
├── rank.py                    ← Main submission script (Raghul)
├── validate_submission.py     ← Official challenge validator
├── requirements.txt
├── .gitignore
│
├── app/                       ← FastAPI live search API (Nithin + Raghul)
│   ├── main.py
│   ├── ranker.py
│   └── schemas.py
│
├── docker/                    ← Containerization (Thibish)
│   └── Dockerfile
│
├── infra/                     ← AWS CDK / Terraform (Nithin)
│   ├── vpc.py
│   ├── ec2.py
│   └── rds.py
│
├── tests/                     ← Unit tests
│   └── test_cosine.py
│
└── data/                      ← Gitignored — never commit raw data
    └── candidates.jsonl       ← Place dataset here locally
```

---

## Architecture

```
[Internet]
    │
    ▼ HTTPS
[AWS API Gateway]
    │ VPC Link
    ▼
[Network Load Balancer]  (private subnet)
    │ TCP 8443
    ▼
[EC2 Docker Container]
  ├── FastAPI app
  ├── Local all-MiniLM-L6-v2 model
  └── Cosine Similarity Engine (raw Python loops)
    │ TCP 5432
    ▼
[Amazon RDS PostgreSQL + pgvector]
  └── Candidate vector index (HNSW)
```

---

## Sandbox Constraints (Non-Negotiable)

| Constraint | Value |
|-----------|-------|
| Runtime limit | ≤ 5 minutes |
| Hardware | CPU-only, 16 GB RAM |
| Network during ranking | ❌ None |
| External AI APIs | ❌ None (OpenAI, Anthropic, etc.) |
| NumPy for cosine sim | ❌ Forbidden |
| JSONL loading strategy | ✅ Stream line-by-line |

---

## Branch Strategy

| Branch prefix | Owner | Domain |
|--------------|-------|--------|
| `infra/...` | Nithin | AWS VPC, EC2, security groups |
| `data/...` | Raghul | Ranking logic, embeddings, schemas |
| `ui/...` `integration/...` | Thibish | Frontend, Docker, Streamlit |

## Commit Format
```
[FEAT] Add cosine similarity engine
[FIX] Fix streaming bug in iter_candidates
[INFRA] Add VPC security group rules
[DOCS] Update README with quickstart
```

---

## Deliverables Checklist

- [ ] `submission.csv` — 100 ranked candidates
- [ ] `submission_metadata.yaml` — filled and committed
- [ ] GitHub repo — clean, reproducible, no raw data
- [ ] Live sandbox URL — HuggingFace Spaces / Streamlit Cloud
- [ ] PDF Architecture Pitch Deck
- [ ] Demo video
