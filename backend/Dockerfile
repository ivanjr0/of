FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY pyproject.toml ./

# Install dependencies
RUN pip install --no-cache-dir -e .

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --output-document=/dev/null http://localhost:8000/api/health || exit 1

# Create a startup script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Running migrations..."\n\
python manage.py migrate --noinput\n\
echo "Starting server..."\n\
python manage.py runserver 0.0.0.0:8000' > /app/start.sh

# Create a worker startup script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Setting up Django for worker..."\n\
export DJANGO_SETTINGS_MODULE=settings\n\
echo "Starting RQ worker..."\n\
exec python worker.py' > /app/start_worker.sh

RUN chmod +x /app/start.sh /app/start_worker.sh

# Start the application
CMD ["/app/start.sh"] 