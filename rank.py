#!/usr/bin/env python3
"""
rank.py — Semantic Candidate Discovery Engine
=============================================
Team: TrioLogic | INDIA RUNS Hackathon (Track 1: Data & AI Challenge)
Owner: Raghul (Data Science) | Coordinated by: Nithin (Cloud Architect)

SANDBOX RULES ENFORCED IN THIS FILE:
  [1] Runs fully offline — zero network calls.
  [2] Streams candidates.jsonl line-by-line — never loads full 487MB into RAM.
  [3] Cosine Similarity computed using raw Python for-loops + math stdlib only.
      DO NOT import numpy / scipy / sklearn for core ranking math.
  [4] Completes in ≤ 5 minutes on CPU-only, 16 GB RAM.
  [5] Produces exactly 100 ranked rows in submission.csv.

Usage:
    python rank.py --candidates ./data/candidates.jsonl --out ./submission.csv
"""

import argparse
import csv
import heapq
import json
import math
import os
import sys
import time
from typing import Generator

# ---------------------------------------------------------------------------
# Sentence-Transformer import (CPU-only embedding model)
# The model is pre-downloaded — NO network call happens here at rank time.
# ---------------------------------------------------------------------------
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("[ERROR] sentence-transformers not installed. Run: pip install sentence-transformers")
    sys.exit(1)


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"   # 384-dim, ~80 MB, fast on CPU
TOP_K = 100                                               # number of candidates to rank

# ---------------------------------------------------------------------------
# JOB DESCRIPTION — extracted from job_description.docx (Hack2Skill dataset)
# Redrob AI | Senior AI Engineer — Founding Team
#
# Key insight from the JD (lines 63-68 of the docx):
#   "The right answer involves reasoning about the gap between what the JD says
#    and what the JD means."
#   "A candidate who has all the AI keywords listed as skills but whose title is
#    'Marketing Manager' is not a fit, no matter how perfect their skill list looks."
#   "Your ranking system should also weigh behavioral signals — a perfect-on-paper
#    candidate who hasn't logged in for 6 months and has a 5% recruiter response
#    rate is, for hiring purposes, not actually available. Down-weight them."
# ---------------------------------------------------------------------------
JOB_DESCRIPTION = """
Job Description: Senior AI Engineer — Founding Team
Company: Redrob AI (Series A AI-native talent intelligence platform)
Location: Pune/Noida, India (Hybrid) | Open to relocation from Tier-1 Indian cities
Employment Type: Full-time
Experience Required: 5-9 years in applied ML/AI roles at product companies

Role Overview:
We are seeking a highly technical Senior AI Engineer to own the intelligence layer
of Redrob's product — the ranking, retrieval, and matching systems that decide what
recruiters see when they search for candidates.

The ideal candidate has deep technical depth in modern ML systems combined with a
scrappy product-engineering attitude. We need someone who can ship a working ranker
in a week while also reasoning about long-term architecture.

What You Will Do:
- Own and improve the candidate ranking, retrieval, and semantic matching systems.
- Ship a v2 ranking system using embeddings, hybrid retrieval, and LLM-based re-ranking.
- Audit existing BM25 + rule-based scoring systems and replace with modern ML approaches.
- Set up evaluation infrastructure: offline benchmarks, online A/B testing, recruiter feedback loops.
- Design candidate-JD matching at scale, working with pgvector and vector databases.
- Mentor the next round of AI hires as the team grows from 4 to 12 engineers.

Things You Absolutely Need (Hard Requirements):
- Production experience with embeddings-based retrieval systems:
  sentence-transformers, OpenAI embeddings, BGE, E5, or similar.
  Must have handled embedding drift, index refresh, retrieval-quality regression in production.
- Production experience with vector databases or hybrid search infrastructure:
  Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, Elasticsearch, FAISS, pgvector.
- Strong Python with high code quality standards.
- Experience designing evaluation frameworks for ranking systems:
  NDCG, MRR, MAP, offline-to-online correlation, A/B test interpretation.
- At least one end-to-end ranking, search, or recommendation system shipped to real users at scale.
- 4-5 years in applied ML/AI roles at product companies (not pure services/consulting).

Nice to Have:
- LLM fine-tuning experience: LoRA, QLoRA, PEFT on open-source models (LLaMA, Mistral, Falcon).
- Learning-to-rank models: XGBoost-based or neural LTR.
- Hybrid retrieval: BM25 + dense retrieval, re-ranking pipelines.
- Prior exposure to HR-tech, recruiting-tech, or marketplace products.
- Background in distributed systems or large-scale inference optimization.
- Open-source contributions in the AI/ML space.
- AWS SageMaker, EC2, Docker, Kubernetes for ML infrastructure.

Required Technical Skills:
Python (expert), PyTorch or TensorFlow, Hugging Face Transformers,
Semantic Search, Embeddings, Vector Databases, NLP, Information Retrieval,
Ranking Systems, Recommendation Systems, MLOps, Docker, SQL,
Data Pipelines, Spark, Airflow, Machine Learning, Deep Learning,
Large Language Models, RAG, Fine-tuning, BERT, GPT architectures.

Ideal Candidate Profile:
6-8 years total experience, of which 4-5 are in applied ML/AI at product companies.
Strong opinions about retrieval (hybrid vs dense), evaluation (offline vs online),
and LLM integration (when to fine-tune vs prompt) backed by systems they actually built.
Located in or willing to relocate to Noida or Pune. Active and responsive on platforms.

Additional Context (Forward Deployed AI Systems Architect responsibilities):
Design and deploy semantic ranking pipelines utilizing vector databases.
Containerize and orchestrate local inference nodes using CPU-optimized LLMs.
Ensure algorithmic determinism by constructing mathematical logic from first principles.
Implement rigorous network isolation: VPC Links, IMDSv2 tokenization, zero-trust AWS.
"""


