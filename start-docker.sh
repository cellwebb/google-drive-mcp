#!/bin/bash

# Check for .env file
if [ ! -f ".env" ]; then
  echo "Error: .env file not found!"
  echo "Please create a .env file based on .env.example with your ANTHROPIC_API_KEY"
  exit 1
fi

# Check for credentials.json
if [ ! -f "credentials.json" ]; then
  echo "Warning: credentials.json not found."
  echo "You'll need to provide Google Drive credentials to use the application."
  echo "Continuing anyway..."
fi

# Build and start the Docker container
echo "Starting Google Drive MCP Client..."
docker-compose up --build

# To run in the background, uncomment the following line:
# docker-compose up --build -d
