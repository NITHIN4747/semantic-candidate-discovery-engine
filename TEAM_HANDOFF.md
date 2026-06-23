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
1. **Run the 50k Production Workload:**
   Pull the latest `main` branch. Ensure the full 487MB `candidates.jsonl` is sitting inside your local `data/` folder.
   Execute the batch-chunked ranking engine:
   ```bash
   python rank.py --candidates ./data/candidates.jsonl --out ./submission.csv
   ```
2. **Validate the Output:**
   Run the Hack2Skill official script to guarantee zero formatting errors:
   ```bash
   python validate_submission.py submission.csv
   ```
3. **Commit the Results:**
   Create a new branch (`data/final-submission`), add the verified `submission.csv`, and open a **Pull Request** for Nithin to review.

---

## 🎨 Thibish: UI/UX & Demo Recording
**Objective:** Spin up the Streamlit frontend and record the final split-screen demo.

### Your Action Items:
1. **Launch the Dashboard:**
   Pull the latest `main` branch. The `ui/app.py` script has already been written.
   ```bash
   pip install -r requirements.txt
   streamlit run ui/app.py
   ```
2. **Verify API Connection:**
   Ensure your local FastAPI backend (`app/main.py`) is running on port `8443` so the Streamlit UI can seamlessly route the payload.
3. **The Split-Screen Video Recording:**
   * **Left Side:** Your Streamlit UI.
   * **Right Side:** The terminal running the Artillery load test (`artillery run infra/load_test.yml`).
   * Show the judges the beautiful UI rendering results *while* the terminal matrix-scrolls with heavy concurrent load-testing metrics.
4. **Push UI Tweaks via PR:**
   If you need to tweak the CSS or visuals in `ui/app.py`, create a new branch (`ui/visual-polish`) and open a **Pull Request**.

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

*Let's close this out and win.*
