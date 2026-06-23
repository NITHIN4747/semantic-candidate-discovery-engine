# TrioLogic | Semantic Talent Discovery OS
**INDIA RUNS Hackathon - Track 1: Data & AI Challenge**

---

## Slide 1: Title Slide
* **Title:** Semantic Candidate Discovery Engine
* **Subtitle:** Zero-Trust Architecture, Deterministic Ranking, Offline Scale
* **Team:** TrioLogic (Nithin, Raghul, Thibish)
* **Visual:** High-level icon representing a neural network matching a candidate profile to a job description.

---

## Slide 2: The Core Philosophy & The "Traps"
* **The Problem:** Keyword matching fails. "Marketing Managers" with AI keywords shouldn't rank for "Senior AI Engineer" roles.
* **Our Solution:** True Semantic Understanding combined with Behavioral Availability.
* **Overcoming the Dataset Traps:**
    * *Trap:* Keyword stuffing -> *Solution:* Sentence-Transformer Embeddings extract structural meaning.
    * *Trap:* Perfect profile, unresponsive candidate -> *Solution:* Custom Behavioral Multiplier (`_behavioral_modifier`) scales semantic score against `recruiter_response_rate` and `last_active_date`.

---

## Slide 3: The Ranking Engine (Algorithm & Scale)
* **Model:** `all-MiniLM-L6-v2` (384-dimensional dense vectors, CPU-optimized).
* **Deterministic Math:** Pure Python `cosine_similarity` implementation with NO external vector libraries (NumPy/SciPy excluded to respect sandbox constraints).
* **Chunked Streaming Pipeline:** 
    * Never loads the 487MB `candidates.jsonl` into memory at once.
    * Uses `batch_size=32` to maximize CPU throughput while safely clearing the 16GB RAM limit.
    * *Metric:* Processes 50,000 JSONL candidates in <5 minutes.

---

## Slide 4: Zero-Trust Network Topology (AWS)
* **The Blueprint:**
    * Custom isolated VPC.
    * **Network Load Balancer (NLB):** The only public entry point (Port 443).
    * **Strict SG Matrix:** The EC2 compute node *only* accepts traffic from the NLB (Port 8443). The RDS vector database *only* accepts traffic from the EC2 node (Port 5432).
* **Visual:** Architecture diagram showing VPC, Subnets, NLB, EC2, and RDS with security group routing paths explicitly drawn.

---

## Slide 5: Identity & Hardware Attestation
* **IMDSv2 Enforced:** EC2 instances launched with `HttpPutResponseHopLimit=2` to securely allow Dockerized containers to fetch metadata, mitigating SSRF vulnerabilities.
* **Passwordless Database Auth:** Ephemeral tokens generated via IAM (`rds-db:connect`) grant the application access to RDS. Zero static master passwords exist in the application state.
* **No SSH Keys:** `AmazonSSMManagedInstanceCore` utilized for secure terminal access. Port 22 is disabled globally.

---

## Slide 6: Database & UI Layer
* **Vector Storage:** Amazon RDS PostgreSQL 15+ utilizing the `pgvector` extension.
* **API Middleware:** FastAPI wrapper serving deterministic ranking pipelines.
* **Live Telemetry:** Streamlit UI executing against load-tested endpoints (Artillery configuration included for performance observability).
* **Visual:** Split screen screenshot showing the Streamlit UI (left) and the live Artillery load-testing metrics (right).

---

## Slide 7: Conclusion & Impact
* We didn't just build a filter; we built an end-to-end, production-ready enterprise Talent OS capable of scaling dynamically while preserving uncompromising security standards.
* **Ready for Production.**
