FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY pyproject.toml .
RUN python -m pip install --upgrade pip

# Copy application code
COPY eyrie_api/ ./eyrie_api/

# Install package with production dependencies
RUN python -m pip install --no-cache-dir .[production]

EXPOSE 5000

CMD ["uvicorn", "eyrie_api.main:app", "--host", "0.0.0.0", "--port", "5000"]
