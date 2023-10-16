from fastapi import FastAPI, UploadFile, HTTPException, File, Depends, Path
from fastapi.responses import StreamingResponse
import cv2
import numpy as np
from io import BytesIO
import skimage.io
import requests
import mimetypes
import io
# Nextcloud signin and communication between modules
from webdav_setup_config import client
from utils import get_file_from_nextcloud, upload_file_to_nextcloud, list_files_recursive
# authentication package
from auth.roles import UserRole
from auth.middleware import has_permission
# logging
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI()


# @app.get("/{cmd:cmd,var1:var1,var2:var2}")  #
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


@app.get("/some_endpoint/")
async def some_endpoint(user_role: UserRole):
    if not has_permission(user_role, "Tools"):
        raise HTTPException(status_code=403, detail="Permission denied")

    # rest of your endpoint logic


# Create middleware for permission checking
def get_current_role():
    # Mocked function to return a role, you would get this from your authentication method
    return Role.EDUCATOR


def has_permission(required_permission: str):
    def role_verifier(current_role: Role = Depends(get_current_role)):
        if required_permission not in ROLE_PERMISSIONS[current_role]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        return True


# Create FastAPI routes and apply permissions:
@app.get("/api_endpoint")
def api_endpoint(permissions: bool = Depends(has_permission("api"))):
    return {"message": "You have API access!"}


@app.get("/tools_endpoint")
def tools_endpoint(permissions: bool = Depends(has_permission("tools"))):
    return {"message": "You have tools access!"}


@app.get("/services_endpoint")
def services_endpoint(permissions: bool = Depends(has_permission("services"))):
    return {"message": "You have services access!"}


@app.get("/datasets_endpoint")
def datasets_endpoint(permissions: bool = Depends(has_permission("datasets"))):
    return {"message": "You have datasets access!"}


@app.get("/code_repo_endpoint")
def code_repo_endpoint(permissions: bool = Depends(has_permission("code_repo"))):
    return {"message": "You have code repository access!"}


@app.get("/change_user_permissions_endpoint")
def change_user_permissions_endpoint(permissions: bool = Depends(has_permission("change_user_permissions"))):
    return {"message": "You have permission to change user permissions!"}
