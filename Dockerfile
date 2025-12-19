# Use the official Python image from the Docker Hub
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
# RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install netcat for entrypoint
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code into the container
COPY . .

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose the port that the Django app runs on
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Command to run the application
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "hrms.asgi:application"]
