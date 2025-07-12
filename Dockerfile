FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y restic rclone && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set working directory
WORKDIR /app

# Copy application files
COPY . .

# Expose API port
EXPOSE 8675

# Run the app
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8675"]
