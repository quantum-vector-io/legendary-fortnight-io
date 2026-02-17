FROM python:3.11-slim

LABEL description="Rate Card Converter - document parsing service with LLM semantic mapping"
LABEL version="0.1.0"

WORKDIR /app

# Install system dependencies required by pdfplumber (uses pdfminer.six which
# requires gcc and libffi for cryptography and charset-normalizer compilation).
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project manifest first to leverage Docker layer caching.
# Dependencies are re-installed only when pyproject.toml changes.
COPY pyproject.toml .

# Install production dependencies (no dev/test extras).
RUN pip install --no-cache-dir -e .

# Copy application source code.
COPY src/ ./src/
COPY samples/ ./samples/

# Runtime configuration.
ENV ENVIRONMENT=local
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create the upload directory. The volume mount in docker-compose will override this.
RUN mkdir -p /app/data/uploads

EXPOSE 8000

# Uvicorn serves the FastAPI application. The --reload flag is appropriate for
# local development but should be removed for production deployments.
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "info"]
