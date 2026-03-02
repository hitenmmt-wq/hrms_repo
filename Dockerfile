# Use the official Python image
FROM python:3.11-slim-bookworm

# Prevent Python from writing pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Create user
RUN useradd -m appuser

# System dependencies
ENV DEBIAN_FRONTEND=noninteractive

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
    libcairo2-dev \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    tzdata \
    shared-mime-info \
    build-essential \
    pkg-config \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Set container timezone
ENV TZ=Asia/Kolkata
# RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
#     && echo $TZ > /etc/timezone

# Copy project code
COPY . .

# Copy and set entrypoint permissions
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Give permissions
RUN chown -R appuser:appuser /app

# Switch user
USER appuser

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
