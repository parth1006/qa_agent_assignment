FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements-backend.txt .

# Upgrade pip and install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-backend.txt

# Copy application code
COPY backend/ ./backend/
COPY data/ ./data/
COPY storage/ ./storage/

# Copy and rename .env.example to .env if it doesn't exist
COPY .env.example .env

# Create necessary directories
RUN mkdir -p logs storage/faiss_index storage/uploaded_files

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GROQ_API_KEY=${GROQ_API_KEY}

# Expose port (HuggingFace uses 7860)
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:7860/health')"

# Run backend
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
