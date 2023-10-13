# Standard Libraries
from concurrent import futures
import logging
import os
import threading

# Third-party Libraries
from webdav_setup0 import client
from fastapi import FastAPI, Depends, UploadFile, HTTPException, File
from fastapi.responses import StreamingResponse, FileResponse
import cv2
import grpc
import numpy as np
from io import BytesIO
import skimage.io
import requests
import mimetypes
import io
from dotenv import load_dotenv

# own modules
from nextcloud_pb2_grpc import add_NextcloudServiceServicer_to_server, NextcloudServiceServicer
from nextcloud_pb2 import FileResponse as NextcloudFileResponse

load_dotenv()
app = FastAPI()

# Nextcloud Config
NEXTCLOUD_URL = os.getenv("NEXTCLOUD_URL")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

def get_file_from_nextcloud(path: str) -> bytes:  # helper function
    try:
        response = requests.get(
            f"{NEXTCLOUD_URL}/remote.php/dav/files/{USERNAME}/{path}",
            auth=(USERNAME, PASSWORD),
        )
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/file/{path:path}")  # also downloads the file if there is no function_handle
def read_file(path: str):
    try:
        content = get_file_from_nextcloud(path)
        mime_type, encoding = mimetypes.guess_type(path)
        if not mime_type:
            mime_type = "application/octet-stream"
        response = StreamingResponse(BytesIO(content), media_type=mime_type)
        response.headers["Content-Disposition"] = f"attachment; filename={path.split('/')[-1]}"
        return response
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


UPLOAD_FOLDER = "Photos"
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Read image contents
        contents = await file.read()
        image = skimage.io.imread(io.BytesIO(contents))

        # Process the image
        edges = cv2.Canny(image, 100, 200)

        # Convert the processed image to a byte stream
        io_buf = io.BytesIO()
        skimage.io.imsave(io_buf, edges, format="png")
        io_buf.seek(0)

        # Define the path in the Nextcloud directory
        remote_path = f"Photos/{file.filename}"

        # Upload the processed image to Nextcloud
        client.upload_to(buff=io_buf, remote_path=remote_path)

        return {"status": "success", "message": f"Processed file saved to Nextcloud at {remote_path}"}
    except Exception as e:
        logging.error(f"Failed to process or upload image. Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process or upload image.")


@app.get("/image/{filename}")
async def get_image(filename: str):
    try:
        # Assuming you have a function called 'get_file_from_nextcloud' to retrieve the image
        content = get_file_from_nextcloud(f"Photos/{filename}")

        # Guess the MIME type of the file
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = "application/octet-stream"

        return StreamingResponse(io.BytesIO(content), media_type=mime_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class NextcloudService(NextcloudServiceServicer):

    def GetFile(self, request, context):
        content = get_file_from_nextcloud(request.path)
        return FileResponse(content=content)


def serve_grpc():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_NextcloudServiceServicer_to_server(NextcloudService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


# Start gRPC server in a separate thread
threading.Thread(target=serve_grpc, daemon=True).start()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
