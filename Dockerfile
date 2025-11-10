FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    ninja-build \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Build and install liboqs from source (latest stable)
RUN git clone --depth 1 https://github.com/open-quantum-safe/liboqs.git /tmp/liboqs && \
    cd /tmp/liboqs && \
    mkdir build && cd build && \
    cmake -GNinja -DCMAKE_INSTALL_PREFIX=/usr/local -DBUILD_SHARED_LIBS=ON .. && \
    ninja && \
    ninja install && \
    ldconfig && \
    cd / && rm -rf /tmp/liboqs

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 8080

# Set environment variables
ENV FLASK_APP=web_dashboard.py
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONWARNINGS="ignore::UserWarning"

# Run the web dashboard
CMD ["python", "web_dashboard.py"]
