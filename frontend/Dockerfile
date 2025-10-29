FROM python:3.12.0-slim

WORKDIR /app

# Update pip and install Python dependencies
COPY pyproject.toml .
RUN python -m pip install --upgrade pip

# Copy application
COPY eyrie_app/ ./eyrie_app/

# Install package with production dependencies
RUN python -m pip install --no-cache-dir .[production]

# Copy frontend static files
COPY . /app/frontend

# Create data directory
RUN mkdir -p /app/data

EXPOSE 5000

# Debug: Show Gunicorn workers and force sync worker
RUN echo "Available Gunicorn workers:" && python -c "import gunicorn.workers; print([w for w in dir(gunicorn.workers) if 'worker' in w.lower()])" || echo "Could not list workers"

# Force sync worker explicitly with verbose logging
CMD ["gunicorn", "--workers", "1", "--worker-class", "gunicorn.workers.sync.SyncWorker", "--bind", "0.0.0.0:5000", "--log-level", "debug", "--access-logfile", "-", "--error-logfile", "-", "eyrie_app.wsgi:app"]
