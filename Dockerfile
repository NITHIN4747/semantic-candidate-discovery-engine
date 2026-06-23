# Use a lightweight, CPU-optimized Python 3.11 base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (required for some basic compile tasks if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies (FastAPI, Uvicorn, Sentence-Transformers)
RUN pip install --no-cache-dir -r requirements.txt fastapi uvicorn pydantic

# 🔥 THE OFFLINE TRICK: Pre-download the embedding model into the image cache
# This ensures zero network calls are made when the container boots in the sandbox.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy the rest of the application code
COPY . .

# Expose Port 8443 to comply strictly with the SG-EC2-Compute Security Group matrix
EXPOSE 8443

# Start the FastAPI server on port 8443
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8443"]
