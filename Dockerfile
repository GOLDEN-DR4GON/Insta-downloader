FROM python:3.9-slim

# Install yt-dlp with full path
RUN apt-get update && \
    apt-get install -y --no-install-recommends && \
    pip install --no-cache-dir yt-dlp flask && \
    which yt-dlp || echo "yt-dlp not in PATH"

# Set working directory
WORKDIR /app

# Copy application
COPY api /app/api

# Expose port
EXPOSE 10000

# Start the app
CMD ["python", "api/app.py"]
