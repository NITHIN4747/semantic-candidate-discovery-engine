"""
scripts/read_jd.py
==================
Reads job_description.docx and prints the raw text.
Run once to extract the text, then paste into rank.py JOB_DESCRIPTION.
"""
import sys

try:
    from docx import Document
except ImportError:
    print("Installing python-docx...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-docx", "-q"])
    from docx import Document

jd_path = r"e:\redrob_ai\[PUB] India_runs_data_and_ai_challenge\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\job_description.docx"

import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

doc = Document(jd_path)
lines = [para.text for para in doc.paragraphs if para.text.strip()]
out_path = r"e:\redrob_ai\semantic-candidate-discovery-engine\scripts\jd_raw.txt"
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"Written {len(lines)} paragraphs to: {out_path}")
for line in lines[:10]:
    print(" ", line[:100])
