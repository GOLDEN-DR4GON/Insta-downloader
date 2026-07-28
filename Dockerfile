FROM python:3.9-slim

# Install yt-dlp
RUN pip install yt-dlp flask

# Set working directory
WORKDIR /app

# Copy application
COPY api /app/api

# Expose port
EXPOSE 10000

# Start the app
CMD ["python", "api/app.py"]
