# Build Stage for Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Runtime Stage
FROM python:3.10-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy Backend Code
COPY . .

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist /app/frontend_dist

# Set permissions for Hugging Face Spaces (user 1000)
RUN chown -R 1000:1000 /app
USER 1000

# Environment variables
ENV FLASK_ENV=production
ENV PORT=7860
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["gunicorn", "-b", "0.0.0.0:7860", "app:app"]
