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
        # In a real production DB, we'd query pgvector here.
        # For the hackathon demo, we dynamically inject the JD and trigger our optimized engine.
        
        # Write the incoming JD to a temporary file for rank.py to read
        os.makedirs("data", exist_ok=True)
        with open("data/current_jd.txt", "w", encoding="utf-8") as f:
            f.write(payload.job_description)
            
        # Trigger the deterministic ranking pipeline
        result = subprocess.run(
            ["python", "rank.py", "--candidates", "data/sample_candidates.jsonl", "--out", "submission.csv"],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            raise Exception(result.stderr)
            
        return {"status": "success", "message": "Candidates ranked successfully. Output written to submission.csv."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy", "architecture": "Zero-Trust Semantic Engine"}
