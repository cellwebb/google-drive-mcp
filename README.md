# Google Drive MCP Client

This is a Model Context Protocol (MCP) client for Google Drive that allows you to interact with your Google Drive files using natural language through Claude.

## Setup

> **Note:** This project requires Python 3.10 or newer.

1. Create a virtual environment and install dependencies:

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On macOS/Linux
# On Windows use: .venv\Scripts\activate

# Install required packages
uv pip install mcp anthropic python-dotenv google-auth google-auth-oauthlib google-api-python-client
```

1. Set up Google Drive API credentials:

   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Drive API
   - Create OAuth credentials (OAuth client ID)
   - Download the credentials as JSON and save it as `credentials.json` in this directory

1. Create a `.env` file with your Anthropic API key:

```bash
ANTHROPIC_API_KEY=your_api_key_here
GOOGLE_CREDENTIALS_PATH=path/to/your/service_account_credentials.json  # Optional
```

## Usage

### Using Shell Scripts

Run the client with the provided shell script:

```bash
./run.sh
```

### Using Hatch (Recommended)

Alternatively, if you prefer using Hatch:

```bash
# Install Hatch if you don't have it
pipx install hatch

# Create a Hatch environment and run the application
hatch shell
python client.py gdrive_server.py
```

On first run, the app will open a browser window for you to authenticate with your Google account and grant the necessary permissions.

## Available Tools

This MCP server provides the following tools:

- **list_files**: List files in your Google Drive
- **search_files**: Search for files by name or content
- **get_file_content**: View the content of text files, Google Docs, and Google Sheets
- **get_file_metadata**: View detailed metadata about a file
- **list_folders**: List folders in your Google Drive

## Example Queries

Try asking questions like:

- "Show me my recent documents"
- "Search for files containing 'project plan'"
- "What's in my Google Drive?"
- "Show me the content of file XYZ"
- "List all folders in my drive"
