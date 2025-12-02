FROM python:3.10-slim

LABEL authors="Ryan Kennedy <ryan.kennedy@skane.se>" \
      maintainers="Ryan Kennedy <ryan.kennedy@skane.se>" \
      description="Docker image for eyrie-popup"

# Set working directory
WORKDIR /usr/src/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the application code and configuration
COPY . .

# Install the package
RUN pip install --no-cache-dir .

# Set the entrypoint
ENTRYPOINT ["popup"]
CMD ["--help"]
