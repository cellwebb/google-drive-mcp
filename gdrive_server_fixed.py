import io
import os
import pickle

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from mcp.server.fastmcp import Context, FastMCP

# If modifying these scopes, delete the token.pickle file
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Initialize FastMCP server
mcp = FastMCP("gdrive-server")
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
                        "No valid credentials found. Please provide credentials.json or set GOOGLE_APPLICATION_CREDENTIALS environment variable."
                    )

        # Save the credentials for future runs
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    drive_service = build("drive", "v3", credentials=creds)
    return drive_service


@mcp.tool()
async def list_files(max_results: int = 10, query: str = "") -> str:
    """List files in Google Drive

    Args:
        max_results: Maximum number of files to return (default: 10)
        query: Optional query to filter files
    """
    service = get_drive_service()

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
        return "No files found."

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
    return f"Files found ({len(files)}):\n\n{file_list}"


@mcp.tool()
async def search_files(query: str, max_results: int = 10) -> str:
    """Search for files in Google Drive by name or content

    Args:
        query: Search query text
        max_results: Maximum number of files to return (default: 10)
    """
    service = get_drive_service()

    # Format the query for Google Drive API
    search_query = f"name contains '{query}' or fullText contains '{query}'"

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
        return f"No files found matching '{query}'."

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
    return f"Search results for '{query}' ({len(files)}):\n\n{file_list}"


@mcp.tool()
async def get_file_content(file_id: str) -> str:
    """Get the content of a text file from Google Drive

    Args:
        file_id: Google Drive file ID
    """
    service = get_drive_service()

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
            return f"Content of '{file['name']}':\n\n{content}"

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
            return f"Content of Google Doc '{file['name']}':\n\n{content}"

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
            return f"Content of Google Sheet '{file['name']}' (CSV format):\n\n{content}"

        else:
            return f"Cannot display content for file type: {file['mimeType']}. This file type is not supported for text preview."

    except Exception as e:
        return f"Error retrieving file: {str(e)}"


@mcp.tool()
async def get_file_metadata(file_id: str) -> str:
    """Get metadata for a specific file

    Args:
        file_id: Google Drive file ID
    """
    service = get_drive_service()

    try:
        file = (
            service.files()
            .get(
                fileId=file_id,
                fields="id,name,mimeType,createdTime,modifiedTime,size,description,webViewLink,owners,parents",
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
            owners = ", ".join([owner.get("displayName", "Unknown") for owner in file["owners"]])
            metadata.append(f"Owners: {owners}")

        return "\n".join(metadata)

    except Exception as e:
        return f"Error retrieving file metadata: {str(e)}"


@mcp.tool()
async def list_folders(parent_id: str = "root", max_results: int = 10) -> str:
    """List folders in Google Drive

    Args:
        parent_id: ID of the parent folder (default: "root")
        max_results: Maximum number of folders to return (default: 10)
    """
    service = get_drive_service()

    # Query to find only folders
    query = f"'{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"

    results = (
        service.files()
        .list(q=query, pageSize=max_results, fields="files(id, name, createdTime, modifiedTime)")
        .execute()
    )

    folders = results.get("files", [])
    if not folders:
        parent_name = (
            "Root"
            if parent_id == "root"
            else service.files().get(fileId=parent_id, fields="name").execute()["name"]
        )
        return f"No folders found in '{parent_name}'."

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
    return f"Folders in '{parent_name}' ({len(folders)}):\n\n{folder_list}"
