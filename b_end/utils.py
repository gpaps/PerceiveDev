import os
from fastapi import HTTPException
import requests
from dotenv import load_dotenv
from webdav_setup_config import client

load_dotenv(".env")

NEXTCLOUD_URL = os.getenv("NEXTCLOUD_URL")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Nextcloud Config
print("NEXTCLOUD_URL:", NEXTCLOUD_URL)
print("USERNAME:", USERNAME)


# Careful, don't expose sensitive passwords in logs.

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