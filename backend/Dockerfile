FROM python:3.11-slim

# ============================================================
# Environment
# ============================================================

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ============================================================
# Working directory
# ============================================================

WORKDIR /app

# ============================================================
# System packages
# ============================================================

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libreoffice \
        tesseract-ocr \
        libgl1 \
        libglib2.0-0 \
        gcc \
        g++ \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# Python dependencies
# ============================================================

COPY backend/requirements.txt /app/backend/requirements.txt

RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/backend/requirements.txt

# ============================================================
# Application
# ============================================================

COPY backend /app/backend

# ============================================================
# Data directories
# ============================================================

RUN mkdir -p /app/data/uploads \
    && mkdir -p /app/data/faiss

# ============================================================
# Port
# ============================================================

EXPOSE 8000

# ============================================================
# Start FastAPI
# ============================================================

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]