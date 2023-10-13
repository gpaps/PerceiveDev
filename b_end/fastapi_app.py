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
from utils import get_file_from_nextcloud, upload_file_to_nextcloud
import logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()


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
#
#     try:
#         content = get_file_from_nextcloud(path)
#         mime_type, encoding = mimetypes.guess_type(path)
#         if not mime_type:
#             mime_type = "application/octet-stream"
#         response = StreamingResponse(BytesIO(content), media_type=mime_type)
#         response.headers["Content-Disposition"] = f"attachment; filename={path.split('/')[-1]}"
#         return response
#     except requests.RequestException as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching file: {str(e)}")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


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
# @app.post("/upload/")
# async def upload_file(file: UploadFile = File(...)):
#     try:
#
#         # Read image contents
#         contents = await file.read()
#         image = skimage.io.imread(io.BytesIO(contents))
#
#         # Process the image
#         edges = cv2.Canny(image, 100, 200)
#
#         # Convert the processed image to a byte stream
#         io_buf = io.BytesIO()
#         skimage.io.imsave(io_buf, edges, format="png")
#         io_buf.seek(0)
#
#         # Define the path in the Nextcloud directory
#         remote_path = f"{UPLOAD_FOLDER}/{file.filename}"
#
#         # Upload the processed image to Nextcloud
#         client.upload_to(buff=io_buf, remote_path=remote_path)
#
#         return {"status": "success", "message": f"Processed file saved to Nextcloud at {remote_path}"}
#     except Exception as e:
#         print(f"Exception occurred: {e}")  # For debugging purposes
#         logging.error(f"Failed to process or upload image. Error: {e}")
#         raise HTTPException(status_code=500, detail="Failed to process or upload image.")

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
        is_success, im_buf_arr = cv2.imencode(".png", edges)
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
