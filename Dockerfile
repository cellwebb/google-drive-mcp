FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create configuration directory for Google credentials
RUN mkdir -p /root/.config/gcloud

# Expose port 8000 in case we need server functionality
EXPOSE 8000

# Set container to run interactively
ENTRYPOINT ["/bin/bash", "-c"]

# Default command - but this will be overridden by docker-compose
CMD ["python client.py gdrive_server_fixed.py"]
