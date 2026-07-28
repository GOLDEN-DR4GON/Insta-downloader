FROM python:3.10-slim
RUN pip install yt-dlp flask
WORKDIR /app
COPY api /app/api
EXPOSE 10000
CMD ["python", "api/app.py"]
