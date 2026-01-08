# Use the official Python image
FROM python:3.11-slim

# Prevent Python from writing pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    wkhtmltopdf \
    fontconfig \
    xfonts-base \
    xfonts-75dpi \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    build-essential \
    pkg-config \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Entrypoint
RUN echo '#!/bin/bash\nset -e\n\
echo "Waiting for database..."\n\
while ! nc -z host.docker.internal 5432; do sleep 2; done\n\
echo "Waiting for Redis..."\n\
while ! nc -z redis 6379; do sleep 2; done\n\
exec "$@"' > /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
