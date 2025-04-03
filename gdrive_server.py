import io
import os
import pickle

import mcp.server.types as types
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from mcp.server import Server

# If modifying these scopes, delete the token.pickle file
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

app = Server("gdrive-server")
drive_service = None


def get_drive_service():
    """Get authenticated Google Drive service"""
    global drive_service
    if drive_service is not None:
        return drive_service

    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Check if we have credentials.json from Google Cloud Console
            if os.path.exists("credentials.json"):
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
            else:
                # Fall back to service account if available
                creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
                if creds_path and os.path.exists(creds_path):
                    creds = service_account.Credentials.from_service_account_file(
                        creds_path, scopes=SCOPES
                    )
                else:
                    raise Exception(
                        "No valid credentials found. Please provide credentials.json "
                        "or set GOOGLE_APPLICATION_CREDENTIALS environment variable."
                    )

        # Save the credentials for future runs
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    drive_service = build("drive", "v3", credentials=creds)
    return drive_service


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_files",
            description="List files in Google Drive",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {"type": "number", "default": 10},
                    "query": {"type": "string", "default": ""},
                },
            },
        ),
        types.Tool(
            name="search_files",
            description="Search for files in Google Drive by name or content",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "number", "default": 10},
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="get_file_content",
            description="Get the content of a text file from Google Drive",
            inputSchema={
                "type": "object",
                "properties": {"file_id": {"type": "string"}},
                "required": ["file_id"],
            },
        ),
        types.Tool(
            name="get_file_metadata",
            description="Get metadata for a specific file",
            inputSchema={
                "type": "object",
                "properties": {"file_id": {"type": "string"}},
                "required": ["file_id"],
            },
        ),
        types.Tool(
            name="list_folders",
            description="List folders in Google Drive",
            inputSchema={
                "type": "object",
                "properties": {
                    "parent_id": {"type": "string", "default": "root"},
                    "max_results": {"type": "number", "default": 10},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent]:
    service = get_drive_service()

    if name == "list_files":
        max_results = int(arguments.get("max_results", 10))
        query = arguments.get("query", "")

        results = (
            service.files()
            .list(
                q=query,
                pageSize=max_results,
                fields="files(id, name, mimeType, createdTime, modifiedTime, size, parents)",
            )
            .execute()
        )

        files = results.get("files", [])
        if not files:
            return [types.TextContent(type="text", text="No files found.")]

        file_list_items = []
        for file in files:
            file_info = f"• {file['name']} (ID: {file['id']})\n"
            file_info += f"  - Type: {file['mimeType']}\n"
            if "createdTime" in file:
                file_info += f"  - Created: {file['createdTime']}\n"
            if "modifiedTime" in file:
                file_info += f"  - Modified: {file['modifiedTime']}\n"
            if "size" in file:
                file_info += f"  - Size: {int(file['size']) // 1024} KB\n"
            file_list_items.append(file_info)

        file_list = "\n".join(file_list_items)
        return [types.TextContent(type="text", text=f"Files found ({len(files)}):\n\n{file_list}")]

    elif name == "search_files":
        query_text = arguments["query"]
        max_results = int(arguments.get("max_results", 10))

        # Format the query for Google Drive API
        search_query = f"name contains '{query_text}' or fullText contains '{query_text}'"

        results = (
            service.files()
            .list(
                q=search_query,
                pageSize=max_results,
                fields="files(id, name, mimeType, createdTime, modifiedTime, size)",
            )
            .execute()
        )

        files = results.get("files", [])
        if not files:
            return [types.TextContent(type="text", text=f"No files found matching '{query_text}'.")]

        file_list_items = []
        for file in files:
            file_info = f"• {file['name']} (ID: {file['id']})\n"
            file_info += f"  - Type: {file['mimeType']}\n"
            if "createdTime" in file:
                file_info += f"  - Created: {file['createdTime']}\n"
            if "modifiedTime" in file:
                file_info += f"  - Modified: {file['modifiedTime']}\n"
            file_list_items.append(file_info)

        file_list = "\n".join(file_list_items)
        return [
            types.TextContent(
                type="text",
                text=f"Search results for '{query_text}' ({len(files)}):\n\n{file_list}",
            )
        ]

    elif name == "get_file_content":
        file_id = arguments["file_id"]

        try:
            # Get file metadata first to check mime type
            file = service.files().get(fileId=file_id, fields="name,mimeType").execute()

            # For text files
            if (
                file["mimeType"] == "text/plain"
                or file["mimeType"].startswith("text/")
                or file["mimeType"] == "application/json"
            ):
                request = service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)

                done = False
                while not done:
                    _, done = downloader.next_chunk()

                content = fh.getvalue().decode("utf-8")
                return [
                    types.TextContent(
                        type="text", text=f"Content of '{file['name']}':\n\n{content}"
                    )
                ]

            # For Google Docs
            elif file["mimeType"] == "application/vnd.google-apps.document":
                # Export as plain text
                request = service.files().export_media(fileId=file_id, mimeType="text/plain")
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)

                done = False
                while not done:
                    _, done = downloader.next_chunk()

                content = fh.getvalue().decode("utf-8")
                return [
                    types.TextContent(
                        type="text", text=f"Content of Google Doc '{file['name']}':\n\n{content}"
                    )
                ]

            # For Google Sheets
            elif file["mimeType"] == "application/vnd.google-apps.spreadsheet":
                # Export as CSV
                request = service.files().export_media(fileId=file_id, mimeType="text/csv")
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)

                done = False
                while not done:
                    _, done = downloader.next_chunk()

                content = fh.getvalue().decode("utf-8")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Content of Google Sheet '{file['name']}' (CSV format):\n\n{content}",
                    )
                ]

            else:
                return [
                    types.TextContent(
                        type="text",
                        text=(
                            f"Cannot display content for file type: {file['mimeType']}. "
                            "This file type is not supported for text preview."
                        ),
                    )
                ]

        except Exception as e:
            return [types.TextContent(type="text", text=f"Error retrieving file: {str(e)}")]

    elif name == "get_file_metadata":
        file_id = arguments["file_id"]

        try:
            file = (
                service.files()
                .get(
                    fileId=file_id,
                    fields="id,name,mimeType,createdTime,modifiedTime,size,description,webViewLink,owners,parents",  # noqa: E501
                )
                .execute()
            )

            metadata = [f"File: {file['name']}"]
            metadata.append(f"ID: {file['id']}")
            metadata.append(f"Type: {file['mimeType']}")

            if "createdTime" in file:
                metadata.append(f"Created: {file['createdTime']}")
            if "modifiedTime" in file:
                metadata.append(f"Modified: {file['modifiedTime']}")
            if "size" in file:
                size_kb = int(file["size"]) // 1024 if "size" in file else "N/A"
                metadata.append(f"Size: {size_kb} KB")
            if "description" in file and file["description"]:
                metadata.append(f"Description: {file['description']}")
            if "webViewLink" in file:
                metadata.append(f"Web View: {file['webViewLink']}")
            if "owners" in file:
                owners = ", ".join(
                    [owner.get("displayName", "Unknown") for owner in file["owners"]]
                )
                metadata.append(f"Owners: {owners}")

            return [types.TextContent(type="text", text="\n".join(metadata))]

        except Exception as e:
            return [
                types.TextContent(type="text", text=f"Error retrieving file metadata: {str(e)}")
            ]

    elif name == "list_folders":
        parent_id = arguments.get("parent_id", "root")
        max_results = int(arguments.get("max_results", 10))

        # Query to find only folders
        query = f"'{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"

        results = (
            service.files()
            .list(
                q=query, pageSize=max_results, fields="files(id, name, createdTime, modifiedTime)"
            )
            .execute()
        )

        folders = results.get("files", [])
        if not folders:
            parent_name = (
                "Root"
                if parent_id == "root"
                else service.files().get(fileId=parent_id, fields="name").execute()["name"]
            )
            return [types.TextContent(type="text", text=f"No folders found in '{parent_name}'.")]

        folder_list_items = []
        for folder in folders:
            folder_info = f"• {folder['name']} (ID: {folder['id']})\n"
            if "createdTime" in folder:
                folder_info += f"  - Created: {folder['createdTime']}\n"
            if "modifiedTime" in folder:
                folder_info += f"  - Modified: {folder['modifiedTime']}\n"
            folder_list_items.append(folder_info)

        parent_name = (
            "Root"
            if parent_id == "root"
            else service.files().get(fileId=parent_id, fields="name").execute()["name"]
        )
        folder_list = "\n".join(folder_list_items)
        return [
            types.TextContent(
                type="text", text=f"Folders in '{parent_name}' ({len(folders)}):\n\n{folder_list}"
            )
        ]

    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


if __name__ == "__main__":
    app.run()
