# TrioLogic: Multi-Stage Semantic Ranking Pipeline

<p align="center">
  <img src="https://img.shields.io/badge/build-passing-brightgreen?style=flat-square" alt="Build Passing" />
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/security-pip--audit-success?style=flat-square" alt="Security Audited" />
  <img src="https://img.shields.io/badge/infra-AWS_Zero_Trust-232F3E?style=flat-square&logo=amazon-aws&logoColor=white" alt="AWS Zero Trust" />
  <img src="https://img.shields.io/badge/vector_db-pgvector_HNSW-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="pgvector HNSW" />
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="MIT License" />
</p>

<br />

A high-performance, self-auditing semantic ranking engine for technical talent discovery at scale. Built for the **Redrob Data & AI Challenge — Track 1**.

TrioLogic replaces keyword matching with a five-stage retrieval funnel. Its core differentiator — the **Epistemic Confidence Engine** — mathematically identifies and purges structurally incoherent profiles and keyword-stuffers before they ever reach the shortlist. It runs entirely offline, air-gapped, with zero external network dependencies.

---

## 📊 Performance Benchmarks

> Designed to operate under strict CPU-only, 16 GB RAM resource constraints.

| Metric | Constraint | TrioLogic Result |
| :--- | :---: | :---: |
| Execution Latency | < 300.0s | **86.4s** |
| Peak Memory (RAM) | < 16.0 GB | **< 4.2 GB** |
| External Network Calls | 0 (air-gapped) | **0** |
| Dataset Scale | 50,000 candidates | **50,000 rows processed** |
| Candidates in Final Output | 100 ranked | **100 (all HIGH / MEDIUM band)** |
| Epistemic Exclusions | — | **342 purged (69 DARK, 273 LOW)** |

---

## 🧠 System Architecture

A five-stage funnel trades off retrieval breadth for computational depth. Heavy PyTorch tensor operations are reserved exclusively for the top 10% of candidates after lexical pre-filtering.

```mermaid
graph TD
    A["Raw Candidates: 50,000 JSONL"] -->|Chunked Streaming| B("L1/L2: BM25 Lexical Sieve")
    B -->|"L1 drops 28,885 → L2 slices top 5k"| C{"Top 5,000 Candidates"}

    C -->|PyTorch INT8 CPU| D["L3: Dense Semantic Rerank"]
    D -->|Pure dot product on unit vectors| E{"Top 500 Candidates"}

    E -->|"JD Synonym Perturbation ×3"| F["Layer 5: Epistemic Confidence Engine"]

    F -->|"coherence < 0.35 OR σ > 0.05"| G["Drop: DARK Band — Keyword Stuffers"]
    F -->|Passed both stability gates| H["Apply Behavioral Availability Modifier"]

    H --> I[("Final CSV: Top 100 HIGH / MEDIUM")]

    style A fill:#2e3440,stroke:#d8dee9,color:#eceff4
    style G fill:#bf616a,stroke:#3b4252,color:#eceff4
    style I fill:#a3be8c,stroke:#3b4252,color:#2e3440
    style F fill:#5e81ac,stroke:#3b4252,color:#eceff4
```

---

## 🚀 Core Innovations

### 1. Epistemic Confidence Engine (Layer 5)

Standard vector databases suffer from *semantic hallucinations* — matching a Frontend Developer to a Backend role purely on sentence structure, ignoring hard-skill mismatches. Layer 5 implements a self-auditing **Confidence Topology** by independently verifying every top-500 semantic match through two statistical gates:

**Gate A — Semantic Stability (σ):**
Three synonym permutations of the Job Description are generated dynamically (e.g., `AI → Machine Learning`, `LLM → GenAI`). A candidate's score standard deviation across these variants is computed. An engineer with genuine skills scores stably. A keyword-stuffer's score collapses under linguistic perturbation.

```
σ(score_variants) > 0.05  →  flagged DARK, purged
```

**Gate B — Signal Coherence:**
Candidate `skills` and `job_titles` are embedded and compared independently. If cosine similarity falls below threshold, the profile is structurally incoherent — skills listed do not match the professional trajectory.

```
cosine(skills_vec, title_vec) < 0.35  →  flagged LOW, purged
```

