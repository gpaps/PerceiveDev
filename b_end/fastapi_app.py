from fastapi import FastAPI, UploadFile, HTTPException, File
from fastapi.responses import StreamingResponse
import cv2
import numpy as np
from io import BytesIO
import skimage.io
import requests
import mimetypes
import io
from webdav_setup_config import client
from utils import get_file_from_nextcloud, upload_file_to_nextcloud, list_files_recursive
import logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

class Role(Enum):
    VISITOR = "visitor"
    EDUCATOR = "educator"
    EXPERTS = "experts"
    PERCEIVE_Experts = "per_experts"
    PERCEIVE_Developers = "per_devs"
    Admin = "admin"

# @app.get("/{cmd:cmd,var1:var1,var2:var2}")  # also downloads the file if there is no function_handle
# def read_file(cmd: str):
#     if cmd=="upload":
#         print("UPLOAD")
#
#         # pile of code
#         # broken
#
#     elif cmd=="image":
#         print("UPLOAD")



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


# UPLOAD_FOLDER = "Photos"
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Read file contents
        contents = await file.read()

        # Convert the contents to a numpy array (OpenCV format)
        nparr = np.fromstring(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Apply the Canny edge detection
        edges = cv2.Canny(image, 100, 200)

        # Convert the processed image back to a byte format
        is_success, im_buf_arr = cv2.imencode(".jpg", edges)
        byte_im = im_buf_arr.tobytes()

        # Upload the file to Nextcloud
        status, message = upload_file_to_nextcloud(file.filename, byte_im)
        # status, message = upload_file_to_nextcloud(file.filename, contents)

        if status == "success":
            return {"status": "success", "message": message}
        else:
            raise HTTPException(status_code=500, detail=message)
    except Exception as e:
        logging.error(f"Failed to upload image. Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload image.")



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


@app.get("/list_files/")
async def list_all_files():
    try:
        files = list_files_recursive()
        return {"status": "success", "files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

