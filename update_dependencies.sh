#!/bin/bash


# Activate virtual environment
source .venv/bin/activate

# Uninstall any existing MCP package
pip uninstall -y mcp

# Install the MCP package with all extras
pip install "mcp[cli,server]"

# Install other requirements
pip install anthropic python-dotenv google-api-python-client google-auth-httplib2 google-auth-oauthlib

echo "Dependencies updated successfully!"
