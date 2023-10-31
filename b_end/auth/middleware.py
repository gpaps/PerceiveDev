from .roles import UserRole
from .permissions import PERMISSIONS
from fastapi import Request, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from decouple import config
from jwt import PyJWTError
import jwt
from .jwt import get_user, users_db
import logging

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

PUBLIC_ENDPOINTS = {"/token"}

SECRET_KEY = config('JWT_SECRET_KEY')
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def convert_to_enum(role: str) -> UserRole:
    try:
        logging.info(f"Converting role: {role}")
        return UserRole(role.upper())
    except ValueError:
        logging.warning(f"Failed to convert role: {role}")
        return None


def check_permission(user_role_enum: UserRole, permission: str) -> bool:
    return PERMISSIONS.get(user_role_enum, {}).get(permission, False)


def extract_user_role_from_token(token: str) -> str:
    try:
        decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_payload['role']
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
    logging.info(f"Received Authorization header: {auth_header}")

    if not token:
        logging.warning("Token is missing")
        raise HTTPException(status_code=401, detail="Token is missing")

    logging.info("About to extract user role from token")
    user_role_str = extract_user_role_from_token(token)
    user_role_enum = convert_to_enum(user_role_str)
    if user_role_enum is None:
        logging.warning(f"Invalid role: {user_role_str}")
        raise HTTPException(status_code=403, detail="Not authorized")

    logging.info(f"The extracted token from middleware has user_role: -> {user_role_enum}")

    route_function = request.scope.get("endpoint")

    logging.info("About to check required permission")
    required_permission = next(
        (tag for tag in getattr(route_function, "tags", []) if tag in PERMISSIONS[user_role_enum.name]), None
    )
    logging.info(f"Required Permission: {required_permission}")

    has_perm = check_permission(user_role_enum, required_permission)
    logging.info(f"Has permission: {has_perm}")

    if required_permission is None:
        logging.info("Public route, no permission required.")
        return await call_next(request)
    elif not has_perm:
        raise HTTPException(status_code=403, detail="Not authorized")
    else:
        response = await call_next(request)
        return response
