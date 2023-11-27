from .roles import UserRole
from .permissions import PERMISSIONS
from fastapi import Request, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from decouple import config
from jwt import PyJWTError, decode, ExpiredSignatureError, InvalidTokenError
import jwt
from .jwt import get_user, users_db
import logging
from enum import Enum

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

PUBLIC_ENDPOINTS = {"/token", "/docs", "/openapi.json", "/redoc", "/login"}

SECRET_KEY = config('JWT_SECRET_KEY')
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # old one was "token" testing endpoint


def has_permission(user_role, required_permission):
    print(f"Checking permission for role: {user_role} against required: {required_permission}")
    allowed = PERMISSIONS.get(user_role, {}).get(required_permission, False)
    return allowed


def convert_to_enum(role: str) -> UserRole:
    try:
        logging.info(f"Converting role: {role}")
        # Explicitly convert the role string to an Enum
        return UserRole[role.upper()]
    except KeyError:
        logging.warning(f"Failed to convert role: {role}")
        return None


def check_permission(user_role_enum: UserRole, permission: str) -> bool:
    return PERMISSIONS.get(user_role_enum, {}).get(permission, False)


def extract_user_role_from_token(token: str) -> str:
    try:
        decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role_str = decoded_payload.get("role")
        print("Extract_user_roles_method outputs: ", f"{role_str}")
        return role_str
        # return decoded_payload['role']
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def auth_middleware(request: Request, call_next):
    logging.info("Entering auth middleware")

    if request.url.path in PUBLIC_ENDPOINTS:
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header or "Bearer " not in auth_header:
        logging.warning("Token is missing or not formatted correctly")
        raise HTTPException(status_code=401, detail="Token is missing or not formatted correctly")

    token = auth_header.replace("Bearer ", "")
    user_role_str = extract_user_role_from_token(token)

    # Validate role conversion here
    user_role_enum = convert_to_enum(user_role_str)
    if user_role_enum is None:
        logging.warning(f"Invalid role: {user_role_str}")
        raise HTTPException(status_code=403, detail="Not authorized")

    logging.info(f"The extracted token from middleware has user_role: -> {user_role_enum}")

    # Commenting out the required_permission based logic.
    # At this point, the user is authenticated and the user_role has been identified.
    # Your route functions will handle the authorization based on this user_role.
    response = await call_next(request)
    return response
