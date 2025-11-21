FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-backend.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-backend.txt

# Copy backend code
COPY backend/ ./backend/
COPY data/ ./data/
COPY storage/ ./storage/
COPY .env.example .env

# Create necessary directories
RUN mkdir -p logs storage/faiss_index storage/uploaded_files

# Expose port
EXPOSE 7860

# Run backend
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
