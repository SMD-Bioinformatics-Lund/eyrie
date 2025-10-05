FROM python:3.10-slim

LABEL maintainer="eyrie-team"
LABEL description="Eyrie Popup - Sample processing tool for Eyrie sample management system"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the application code and configuration
COPY popup/ ./popup/
COPY pyproject.toml .
COPY README.md .

# Install the package
RUN pip install --no-cache-dir .

# Create a non-root user
RUN useradd -m -u 1000 eyrie && chown -R eyrie:eyrie /app
USER eyrie

# Set the entrypoint
ENTRYPOINT ["eyrie-popup"]
CMD ["--help"]
