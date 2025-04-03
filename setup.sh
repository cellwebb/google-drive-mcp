#!/bin/bash

# Create and activate virtual environment
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  uv venv
  echo "Virtual environment created."
else
  echo "Virtual environment already exists."
fi

# Activate virtual environment
source .venv/bin/activate

# Install required packages
echo "Installing required packages..."
uv pip install mcp anthropic python-dotenv google-api-python-client google-auth-httplib2 google-auth-oauthlib --python ">=3.10"

# If installation fails, try with --frozen flag
if [ $? -ne 0 ]; then
  echo "Trying installation with --frozen flag..."
  uv pip install mcp anthropic python-dotenv google-api-python-client google-auth-httplib2 google-auth-oauthlib
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
  echo "Creating .env file template..."
  cp .env.example .env
  echo "Please edit the .env file to add your API keys."
fi

# Make run script executable
chmod +x run.sh

echo "Setup complete! You can now run the application with ./run.sh"
echo "Make sure to edit the .env file with your Anthropic API key."
