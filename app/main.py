from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import os

app = FastAPI(title="TrioLogic | Talent Discovery OS")

class JobDescriptionPayload(BaseModel):
    job_description: str

@app.post("/v1/rank")
async def trigger_ranking(payload: JobDescriptionPayload):
    try:
        # Write the incoming JD to disk so rank.py can pick it up.
        # rank.py checks for data/current_jd.txt at boot and prefers it over the hardcoded default.
        os.makedirs("data", exist_ok=True)
        with open("data/current_jd.txt", "w", encoding="utf-8") as f:
            f.write(payload.job_description)

        # Kick off the ranking pipeline as a subprocess.
        # timeout=300 matches the 5-minute sandbox limit — if rank.py hangs, the worker recovers.
        result = subprocess.run(
            ["python", "rank.py", "--candidates", "data/sample_candidates.jsonl", "--out", "submission.csv"],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            raise Exception(result.stderr)

        return {"status": "success", "message": "Candidates ranked. Output written to submission.csv."}

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Ranking pipeline timed out after 300s.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy", "architecture": "Zero-Trust Semantic Engine"}
