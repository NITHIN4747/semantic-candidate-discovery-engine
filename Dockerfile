# Stage 1: Dependency installation layer
# Using python:3.11-slim keeps the image surface area minimal and reduces CVE exposure.
FROM python:3.11-slim AS builder

WORKDIR /build

# Install OS-level build tools required by some Python packages at compile time
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install application dependencies into /install for clean COPY into final stage
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt fastapi uvicorn pydantic

# Pre-download the embedding model into the build cache.
# This ensures zero network calls when the container runs in the offline sandbox.
RUN TRANSFORMERS_CACHE=/install/model_cache \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', cache_folder='/install/model_cache')"


# Stage 2: Minimal runtime image
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages and cached model from builder
COPY --from=builder /install /usr/local
COPY --from=builder /install/model_cache /app/model_cache

# Copy application code
COPY . .

# Create non-root user and transfer ownership — Least Privilege enforcement
RUN useradd -m -r appuser && chown -R appuser:appuser /app
USER appuser

# Port 8443 aligns with the SG-EC2-Compute Security Group rule:
# SG-NLB accepts public HTTPS (443) and forwards to EC2 on 8443.
EXPOSE 8443

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8443"]
