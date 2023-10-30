import os
from fastapi import HTTPException
import requests
from dotenv import load_dotenv
from webdav_setup_config import client

load_dotenv(".env")

# Nextcloud Config
NEXTCLOUD_URL = os.getenv("NEXTCLOUD_URL")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")


def get_file_from_nextcloud(path: str) -> bytes:
    try:
        response = requests.get(
            f"{NEXTCLOUD_URL}/remote.php/dav/files/{USERNAME}/{path}",
            auth=(USERNAME, PASSWORD),
        )

        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))


UPLOAD_FOLDER = "Photos"


def upload_file_to_nextcloud(filename: str, content: bytes) -> tuple:
    try:
        remote_path = f"{UPLOAD_FOLDER}/{filename}"

        # Ensure the directory exists on Nextcloud
        if not client.check(remote_path=UPLOAD_FOLDER):
            client.mkdir(remote_path=UPLOAD_FOLDER)

        response = requests.put(
            f"{NEXTCLOUD_URL}/remote.php/dav/files/{USERNAME}/{remote_path}",
            auth=(USERNAME, PASSWORD),
            data=content
        )

        response.raise_for_status()
        return "success", f"File uploaded to {remote_path}"
    except requests.RequestException as e:
        return "error", str(e)


import xml.etree.ElementTree as ET


def list_files_recursive(remote_path="/"):
    """
    Recursively list files and directories in Nextcloud starting from remote_path.
    """
    all_files = []

    # Use WebDAV PROPFIND request to fetch directory and file listings
    headers = {
        "Depth": "1"
    }

    response = requests.request("PROPFIND", f"{NEXTCLOUD_URL}/remote.php/dav/files/{USERNAME}{remote_path}",
                                headers=headers, auth=(USERNAME, PASSWORD))

    if response.status_code != 207:  # 207 Multi-Status is a standard success code for PROPFIND
        raise HTTPException(status_code=500,
                            detail=f"Failed to list directory {remote_path}. Status code: {response.status_code}")
    # Parse the XML response
    tree = ET.ElementTree(ET.fromstring(response.content))

    # XML namespaces used in the response
    namespaces = {
        'd': 'DAV:',
        'oc': 'http://owncloud.org/ns'
    }

    # Extract the href value for each file/directory returned in the response
    for href in tree.findall(".//d:href", namespaces=namespaces):
        path = href.text.split(f"/remote.php/dav/files/{USERNAME}", 1)[-1]

        if path != remote_path:
            if path.endswith("/"):
                # It's a directory
                all_files.extend(list_files_recursive(path))
            else:
                # It's a file
                all_files.append(path)

    return all_files
