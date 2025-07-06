FROM python:3.13-slim

ENV TZ=America/Detroit

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    iputils-ping \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for database
RUN mkdir -p /data

# Set environment variables
ENV DATABASE_PATH=/data/network_monitor.db
ENV PYTHONUNBUFFERED=1

# Expose Streamlit port
EXPOSE 8501

# Default command (can be overridden)
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
