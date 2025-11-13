# Use lightweight Python base image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies for TLS and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app files
COPY . .

# Set environment variable
ENV PYTHONUNBUFFERED=1

# Default command to run when the container starts
CMD ["python", "ingest.py"]
