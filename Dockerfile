FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port for Hugging Face Spaces (7860 is standard)
EXPOSE 7860

# Set environment variables
ENV FLASK_APP=web_dashboard.py
ENV PYTHONUNBUFFERED=1

# Run the web dashboard
CMD ["python", "web_dashboard.py"]
