FROM python:3.11-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install fastapi uvicorn yt-dlp

# Copy app code
COPY . .

# Expose the port Render expects
EXPOSE 10000

# Run FastAPI
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "10000"]

