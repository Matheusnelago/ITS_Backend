# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .\n\n# Install Python dependencies\nRUN pip install --no-cache-dir -r requirements.txt

# Copy the backend directory
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBUG=False
ENV DATABASE_URL="postgresql://postgres:nHxOKjreYAEHzhgwJimFhQiIZiclJJtg@postgres.railway.internal:5432/railway"

# Expose port
EXPOSE 8000

# Run migrations and start gunicorn
CMD python manage.py migrate && gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 2

