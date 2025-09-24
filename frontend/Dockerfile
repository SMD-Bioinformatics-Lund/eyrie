FROM python:3.10-slim

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

CMD ["python", "-m", "eyrie_app.wsgi"]
