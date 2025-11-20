# Use more recent Python version with better ARM64 support
FROM python:3.11.3-slim

# Add a cache-busting layer
ARG CACHE_BUST=1

# Install system dependencies - separate steps for better ARM64 compatibility
RUN apt-get update -qq && apt-get upgrade -y
RUN apt-get install -y --no-install-recommends \
        gcc \
        curl
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY pyproject.toml .
RUN python -m pip install --upgrade pip --no-cache-dir

# Copy application code
COPY eyrie_api/ ./eyrie_api/

# Install package with production dependencies
RUN python -m pip install --no-cache-dir .[production]

# Create non-root user
RUN groupadd --gid 1000 worker && \
    useradd -g worker --uid 1000 --shell /usr/sbin/nologin --create-home worker

# Set ownership of application directory and create data directory
RUN chown -R worker:worker /app && \
    mkdir -p /app/data && \
    chown -R worker:worker /app/data

# Switch to non-root user
USER worker

EXPOSE 5000

# Add healthcheck - temporarily disabled for debugging
# HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
#     CMD curl -f http://localhost:5000/api/system/health || exit 1

# Production command using uvicorn with single worker and enhanced logging
CMD ["uvicorn", "eyrie_api.main:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "1", "--access-log", "--log-level", "info"]
