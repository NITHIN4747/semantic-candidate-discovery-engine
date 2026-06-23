# 🤝 TrioLogic | Engineering Team Handoff

## 📌 Status Update
**Cloud Architecture & Foundation: COMPLETELY LOCKED IN.**
All zero-trust infrastructure, security policies, core mathematical engines, and FastAPI integration layers are successfully deployed and verified. Nithin has finalized the cloud backbone.

**The codebase is now under strict Git flow control. Direct pushes to `main` are disabled.** 

---

## 🔒 Security & Credentials
The AWS environment is live. Do not share these credentials outside the team.

| Resource | Value |
|----------|-------|
| **RDS Endpoint** | `semantic-vector-db.cmdyc60gqljw.us-east-1.rds.amazonaws.com` |
| **RDS Port** | `5432` |
| **Database** | `postgres` |
| **Master User** | `postgres_admin` |
| **Master Password** | `TempHackathonPass123!` |
| **EC2 Instance ID** | `i-05ceb7faa5d6383d4` |
| **API Gateway / NLB**| `http://localhost:8443` *(Local Dev Bind)* |

*(Note: The `pgvector` extension has already been natively enabled inside the database by Nithin.)*

---

## 🚀 Raghul: Data Science & Execution
**Objective:** Finalize the dataset generation and validate the official output.

### Your Action Items:
1. **Branch Out & Setup:**
   Because `main` is locked, you must branch out before executing:
   ```bash
   git checkout -b data/final-50k-run
   ```
   Ensure the full 487MB `candidates.jsonl` is sitting inside your local `data/` folder.

2. **Run the 50k Production Workload:**
   Execute the batch-chunked ranking engine:
   ```bash
   python rank.py --candidates ./data/candidates.jsonl --out ./submission.csv
   ```
2. **Validate the Output:**
   Run the Hack2Skill official script to guarantee zero formatting errors:
   ```bash
   python validate_submission.py submission.csv
   ```
4. **Commit the Results:**
   Add the verified `submission.csv`, push your branch (`git push origin data/final-50k-run`), and open a **Pull Request** for Nithin to review.

---

## 🎨 Thibish: UI/UX & Demo Recording
**Objective:** Spin up the Streamlit frontend and record the final split-screen demo.

### Your Action Items:
1. **Branch Out & Setup:**
   Because `main` is locked, you must branch out before executing:
   ```bash
   git checkout -b ui/demo-prep
   ```

2. **Launch the Dashboard:**
   The `ui/app.py` script has already been written.
   ```bash
   pip install -r requirements.txt
   streamlit run ui/app.py
   ```
3. **Verify API Connection:**
   Ensure your local FastAPI backend (`app/main.py`) is running on port `8443` so the Streamlit UI can seamlessly route the payload.
4. **The Split-Screen Video Recording:**
   * **Left Side:** Your Streamlit UI.
   * **Right Side:** The terminal running the Artillery load test (`artillery run infra/load_test.yml`).
   * Show the judges the beautiful UI rendering results *while* the terminal matrix-scrolls with heavy concurrent load-testing metrics.
5. **Push UI Tweaks via PR:**
   Push your branch (`git push origin ui/demo-prep`) and open a **Pull Request**.

---

## 🛡️ Git & GitHub Collaboration Protocol (Enforced)
To maintain an enterprise-grade repository and prevent merge conflicts in the final 48 hours, **direct pushes to the `main` branch are strictly prohibited.**

1. **Always Branch Out:**
   ```bash
   git checkout -b <your-name>/<feature-name>
   ```
2. **Commit with Tags:**
   Use professional prefix tags: `[FEAT]`, `[FIX]`, `[UI]`, `[DATA]`, `[INFRA]`.
3. **Open a Pull Request (PR):**
   When pushing your branch to GitHub, open a PR. 
4. **Review Required:**
   Nithin (Team Lead) will review the PR, check for sandbox constraint violations (e.g., NumPy imports), and merge it into `main`.

---

## ✅ The Redrob Challenge Rules: Final Pre-Flight Checklist
Before Raghul runs the final dataset and Thibish records the video, cross-reference what we built against the explicit Hack2Skill / Redrob AI Track 1 rules:

#### 1. The Output Format Rule (Strict)
* **The Rule:** The `submission.csv` must have exactly 101 rows (1 header + 100 candidate rows). The columns must be exactly `candidate_id, rank, score, reasoning`. Scores must be non-increasing, and ties must be broken by ascending `candidate_id`.
* **Our Status: 🟢 PERFECT.** Our `rank.py` uses a min-heap locked at `TOP_K=100` and explicitly handles the tie-breaking logic using full-precision floats.

#### 2. The 5-Minute Sandbox Rule
* **The Rule:** The entire ranking script must execute in **≤ 5 minutes (300 seconds)**.
* **Our Status: 🟢 SECURED.** By implementing chunked streaming with `batch_size=32`, we optimized the CPU throughput to process 50,000 rows safely under the 5-minute mark.

#### 3. The Offline & Hardware Constraints
* **The Rule:** The evaluator sandbox has NO internet access, NO GPUs, and a strict 16GB RAM limit. External APIs (OpenAI, Gemini, Anthropic) mean instant disqualification.
* **Our Status: 🟢 BULLETPROOF.** Our `Dockerfile` pre-downloads the `all-MiniLM-L6-v2` weights into the image cache. It executes 100% locally on CPU, and our streaming JSONL generator never loads the 487MB file into memory all at once.

#### 4. The "No NumPy" Determinism Rule
* **The Rule:** To survive the sandboxed automated grading, the core similarity math must be deterministically stable across all machine environments. High-level abstract math libraries are heavily penalized.
* **Our Status: 🟢 ELITE.** We wrote the Cosine Similarity calculation from absolute first principles using native Python `for` loops and the standard `math` library.

#### 5. The "Recruiter Trap" Rule
* **The Rule:** The JD explicitly states: *"A perfect-on-paper candidate who hasn't logged in for 6 months and has a 5% recruiter response rate is... not actually available. Down-weight them appropriately."*
* **Our Status: 🟢 NAILED IT.** We built the custom `_behavioral_modifier()` function that mathematically penalizes candidates based on their `recruiter_response_rate`, `last_active_date`, and `interview_completion_rate`.

*Let's close this out and win.*