# ---------------------------------------------------------------------------
# RULE 3: COSINE SIMILARITY — RAW PYTHON LOOPS ONLY (NO NUMPY)
# ---------------------------------------------------------------------------
def cosine_similarity(vec_a: list, vec_b: list) -> float:
    """
    Compute cosine similarity between two equal-length float vectors.
    Implemented strictly with native Python for-loops and the math stdlib.
    DO NOT refactor this to use any vector math library — sandbox enforcement.
    """
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for i in range(len(vec_a)):
        dot    += vec_a[i] * vec_b[i]
        norm_a += vec_a[i] * vec_a[i]
        norm_b += vec_b[i] * vec_b[i]
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


# ---------------------------------------------------------------------------
# RULE 2: STREAMING JSONL READER — never loads entire file into RAM
# ---------------------------------------------------------------------------
def iter_candidates(path: str) -> Generator[dict, None, None]:
    """
    Stream candidates.jsonl line-by-line.
    The file is ~487 MB — loading it entirely would OOM a 16 GB machine.
    """
    with open(path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[WARN] Skipping malformed JSON at line {line_num}: {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# CANDIDATE TEXT BUILDER
# Converts structured candidate JSON into a single rich text blob
# for embedding. Weights important signals by repetition / ordering.
# ---------------------------------------------------------------------------
def build_candidate_text(c: dict) -> str:
    """
    Build a flat text representation of a candidate profile.
    The richer and more accurate this text, the better the semantic match.
    """
    parts = []
    profile = c.get("profile", {})

    # --- Core identity ---
    title = profile.get("current_title", "")
    summary = profile.get("summary", "")
    headline = profile.get("headline", "")
    yoe = profile.get("years_of_experience", 0)
    industry = profile.get("current_industry", "")

    if title:
        parts.append(f"Current Role: {title}")
    if headline:
        parts.append(f"Headline: {headline}")
    if summary:
        parts.append(f"Summary: {summary}")
    if yoe:
        parts.append(f"Years of Experience: {yoe}")
    if industry:
        parts.append(f"Industry: {industry}")

    # --- Skills (most semantically rich signal) ---
    skills = c.get("skills", [])
    if skills:
        # Sort by proficiency weight then endorsements
        proficiency_order = {"expert": 4, "advanced": 3, "intermediate": 2, "beginner": 1}
        skills_sorted = sorted(
            skills,
            key=lambda s: (proficiency_order.get(s.get("proficiency", ""), 0), s.get("endorsements", 0)),
            reverse=True
        )
        skill_names = [s["name"] for s in skills_sorted if s.get("name")]
        if skill_names:
            parts.append("Skills: " + ", ".join(skill_names))

    # --- Skill assessment scores (verified platform scores) ---
    signals = c.get("redrob_signals", {})
    assessment_scores = signals.get("skill_assessment_scores", {})
    if assessment_scores:
        top_assessed = sorted(assessment_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        assessed_text = ", ".join(f"{k} ({v:.0f}/100)" for k, v in top_assessed)
        parts.append(f"Verified Skill Assessments: {assessed_text}")

    # --- Career history ---
    career = c.get("career_history", [])
    for job in career[:4]:  # Top 4 most recent roles
        job_title = job.get("title", "")
        job_company = job.get("company", "")
        job_desc = job.get("description", "")
        job_industry = job.get("industry", "")
        duration = job.get("duration_months", 0)
        if job_title:
            parts.append(f"Role: {job_title} at {job_company} ({job_industry}, {duration} months). {job_desc}")

    # --- Education ---
    education = c.get("education", [])
    for edu in education[:2]:
        degree = edu.get("degree", "")
        field = edu.get("field_of_study", "")
        institution = edu.get("institution", "")
        tier = edu.get("tier", "")
        if degree:
            parts.append(f"Education: {degree} in {field} from {institution} ({tier})")

    # --- Certifications ---
    certs = c.get("certifications", [])
    if certs:
        cert_names = [c_item.get("name", "") for c_item in certs[:5] if c_item.get("name")]
        if cert_names:
            parts.append("Certifications: " + ", ".join(cert_names))

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# REASONING GENERATOR
# Produces a short, human-readable reasoning string for submission.csv
# ---------------------------------------------------------------------------
def build_reasoning(c: dict, score: float) -> str:
    """
    Generate a concise reasoning string for the submission.csv `reasoning` column.
    Must be human-readable and fit comfortably in a CSV cell.
    """
    profile = c.get("profile", {})
    signals = c.get("redrob_signals", {})
    skills  = c.get("skills", [])

    title = profile.get("current_title", "Unknown")
    yoe   = profile.get("years_of_experience", 0)

    # Count AI/ML-relevant skills
    ai_keywords = {
        "python", "pytorch", "tensorflow", "transformers", "llm", "nlp", "ml",
        "machine learning", "deep learning", "scikit-learn", "hugging face",
        "bert", "gpt", "rag", "fine-tuning", "lora", "qlora", "mlops",
        "docker", "kubernetes", "aws", "sagemaker", "spark", "airflow",
        "vector", "embeddings", "semantic", "computer vision", "speech",
        "image classification", "tts", "ner", "reinforcement learning",
    }
    ai_skill_count = sum(
        1 for s in skills
        if any(kw in s.get("name", "").lower() for kw in ai_keywords)
    )

    response_rate = signals.get("recruiter_response_rate", 0)
    open_to_work  = signals.get("open_to_work_flag", False)
    github_score  = signals.get("github_activity_score", -1)
    notice_days   = signals.get("notice_period_days", 90)

    parts = [f"{title} | {yoe:.1f} yrs exp | {ai_skill_count} AI/ML skills"]
    parts.append(f"response rate {response_rate:.0%}")
    if open_to_work:
        parts.append("open to work")
    if github_score >= 0:
        parts.append(f"GitHub score {github_score:.0f}")
    parts.append(f"notice {notice_days}d")
    parts.append(f"semantic score {score:.4f}")

    return " | ".join(parts)



# ---------------------------------------------------------------------------
# BEHAVIORAL SIGNAL MODIFIER
# ---------------------------------------------------------------------------
# The JD explicitly warns (lines 63-68 of job_description.docx):
#   "Your ranking system should also weigh behavioral signals — a perfect-on-paper
#    candidate who hasn't logged in for 6 months and has a 5% recruiter response
#    rate is, for hiring purposes, not actually available. Down-weight them."
#
# This function returns a multiplier in [0.5, 1.0] applied to the semantic score.
# It does NOT override the semantic signal — it adjusts it based on availability.
# ---------------------------------------------------------------------------
def _behavioral_modifier(c: dict) -> float:
    """
    Compute a behavioral availability multiplier for a candidate.
    Returns a float in [0.5, 1.0]:
      1.0 = fully available, engaged, responsive
      0.5 = available on paper but behaviorally disengaged
    """
    import datetime

    signals = c.get("redrob_signals", {})
    score = 1.0

    # 1. Recruiter response rate (0-1) — most important signal
    #    A 5% response rate candidate is effectively unavailable.
    response_rate = signals.get("recruiter_response_rate", 0.5)
    # Scale: 0% response → 0.7 penalty, 100% → no penalty
    score *= (0.7 + 0.3 * response_rate)

    # 2. Open to work flag — explicit availability signal
    if signals.get("open_to_work_flag", False):
        score *= 1.05  # small boost for explicitly available

    # 3. Last active date — recency matters
    last_active_str = signals.get("last_active_date", "")
    if last_active_str:
        try:
            last_active = datetime.date.fromisoformat(last_active_str)
            today = datetime.date(2025, 1, 1)  # reference date for dataset
            days_inactive = (today - last_active).days
            if days_inactive > 180:
                score *= 0.80   # inactive 6+ months: significant down-weight
            elif days_inactive > 90:
                score *= 0.92   # inactive 3-6 months: moderate down-weight
            elif days_inactive < 30:
                score *= 1.02   # active in last month: slight boost
        except ValueError:
            pass

    # 4. Interview completion rate — shows seriousness
    icr = signals.get("interview_completion_rate", 0.5)
    # Scale: 0% completion → slight penalty, 100% → slight boost
    score *= (0.90 + 0.10 * icr)

    # 5. Offer acceptance rate (–1 = no history, 0-1 = rate)
    oar = signals.get("offer_acceptance_rate", -1)
    if oar >= 0:
        # Low offer acceptance can mean picky or unreliable; high means serious
        score *= (0.95 + 0.05 * oar)

    # Clamp to [0.5, 1.0] — never let behavioral signals fully override semantic fit
    return max(0.5, min(1.0, score))


# ---------------------------------------------------------------------------
# MAIN RANKING PIPELINE
# ---------------------------------------------------------------------------
def rank_candidates(candidates_path: str, output_path: str) -> None:
    """
    Full ranking pipeline:
      1. Load the local embedding model (pre-downloaded — offline).
      2. Embed the fixed Job Description.
      3. Stream candidates.jsonl and embed each candidate.
      4. Maintain a min-heap of top-K candidates by cosine similarity.
      5. Write the top-K to submission.csv.
    """
    t_start = time.time()

    # ------------------------------------------------------------------
    # Step 1: Load the embedding model (local, no network call)
    # ------------------------------------------------------------------
    print(f"[1/5] Loading embedding model: {MODEL_NAME}")
    print("      (First run may take ~30s to load from disk. Subsequent runs are faster.)")

    # local_files_only=True enforces offline mode — will fail fast if model not cached
    model = SentenceTransformer(MODEL_NAME, device="cpu")
    print(f"      Model loaded in {time.time() - t_start:.1f}s")

    # ------------------------------------------------------------------
    # Step 2: Embed the Job Description
    # ------------------------------------------------------------------
    print("[2/5] Embedding Job Description...")
    jd_embedding = model.encode(JOB_DESCRIPTION, convert_to_tensor=False, show_progress_bar=False)
    jd_vec = jd_embedding.tolist()   # convert numpy array → plain Python list
    print(f"      JD vector: {len(jd_vec)} dimensions")

    # ------------------------------------------------------------------
    # Step 3 + 4: Stream candidates, embed, compute similarity, track top-K
    # ------------------------------------------------------------------
    print(f"[3/5] Streaming and ranking candidates in batches from: {candidates_path}")
    print("      Using batch_size=32 for optimal CPU throughput within RAM limits.")

    # Min-heap: stores (score, candidate_id, candidate_dict)
    # We use a min-heap of size K so we efficiently track the top-K
    # without sorting the full 50K candidates.
    heap: list = []   # (score, candidate_id, candidate_dict)
    processed = 0
    skipped = 0

    # Helper to yield chunks
    def iter_candidate_batches(path: str, batch_size: int = 32):
        batch = []
        for c in iter_candidates(path):
            batch.append(c)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

    for batch in iter_candidate_batches(candidates_path, batch_size=32):
        valid_cands = []
        cand_texts = []

        for cand in batch:
            candidate_id = cand.get("candidate_id", "")
            if not candidate_id:
                skipped += 1
                continue

            cand_text = build_candidate_text(cand)
            if not cand_text.strip():
                skipped += 1
                continue

            valid_cands.append(cand)
            cand_texts.append(cand_text)

        if not valid_cands:
            continue

        # Embed candidate batch in one go using batch_size=32
        cand_embeddings = model.encode(cand_texts, batch_size=32, convert_to_tensor=False, show_progress_bar=False)
        cand_vecs = cand_embeddings.tolist()

        for i, cand in enumerate(valid_cands):
            candidate_id = cand.get("candidate_id", "")
            cand_vec = cand_vecs[i]

            # RULE 3: Cosine similarity via raw Python loops (no NumPy)
            semantic_score = cosine_similarity(jd_vec, cand_vec)

            # --- Behavioral Signal Modifier ---
            # The JD explicitly warns: down-weight candidates who are
            # "perfect on paper" but behaviorally unavailable.
            # This multiplier adjusts the final score based on platform signals.
            score = semantic_score * _behavioral_modifier(cand)

            # Maintain top-K min-heap
            if len(heap) < TOP_K:
                heapq.heappush(heap, (score, candidate_id, cand))
            elif score > heap[0][0]:
                heapq.heapreplace(heap, (score, candidate_id, cand))

        # Progress reporting
        prev_processed = processed
        processed += len(valid_cands)
        
        # Print if we crossed a 1000 boundary
        if prev_processed // 1000 < processed // 1000:
            elapsed = time.time() - t_start
            best_score = heap[0][0] if heap else 0.0
            print(f"      Processed {processed:,} candidates | "
                  f"Elapsed: {elapsed:.0f}s | "
                  f"Heap min score: {best_score:.4f}")

    print(f"\n[4/5] Ranking complete.")
    print(f"      Processed: {processed:,} | Skipped: {skipped} | "
          f"Time: {time.time() - t_start:.1f}s")

    # ------------------------------------------------------------------
    # Step 5: Sort and write submission.csv
    # ------------------------------------------------------------------
    print(f"[5/5] Writing submission to: {output_path}")

    # Sort: descending full-precision score, then ascending candidate_id for tie-breaking.
    top_candidates = sorted(heap, key=lambda x: (-x[0], x[1]))

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])

        # We need to ensure the WRITTEN score (4 d.p.) is also non-increasing,
        # and that ties at the written precision are broken by ascending candidate_id.
        # Strategy: group consecutive entries with the same rounded score,
        # sort each group by candidate_id ascending, then write in order.
        rounded_groups = []
        current_group = []
        current_rounded = None

        for item in top_candidates:
            score, cand_id, cand = item
            r = f"{score:.4f}"
            if r != current_rounded:
                if current_group:
                    rounded_groups.append(current_group)
                current_group = [item]
                current_rounded = r
            else:
                current_group.append(item)
        if current_group:
            rounded_groups.append(current_group)

        # Within each same-rounded-score group, sort by candidate_id ascending
        rank_num = 1
        for group in rounded_groups:
            group_sorted = sorted(group, key=lambda x: x[1])  # ascending candidate_id
            for score, cand_id, cand in group_sorted:
                reasoning = build_reasoning(cand, score)
                writer.writerow([cand_id, rank_num, f"{score:.4f}", reasoning])
                rank_num += 1

    # ------------------------------------------------------------------
    # Final summary
    # ------------------------------------------------------------------
    total_time = time.time() - t_start
    print(f"\n{'='*60}")
    print(f"  [OK]  Submission generated: {output_path}")
    print(f"  [##]  Candidates ranked:    {min(len(top_candidates), TOP_K)}")
    print(f"  [1st] Top score:            {top_candidates[0][0]:.4f}")
    print(f"  [Nth] {TOP_K}th score:          {top_candidates[-1][0]:.4f}")
    print(f"  [t]   Total runtime:        {total_time:.1f}s")
    print(f"{'='*60}\n")
    print("Run validator: python validate_submission.py submission.csv")


# ---------------------------------------------------------------------------
# CLI ENTRY POINT
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Semantic Candidate Discovery Engine — TrioLogic | INDIA RUNS Hackathon"
    )
    parser.add_argument(
        "--candidates",
        required=True,
        help="Path to candidates.jsonl (e.g., ./data/candidates.jsonl)"
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output path for submission CSV (e.g., ./submission.csv)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if not os.path.exists(args.candidates):
        print(f"[ERROR] Candidates file not found: {args.candidates}")
        sys.exit(1)

    rank_candidates(
        candidates_path=args.candidates,
        output_path=args.out,
    )
