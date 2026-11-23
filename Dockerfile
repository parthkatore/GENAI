# ============================================================
# ArduinoMate — Multi-stage Docker image
# Stage 1: builder  — install Python deps into /install
# Stage 2: runtime  — slim image that copies only /install
# ============================================================

# ---- Stage 1: builder ----
FROM python:3.11-slim AS builder

WORKDIR /install

# System build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (layer-cached unless requirements change)
COPY requirements.txt .

RUN pip install --upgrade pip --root-user-action=ignore \
 && pip install --prefix=/install --no-cache-dir --root-user-action=ignore \
      -r requirements.txt


# ---- Stage 2: runtime ----
FROM python:3.11-slim AS runtime

# Non-root user for security
RUN groupadd -r arduinomate && useradd -r -g arduinomate arduinomate

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# System runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy application source
COPY . .

# Application runtime settings
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create writable dirs and set ownership
RUN mkdir -p /app/data/chroma_db /app/data \
 && chown -R arduinomate:arduinomate /app

USER arduinomate

# Expose FastAPI (8000) and Streamlit (8501)
EXPOSE 8000 8501

# Default: start the FastAPI backend.
# docker-compose overrides this per-service.
# Render injects PORT; fall back to 8000 for local runs.
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]