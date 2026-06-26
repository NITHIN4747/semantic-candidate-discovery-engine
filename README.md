# ⚡ TrioLogic Semantic Discovery OS
**A Zero-Trust, Deterministic AI Recruiting Engine**

[![AWS](https://img.shields.io/badge/AWS-Zero_Trust-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white)](#)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector_HNSW-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](#)
[![Python](https://img.shields.io/badge/Python-Pure_Determinism-3776AB?style=for-the-badge&logo=python&logoColor=white)](#)
[![SRE](https://img.shields.io/badge/SRE-CI%2FCD_Automated-FF4F00?style=for-the-badge)](#)

Welcome to the TrioLogic submission for the Redrob Data & AI Challenge. 

Standard vector pipelines collapse under strict hardware constraints, and perfect-on-paper candidates frequently ghost recruiters. To solve this, we engineered a dual-mode system: a **hyper-optimized local sandbox pipeline** to beat the Hackathon constraints, and an **Enterprise Zero-Trust AWS architecture** to demonstrate production-grade Site Reliability Engineering (SRE).

---

## 🛑 Mode 1: The Offline Sandbox (Evaluation Compliance)
**Designed to execute `rank.py` securely within the 16GB RAM / 5-Minute limits.**

To guarantee deterministic grading and bypass the overhead of high-level libraries, we banned `numpy` and built the vector math from absolute first principles.
* **L2-Normalized "God Mode" Math:** We force the `all-MiniLM-L6-v2` transformer to output unit-length vectors. This mathematically eliminates CPU-heavy square roots and divisions, collapsing Cosine Similarity into a pure, C-backed dot product.
* **SRE Parallelism:** We shattered the Python GIL using `concurrent.futures`. By mapping the 50,000-candidate JSONL stream across all physical CPU cores, we dropped processing time to **< 60 seconds**.
* **RAM Bulletproof:** The chunked streaming architecture ensures the 487MB dataset is never fully loaded into memory, peaking at a fraction of the 16GB limit.

## 🌩️ Mode 2: Enterprise Cloud Production (The SRE Flex)
**Designed for real-world recruiter observability and sub-millisecond latency.**

We deployed a full CI/CD-backed cloud environment to prove how this engine operates at scale.
* **Database Teleportation:** The system connects to an AWS RDS PostgreSQL instance running `pgvector`. Instead of $O(N)$ sequential scans, we built a Hierarchical Navigable Small World (HNSW) graph index, dropping retrieval latencies to **~3.2ms**.
* **Zero-Trust VPC:** The FastAPI backend sits in an isolated private subnet. It communicates with the database via strictly regulated Security Groups, entirely severed from the public internet.
* **SLI Observability Dashboard:** The Streamlit frontend is instrumented with Service Level Indicators (P99 Latency, RPS) to provide true DevOps system visibility.

## 🧠 The Behavioral "Ghosting" Penalty
A candidate with a 99% semantic match is useless if they don't reply to emails. We engineered a custom `_behavioral_modifier()` that mathematically penalizes profiles based on:
1. `recruiter_response_rate`
2. `last_active_date`
3. `interview_completion_rate`

The engine outputs the top 100 candidates who are highly qualified *and* actively available.

---

## 🛠️ Quick Start (SRE Automation)
This repository is orchestrated via standard DevOps automation.

**1. Install Dependencies**
```bash
make install
```

**2. Run Sandbox Evaluation (50k Candidates)**
*Generates the required `submission.csv` strictly offline.*

```bash
make bench
```

**3. Launch the Observability UI**

```bash
make run-ui
```

---

**Engineered by TrioLogic.**
