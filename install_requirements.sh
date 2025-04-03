#!/bin/bash


# Activate virtual environment
if [ -d ".venv" ]; then
  source .venv/bin/activate
else
  echo "Creating virtual environment..."
  python -m venv .venv
  source .venv/bin/activate
fi

# Uninstall existing packages to avoid conflicts
pip uninstall -y mcp

# Install from requirements.txt
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "Dependencies installed successfully!"
echo "You can now run the application with: ./run.sh"