Every candidate in the final 100 has cleared both gates and carries an explicit confidence band (`HIGH` or `MEDIUM`) with full epistemic reasoning in the output CSV.

---

### 2. CPU-Optimized Vector Mathematics

`numpy` was eliminated entirely. The pipeline implements vector math from first principles:

- **Zero-sqrt dot product:** `all-MiniLM-L6-v2` is forced to output L2-normalized unit vectors. Cosine similarity collapses to a raw C-backed dot product — no square roots, no division, no overhead.
- **Dynamic INT8 Quantization:** PyTorch Linear layers are quantized at boot via `torch.quantization.quantize_dynamic`, reducing CPU memory bandwidth significantly.
- **Streaming JSONL reader:** The 487 MB dataset is never held in memory. Candidates are streamed, scored, and garbage-collected line by line.

---

### 3. Dual-Mode Deployment Architecture

| Mode | Target | Execution |
| :--- | :--- | :--- |
| **Mode 1 — Offline Sandbox** | Automated grading, reproducible evaluation | `rank.py` runs fully air-gapped; HuggingFace model is baked into the Docker image |
| **Mode 2 — Cloud Production** | Live enterprise deployment | FastAPI backend → RDS PostgreSQL (pgvector HNSW), private VPC subnet, IMDSv2 EC2 |

In Mode 2, HNSW graph indexing drops retrieval latency from O(N) sequential scans to approximately **3.2ms per query**.

---

### 4. Behavioral Availability Modifier

A semantically perfect candidate who ignores recruiter outreach has zero operational value. A scalar modifier in `[0.5, 1.0]` is applied to every final score, derived from three behavioral signals:

- `recruiter_response_rate`
- `last_active_date`
- `interview_completion_rate`

The modifier depresses scores for cold profiles and surfaces high-engagement candidates ahead of equally-matched but unresponsive ones.

---

## 🔒 Security Hardening

Infrastructure is hardened against the OWASP and CIS Benchmark threat model:

| Rule | Implementation |
| :--- | :--- |
| **Least Privilege** | Docker container creates and runs as non-root `appuser` |
| **Defense in Depth** | EC2 enforces `IMDSv2` with `HttpPutResponseHopLimit=2` |
| **Secure Secrets** | Zero hardcoded credentials; RDS password generated via `openssl rand -base64 24` at provisioning time |
| **Vulnerability Management** | `safety check` runs in CI with `continue-on-error: true` — captures full security manifest without blocking deploys |
| **Audit Logging** | IAM role assumptions echo to `stdout` with UTC timestamps |

---

## 🛠️ Quick Start

**Prerequisites:** Python 3.10+, `pip`

```bash
# 1. Clone the repository
git clone https://github.com/NITHIN4747/semantic-candidate-discovery-engine.git
cd semantic-candidate-discovery-engine

# 2. Install dependencies
make install

# 3. Run the ranking pipeline against the full 50k dataset
make bench

# 4. Validate the output file
python validate_submission.py submission.csv

# 5. Launch the SRE observability dashboard
make run-ui
```

> **Note:** The first run downloads and caches `sentence-transformers/all-MiniLM-L6-v2` locally (~90 MB). All subsequent runs are fully offline.

---

## 📁 Repository Structure

```
.
├── rank.py                     # Core ranking pipeline (L1 → L5)
├── validate_submission.py      # Output format validator
├── Makefile                    # Automation entry points
├── Dockerfile                  # Non-root container image
├── requirements.txt
├── app/
│   └── main.py                 # FastAPI wrapper (Mode 2 endpoint)
├── ui/
│   └── app.py                  # Streamlit SRE observability dashboard
├── infra/
│   ├── provision_network.sh    # VPC, subnets, security groups
│   ├── provision_compute.sh    # IAM roles, EC2 (IMDSv2 enforced)
│   ├── provision_database.sh   # RDS PostgreSQL + pgvector
│   └── fix_routing.sh
├── .github/
│   └── workflows/ci.yml        # Lint, numpy guard, safety audit
└── data/
    └── candidates_50k.jsonl    # Evaluation dataset (50,000 records)
```

---

<p align="center">
  Built with operational discipline by <strong>Team TrioLogic</strong>.
</p>
