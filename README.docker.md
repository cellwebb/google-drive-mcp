# Google Drive MCP Client - Docker Setup

This document explains how to run the Google Drive MCP client using Docker and Docker Compose.

## Prerequisites

- Docker and Docker Compose installed on your system
- Google Drive API credentials (service account or OAuth)
- Anthropic API key (for Claude)

## Setup Instructions

1. **Configure environment variables**

   Copy the example environment file and add your Anthropic API key:

   ```bash
   cp .env.example .env
   ```

   Then edit the `.env` file to add your Anthropic API key:

   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

2. **Prepare Google credentials**

   Place your Google Drive credentials in the project root directory as `credentials.json`.

3. **Make the start script executable**

   ```bash
   chmod +x start-docker.sh
   ```

4. **Start the Docker container**

   ```bash
   ./start-docker.sh
   ```

   Or directly with:

   ```bash
   docker-compose up --build
   ```

   To run in the background (detached mode):

   ```bash
   docker-compose up --build -d
   ```

## Using the Client

Once the container is running, you can interact with the Google Drive MCP client through the interactive console. Type your queries about Google Drive, and the client will execute them using the appropriate tools.

Example queries:
- "List my recent files"
- "Search for documents containing 'project plan'"
- "Get the content of a specific file"

To exit the client, type `quit` or `exit`.

## Stopping the Container

If you ran the container in the foreground, press Ctrl+C to stop it.

If you ran it in detached mode, use:

```bash
docker-compose down
```

## Troubleshooting

- **Authentication Issues**: Ensure your credentials.json file is valid and has the correct permissions for Google Drive API.
- **Container Not Starting**: Check Docker logs with `docker-compose logs`.
- **API Key Issues**: Verify your Anthropic API key is correctly set in the .env file.
