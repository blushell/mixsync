# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Update yt-dlp to latest version (fixes YouTube issues)
RUN pip install --upgrade yt-dlp

# Copy application code
COPY app/ ./app/
COPY run_continuous.py .
COPY run_quiet.py .
COPY env_example.txt .

# Create downloads directory
RUN mkdir -p /app/downloads

# Create volume for downloads and config
VOLUME ["/app/downloads", "/app/config"]

# Environment variables
ENV PYTHONPATH=/app
ENV DOWNLOAD_PATH=/app/downloads

# Expose port for FastAPI web UI
EXPOSE 8000

# Health check using FastAPI health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - run full FastAPI app with auto-sync + web UI
CMD ["python", "-m", "app.main"] 
