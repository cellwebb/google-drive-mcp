#!/bin/bash


# Activate virtual environment
if [ -d ".venv" ]; then
  source .venv/bin/activate
else
  echo "Virtual environment not found. Please run setup first."
  exit 1
fi

# Check for environment file
if [ ! -f ".env" ]; then
  echo "Error: .env file not found. Please create one based on .env.example"
  exit 1
fi

# Run the client
python client.py gdrive_server_fixed.py
