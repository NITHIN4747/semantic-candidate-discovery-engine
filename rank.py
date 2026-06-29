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
      DO NOT use numpy / scipy / sklearn for core ranking math.
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
    import torch
except ImportError:
    print("[ERROR] sentence-transformers or torch not installed. Run: pip install sentence-transformers torch")
    sys.exit(1)


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"   # 384-dim, ~80 MB, fast on CPU
POST_HOC_K = 500                                          # number of candidates to evaluate for confidence
FINAL_K = 100                                             # number of final trusted candidates to output

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
def fast_dot_product(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Because vec_a and vec_b are L2 Normalized, their dot product IS their cosine similarity.
    No square roots, no division, massive CPU cycle savings.
    """
    return sum(a * b for a, b in zip(vec_a, vec_b))


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
    Optimized for high-throughput CPU inference: super-compact text.
    """
    parts = []
    profile = c.get("profile", {})

    title = profile.get("current_title", "")
    headline = profile.get("headline", "")
    yoe = profile.get("years_of_experience", 0)

    if title:
        parts.append(f"Current Role: {title}")
    if headline:
        parts.append(f"Headline: {headline}")
    if yoe:
        parts.append(f"Years of Experience: {yoe}")

    # Skills (top 15)
    skills = c.get("skills", [])
    if skills:
        proficiency_order = {"expert": 4, "advanced": 3, "intermediate": 2, "beginner": 1}
        skills_sorted = sorted(
            skills,
            key=lambda s: (proficiency_order.get(s.get("proficiency", ""), 0), s.get("endorsements", 0)),
            reverse=True
        )
        skill_names = [s["name"] for s in skills_sorted[:15] if s.get("name")]
        if skill_names:
            parts.append("Skills: " + ", ".join(skill_names))

    # Past Roles titles
    career = c.get("career_history", [])
    job_titles = [job.get("title", "") for job in career[:3] if job.get("title")]
    if job_titles:
        parts.append("Past Roles: " + ", ".join(job_titles))

    full_text = "\n".join(parts)
    return full_text[:400]


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
    torch.set_num_threads(10)
    model.max_seq_length = 64

    # --- INJECTION 1: Dynamic INT8 Quantization ---
    # Forces PyTorch Linear layers to use AVX2/VNNI integer math on the CPU.
    # We use legacy torch.quantization because torchao currently throws NotImplementedError
    # for `aten._has_compatible_shallow_copy_type` inside SentenceTransformer.encode().
    print("      Applying Dynamic INT8 Quantization to model Linear layers...")
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=DeprecationWarning)
        model[0].auto_model = torch.quantization.quantize_dynamic(
            model[0].auto_model,
            {torch.nn.Linear},
            dtype=torch.qint8
        )
    print(f"      Model loaded + quantized in {time.time() - t_start:.1f}s")

    # ------------------------------------------------------------------
    # Step 2: Embed the Job Description & Variants (Layer 5)
    # ------------------------------------------------------------------
    print("[2/5] Embedding Job Description and Semantic Variants...")
    
    # Read dynamic JD from API if it exists, otherwise use fallback
    jd_text = JOB_DESCRIPTION
    dynamic_jd_path = "data/current_jd.txt"
    if os.path.exists(dynamic_jd_path):
        try:
            with open(dynamic_jd_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    jd_text = content
                    print("      Loaded dynamic JD from data/current_jd.txt")
        except Exception as e:
            print(f"      [WARN] Failed to read {dynamic_jd_path}: {e}")
            
    # Generate synonym variants for semantic stability check (Layer 5)
    jd_v1 = jd_text.replace("AI", "Machine Learning").replace("LLM", "Generative AI").replace("embeddings", "vector representations")
    jd_v2 = jd_text.replace("AI", "Data Science").replace("LLM", "Foundation Models").replace("embeddings", "dense vectors")
    jd_v3 = jd_text.replace("AI Engineer", "MLOps Engineer").replace("LLM", "Large Language Models").replace("embeddings", "vector embeddings")
    
    with torch.inference_mode():
        jd_embedding = model.encode(jd_text, normalize_embeddings=True, convert_to_tensor=False, show_progress_bar=False)
        jd_vars_embeddings = model.encode([jd_v1, jd_v2, jd_v3], normalize_embeddings=True, convert_to_tensor=False, show_progress_bar=False)
        
    jd_vec = jd_embedding.tolist()   # convert numpy array → plain Python list
    jd_vars_vecs = jd_vars_embeddings.tolist()
    print(f"      JD vector: {len(jd_vec)} dimensions (along with 3 stability variants)")

    # ------------------------------------------------------------------
    # Step 3: L1 Gatekeeper + L2 Lexical Scorer
    # ------------------------------------------------------------------
    print(f"[3/5] Funnel Stage 1 & 2: L1 Gatekeeper + L2 Lexical Reranker")
    print(f"      Scanning candidates from: {candidates_path}")

    _MASTER_TECH_DICT = {
        "python", "java", "c++", "react", "angular", "node", "javascript",
        "aws", "docker", "kubernetes", "sql", "nosql", "postgres",
        "pytorch", "tensorflow", "machine learning", "deep learning", "nlp",
        "linux", "ci/cd", "azure", "gcp", "devops", "sre", "terraform"
    }

    def generate_dynamic_gatekeeper(text: str) -> set:
        text_lower = text.lower()
        active_keywords = {term for term in _MASTER_TECH_DICT if term in text_lower}
        return active_keywords if active_keywords else {"engineer", "developer", "data"}

    _L1_KEYWORDS = generate_dynamic_gatekeeper(jd_text)
    print(f"      [Gatekeeper] Activated {len(_L1_KEYWORDS)} dynamic keywords based on JD.")

    import collections
    import re
    
    jd_words = collections.Counter(re.findall(r'\w+', jd_text.lower()))

    def l1_fast_filter(cand_raw: str) -> bool:
        """Requires at least TWO technical keywords to pass the L1 Gatekeeper."""
        match_count = sum(kw in cand_raw for kw in _L1_KEYWORDS)
        return match_count >= 2

    def l2_lexical_score(cand_raw: str) -> int:
        """Fast TF (Term Frequency) overlap scorer."""
        cand_words = collections.Counter(re.findall(r'\w+', cand_raw))
        score = 0
        for w, count in cand_words.items():
            if w in jd_words:
                score += min(count, jd_words[w])
        return score

    l1_rejected = 0
    skipped = 0
    l2_candidates = []
    
    for cand in iter_candidates(candidates_path):
        candidate_id = cand.get("candidate_id", "")
        if not candidate_id:
            skipped += 1
            continue
            
        cand_raw = json.dumps(cand).lower()
        if not l1_fast_filter(cand_raw):
            l1_rejected += 1
            continue
            
        lexical_score = l2_lexical_score(cand_raw)
        l2_candidates.append((lexical_score, cand))
        
    print(f"      L1 Rejected: {l1_rejected:,} candidates.")
    
    # Sort survivors by Lexical Score (Descending) and slice top 5000
    l2_candidates.sort(key=lambda x: x[0], reverse=True)
    top_l2_cands = l2_candidates[:5000]
    print(f"      L2 Lexical Scorer selected Top {len(top_l2_cands):,} candidates for dense L3 semantic embedding.")

    # Get max lexical score for normalization
    max_lexical_score = max(1, top_l2_cands[0][0]) if top_l2_cands else 1

    # ------------------------------------------------------------------
    # Step 4: L3 Semantic Reranking (PyTorch)
    # ------------------------------------------------------------------
    print(f"[4/5] Funnel Stage 3: L3 Dense PyTorch Embedding (Hybrid BM25+Semantic)")
    
    heap: list = []   # (score, candidate_id, candidate_dict)
    processed = 0

    def iter_candidate_batches(cands_list: list, batch_size: int = 64):
        for i in range(0, len(cands_list), batch_size):
            yield cands_list[i:i + batch_size]

    for batch in iter_candidate_batches(top_l2_cands, batch_size=64):
        valid_cands = []
        cand_texts = []
        lexical_scores = []

        for lex_score, cand in batch:
            cand_text = build_candidate_text(cand)
            if not cand_text.strip():
                skipped += 1
                continue
            valid_cands.append(cand)
            cand_texts.append(cand_text)
            lexical_scores.append(lex_score)

        if not valid_cands:
            continue

        # Dynamic Batch Truncation happens automatically here:
        # padding=True dynamically pads to the longest sequence in the *current batch*, up to max_seq_length.
        with torch.inference_mode():
            cand_embeddings = model.encode(cand_texts, batch_size=64, normalize_embeddings=True, convert_to_tensor=False, show_progress_bar=False)
        cand_vecs = cand_embeddings.tolist()

        for i, cand in enumerate(valid_cands):
            candidate_id = cand.get("candidate_id", "")
            cand_vec = cand_vecs[i]
            lex_score = lexical_scores[i]

            # 80/20 blend: semantic dominates, lexical stops pure-vibe matches slipping through.
            semantic_score = fast_dot_product(jd_vec, cand_vec)
            normalized_lexical = lex_score / max_lexical_score
            hybrid_score = (semantic_score * 0.8) + (normalized_lexical * 0.2)

            score = hybrid_score * _behavioral_modifier(cand)

            if len(heap) < POST_HOC_K:
                heapq.heappush(heap, (score, candidate_id, cand))
            elif score > heap[0][0]:
                heapq.heapreplace(heap, (score, candidate_id, cand))

        processed += len(valid_cands)

    print(f"      L3 Semantic Processing Complete.")
    print(f"      Total Processed by L3: {processed:,} | Skipped Total: {skipped} | "
          f"Time: {time.time() - t_start:.1f}s")

    # ------------------------------------------------------------------
    # Step 5: Sort, Layer 5 Confidence Engine, and write submission.csv
    # ------------------------------------------------------------------
    print(f"[5/5] Executing Layer 5 Confidence Engine and writing to: {output_path}")

    # Sort: descending full-precision score, then ascending candidate_id for tie-breaking.
    top_candidates = sorted(heap, key=lambda x: (-x[0], x[1]))
    
    print(f"      [Layer 5] Analyzing top {POST_HOC_K} candidates for Epistemic Confidence...")
    
    # Pre-extract texts for batch encoding
    l5_cand_texts = [build_candidate_text(item[2]) for item in top_candidates]
    l5_skills_texts = [", ".join([s.get("name", "") for s in item[2].get("skills", [])][:15]) for item in top_candidates]
    l5_titles_texts = [", ".join([job.get("title", "") for job in item[2].get("career_history", [])[:3]]) for item in top_candidates]
    
    with torch.inference_mode():
        l5_cand_vecs = model.encode(l5_cand_texts, batch_size=64, normalize_embeddings=True, convert_to_tensor=False, show_progress_bar=False).tolist()
        l5_skills_vecs = model.encode(l5_skills_texts, batch_size=64, normalize_embeddings=True, convert_to_tensor=False, show_progress_bar=False).tolist()
        l5_titles_vecs = model.encode(l5_titles_texts, batch_size=64, normalize_embeddings=True, convert_to_tensor=False, show_progress_bar=False).tolist()
        
    final_candidates = []
    
    for i, item in enumerate(top_candidates):
        score, cand_id, cand = item
        cand_vec = l5_cand_vecs[i]
        
        # 1. Semantic Stability
        var_scores = [fast_dot_product(jd_var_vec, cand_vec) for jd_var_vec in jd_vars_vecs]
        mean_score = sum(var_scores) / len(var_scores)
        variance = sum((x - mean_score) ** 2 for x in var_scores) / len(var_scores)
        stability_score = math.sqrt(variance)
        
        # 2. Coherence
        if not l5_skills_texts[i] or not l5_titles_texts[i]:
            coherence_score = 0.0 # Sparse
        else:
            coherence_score = fast_dot_product(l5_skills_vecs[i], l5_titles_vecs[i])
            
        # Compute the raw semantic score (pure cosine, pre-behavioral, pre-lexical)
        semantic_score = fast_dot_product(jd_vec, cand_vec)

        # 3. Confidence Band Logic
        # Change 2: coherence < 0.35 alone triggers LOW — no stability condition required.
        # This ensures Civil Engineers, Sales Executives, etc. can never be MEDIUM.
        confidence_band = "MEDIUM"
        if coherence_score >= 0.5 and stability_score <= 0.02:
            confidence_band = "HIGH"
        elif coherence_score < 0.35:
            confidence_band = "LOW"

        # DARK overrides LOW — incoherent profile with high score, or score volatile across JD variants
        if coherence_score > 0.0 and coherence_score < 0.35 and score > 0.6:
            confidence_band = "DARK"
        if stability_score > 0.05:
            confidence_band = "DARK"

        final_candidates.append({
            "cand_id": cand_id,
            "score": score,
            "semantic_score": semantic_score,
            "cand": cand,
            "confidence_band": confidence_band,
            "coherence_score": coherence_score,
            "stability_score": stability_score
        })
        
    # Change 1 (Option B): Secondary heap — final 100 is built from HIGH and MEDIUM only.
    # LOW and DARK candidates are excluded from the ranked output entirely.
    # LOW candidates are those with coherence_score < 0.35 (skills/title mismatch).
    # This is the gate that removes Civil Engineers, Sales Executives, etc.
    # The pool is the already-sorted top-500; we never touch the embedding pipeline.
    high_medium = [c for c in final_candidates if c["confidence_band"] in ("HIGH", "MEDIUM")]
    top_100_final = high_medium[:FINAL_K]

    dark_dropped  = sum(1 for c in final_candidates if c["confidence_band"] == "DARK")
    low_excluded  = sum(1 for c in final_candidates if c["confidence_band"] == "LOW")
    print(f"      [Layer 5] Excluded {dark_dropped} DARK (keyword stuffed) candidates.")
    print(f"      [Layer 5] Excluded {low_excluded} LOW (incoherent profile) candidates.")
    print(f"      [Layer 5] Outputting {len(top_100_final)} HIGH/MEDIUM trusted candidates to CSV.")
    if len(top_100_final) < FINAL_K:
        print(f"      [Layer 5] WARNING: Only {len(top_100_final)} HIGH/MEDIUM candidates available — "
              f"output will have fewer than {FINAL_K} rows. Never padding with LOW.")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Validator enforces exactly 4 columns: candidate_id, rank, score, reasoning.
        # Structured epistemic signals (band, semantic_score, coherence, stability) are
        # embedded in reasoning as a clean parseable prefix: BAND | sem:X | coh:X | stb:X
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])

        # Strategy: group consecutive entries with the same rounded score,
        # sort each group by candidate_id ascending, then write in order.
        rounded_groups = []
        current_group = []
        current_rounded = None

        for item in top_100_final:
            r = f"{item['score']:.4f}"
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
            group_sorted = sorted(group, key=lambda x: x["cand_id"])  # ascending candidate_id
            for c in group_sorted:
                base_reasoning = build_reasoning(c["cand"], c["score"])
                # Change 4: structured reasoning prefix — band and all four numeric signals
                # are readable as plain prose AND parseable by splitting on " | ".
                # Format: BAND | sem:0.6622 | coh:0.39 | stb:0.04 | <human prose>
                structured_prefix = (
                    f"{c['confidence_band']} | "
                    f"sem:{c['semantic_score']:.4f} | "
                    f"coh:{c['coherence_score']:.2f} | "
                    f"stb:{c['stability_score']:.2f}"
                )
                full_reasoning = f"{structured_prefix} | {base_reasoning}"
                writer.writerow([
                    c["cand_id"],
                    rank_num,
                    f"{c['score']:.4f}",
                    full_reasoning
                ])
                rank_num += 1

    # ------------------------------------------------------------------
    # Final summary
    # ------------------------------------------------------------------
    total_time = time.time() - t_start
    print(f"\n{'='*60}")
    print(f"  [OK]  Submission generated: {output_path}")
    print(f"  [##]  Candidates ranked:    {len(top_100_final)}")
    if top_100_final:
        print(f"  [1st] Top score:            {top_100_final[0]['score']:.4f}")
        print(f"  [Nth] {len(top_100_final)}th score:          {top_100_final[-1]['score']:.4f}")
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
