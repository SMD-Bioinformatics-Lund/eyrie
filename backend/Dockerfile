# Use more recent Python version with better ARM64 support
FROM python:3.12.0-slim

# Add a cache-busting layer
ARG CACHE_BUST=1

WORKDIR /app

# Install system dependencies - separate steps for better ARM64 compatibility
RUN apt-get update -qq && apt-get upgrade -y
RUN apt-get install -y --no-install-recommends \
        gcc \
        curl
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy and install Python dependencies
COPY pyproject.toml .
RUN python -m pip install --upgrade pip --no-cache-dir

# Copy application code
COPY eyrie_api/ ./eyrie_api/

# Install package with production dependencies
RUN python -m pip install --no-cache-dir .[production]

EXPOSE 5000

# Add healthcheck - temporarily disabled for debugging
# HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
#     CMD curl -f http://localhost:5000/health || exit 1

# Production command using uvicorn with single worker and enhanced logging
CMD ["uvicorn", "eyrie_api.main:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "1", "--access-log", "--log-level", "info"]
