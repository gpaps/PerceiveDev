from pydantic import BaseModel
import traceback

from fastapi import FastAPI, UploadFile, HTTPException, File, Depends, Path, Query, Header, Body, Response, APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.exceptions import RequestValidationError

import cv2
import numpy as np
from io import BytesIO
import skimage.io
import requests
import mimetypes
import io, os, base64
from datetime import timedelta
# Nextcloud signin and communication between modules
from webdav_setup_config import client
from utils import get_file_from_nextcloud, upload_file_to_nextcloud, list_files_recursive
# authentication package
from auth.jwt import (verify_password, get_user, create_access_token,
                      oauth2_scheme, users_db, ACCESS_TOKEN_EXPIRE_MINUTES)
import jwt
from auth.roles import UserRole
from auth.middleware import auth_middleware, has_permission  # , get_current_user
from auth.models import User, UserInDB, Token
# logging
import logging
from decouple import config

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="PERCEIVE API",
    description="Backend services for the PERCEIVE project.",
    version="1.0.0",
)
app.middleware("http")(auth_middleware)


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(users_db, username=form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # Embed the role in the token payload
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username, "role": user.role.name},
                                       expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer"}


# TODO decide for loging and token endpoints
@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(users_db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/logout")
async def logout():
    response = Response(content="Logged out", status_code=200)
    response.delete_cookie(key="Authorization")
    return response

from auth.middleware import extract_user_role_from_token


async def get_user_role(token: str = Header(..., alias="Authorization")) -> UserRole:
    print('Reached ___ get_user_role()method')
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Invalid or missing token")
    token = token[7:]
    try:
        payload = jwt.decode(token, config('JWT_SECRET_KEY'), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    role = payload.get("role", UserRole.VISITOR.value)
    print(f"Prints the Role from get_user_role: {role}")
    return UserRole(role)


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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": "Error processing request. Check file size or format."}
    )


router = APIRouter()


class CannyEdgeRequest(BaseModel):
    image: str
    filename: str
    minThreshold: float
    maxThreshold: float


class CannyEdgeResponse(BaseModel):
    image: str  # base64 encoded processed image


@router.post("/canny-edge-detection/", response_model=CannyEdgeResponse)
async def canny_edge_detection(
        file: UploadFile = File(...),
        min_threshold: float = Query(default=100.0, ge=0, le=100),  # Now with default values
        max_threshold: float = Query(default=200.0, ge=100, le=300),  # Now with default values
        user_role: UserRole = Depends(get_user_role)):

    # Check if the user has permission to use this endpoint
    if not has_permission(user_role, "CannyEdgeDetection"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied for Canny Edge Detection"
        )
    # Read the file contents
    contents = await file.read()
    # Process the image with Canny Edge Detection
    processed_image_base64 = process_image_canny_edge(contents, min_threshold, max_threshold)
    # Return the processed image in base64 format
    return CannyEdgeResponse(image=processed_image_base64)


# @app.post("/canny-edge-detection/")  # duplicate route from "upload" method to tackle the colab phase.
# async def canny_edge_detection(file: UploadFile = File(...), min_threshold: float = Query(default=100, ge=0, le=100),
#                                max_threshold: float = Query(default=200, ge=100, le=300)):
#     # Read file contents and apply Canny edge detection...
#     logging.info(f"Received request: File Name = {file.filename}, Content Type = {file.content_type}")
#     # Image size limit (20 MB)
#     MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB in bytes
#
#     # Check file format
#     allowed_formats = ["image/jpeg", "image/png", "image/tiff"]
#     if file.content_type not in allowed_formats:
#         raise HTTPException(status_code=415, detail="Unsupported file format.")
#
#     contents = await file.read()
#     file_size = len(contents)
#
#     # Check file size
#     if file_size > MAX_FILE_SIZE:
#         return JSONResponse(
#             status_code=413,
#             content={"detail": "File size exceeds 20 MB limit."}
#         )
#
#     if file.content_type not in allowed_formats:
#         return JSONResponse(
#             status_code=415,
#             content={"detail": "Unsupported file format."}
#         )
#
#     try:
#         # Read file contents
#         # contents = await file.read()
#
#         # Convert the contents to a numpy array (OpenCV format)
#         nparr = np.fromstring(contents, np.uint8)
#         image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#
#         # Apply the Canny edge detection
#         edges = cv2.Canny(image, min_threshold, max_threshold)
#
#         # Convert the processed image back to a byte format
#         _, buffer = cv2.imencode(".jpg", edges)
#         encoded_image = base64.b64encode(buffer).decode("utf-8")
#
#         # Upload the file to Nextcloud
#         status, message = upload_file_to_nextcloud(file.filename, encoded_image)
#
#         if status == "success":
#             # return {"image": processed_image_base64}
#             # return {"image": encoded_image}
#             # processed_image_url = f"{nextcloud_base_url}/{UPLOAD_FOLDER}/{file.filename}"  # Modify as needed
#             # return {"status": "success", "message": "Image processed successfully",
#             #         "processed_image_url": processed_image_url}
#             return {"status": "success", "message": message}
#         else:
#             raise HTTPException(status_code=500, detail=message)
#     except Exception as e:
#         error_details = traceback.format_exc()
#         logging.error(f"Failed to process image. Error: {e}\n{error_details}")
#         return JSONResponse(
#             status_code=500,
#             content={"detail": f"Failed to process image. Error: {str(e)}"}
#         )

# UPLOAD_FOLDER = "Photos"
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):  # This method uploads in photos via grpc service in Nextcloud
    try:
        # Read file contents
        contents = await file.read()

        # Convert the contents to a numpy array (OpenCV format)
        # nparr = np.fromstring(contents, np.uint8)
        # image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Apply the Canny edge detection
        # edges = cv2.Canny(image, 100, 200)
        # edges = cv2.Canny(image, min_threshold, max_threshold)

        # Convert the processed image back to a byte format
        # is_success, im_buf_arr = cv2.imencode(".jpg", edges)
        # byte_im = im_buf_arr.tobytes()

        # Upload the file to Nextcloud
        # status, message = upload_file_to_nextcloud(file.filename, byte_im)
        status, message = upload_file_to_nextcloud(file.filename, contents)

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
        logging.error(f"Error in get_image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
        # raise HTTPException(status_code=500, detail=str(e))


@app.get("/list_files/")
async def list_all_files():
    try:
        files = list_files_recursive()
        return {"status": "success", "files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test/admin")  # , tags=[UserRole.ADMIN.value])
async def test_admin():
    return {"status": "Admin access granted!"}


@app.get("/web_portal/")
async def web_portal(user_role: UserRole = Depends(get_user_role)):
    print('web_portal - reached')
    if not has_permission(user_role, "Tools"):
        print(f"Has permission returned: {has_permission(user_role, 'Tools')}")
        raise HTTPException(status_code=403, detail="Permission denied to access web portal")
    return {"detail": "Welcome to the web portal!"}


@app.get("/educational_services/", tags=["Services"])
async def educational_services(user_role: UserRole = Depends(get_user_role)):
    if not has_permission(user_role, "Services"):
        raise HTTPException(status_code=403, detail="Permission denied to access educational services")
    return {"detail": "Access granted to educational services"}


@app.get("/expert_tools/", tags=["Tools"])
async def expert_tools(user_role: UserRole = Depends(get_user_role)):
    if not has_permission(user_role, "Tools"):
        raise HTTPException(status_code=403, detail="Permission denied to access expert tools")
    return {"detail": "Access granted to expert tools"}


@app.get("/datasets/", tags=["Dataset"])
async def datasets(user_role: UserRole = Depends(get_user_role)):
    if not has_permission(user_role, "Dataset"):
        raise HTTPException(status_code=403, detail="Permission denied to access datasets")
    return {"detail": "Access granted to datasets"}


@app.get("/trained_models/", tags=["Trained_Models"])
async def trained_models(user_role: UserRole = Depends(get_user_role)):
    if not has_permission(user_role, "Trained_Models"):
        raise HTTPException(status_code=403, detail="Permission denied to access trained models")
    return {"detail": "Access granted to trained models"}


@app.get("/code_repository/", tags=["Code_Repo"])
async def code_repository(user_role: UserRole = Depends(get_user_role)):
    if not has_permission(user_role, "Code_Repo"):
        raise HTTPException(status_code=403, detail="Permission denied to access code repository")
    return {"detail": "Access granted to code repository"}


@app.get("/change_user_permissions/", tags=["Change_User_Permissions"])
async def change_user_permissions(user_role: UserRole = Depends(get_user_role)):
    if not has_permission(user_role, "Change_User_Permissions"):
        raise HTTPException(status_code=403, detail="Permission denied to change user permissions")
    return {"detail": "Access granted to change user permissions"}
