# Use the official Python image
FROM python:3.11-slim

# Prevent Python from writing pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# -----------------------------
# System dependencies (IMPORTANT)
# -----------------------------
# These are REQUIRED for WeasyPrint (PDF generation) and pycairo (for svglib)
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libcairo2-dev \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Python dependencies
# -----------------------------
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# -----------------------------
# Copy project code
# -----------------------------
COPY . .

# -----------------------------
# Entrypoint
# -----------------------------
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]

# Daphne for ASGI (Channels/WebSockets)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "hrms.asgi:application"]
