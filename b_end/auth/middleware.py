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


# def get_current_user(token: str = Depends(oauth2_scheme))-> dict:
#     credentials_exception = HTTPException(
#         status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"}
#     )
#     try:
#         decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = decoded_payload.get("sub")
#         if username is None:
#             raise credentials_exception
#         user = get_user(users_db, username=username)
#         if user is None:
#             raise credentials_exception
#     except JWTError:
#         raise credentials_exception
#     return user


def extract_user_role_from_token(token: str) -> UserRole:
    """
    Decode the token and extract the user role.
    """
    try:
        decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(decoded_payload['role'], decoded_payload['role']=='admin' )
        return UserRole(decoded_payload.get("role", UserRole.VISITOR))
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def has_permission(user_role: UserRole, permission: str) -> bool:
    """
    Check if the user has the required permission based on their role.
    """
    if not permission:
        return False

    return PERMISSIONS.get(user_role, {}).get(permission, False)


async def auth_middleware(request: Request, call_next):
    # Log entry into middleware
    logging.info("Entering auth middleware")

    # If it's a public endpoint, bypass the checks.
    if request.url.path in PUBLIC_ENDPOINTS:
        return await call_next(request)

    # Extract the token from the request headers.
    auth_header = request.headers.get("Authorization", "")
    if not auth_header or "Bearer " not in auth_header:
        logging.warning("Token is missing or not formatted correctly")
        raise HTTPException(status_code=401, detail="Token is missing or not formatted correctly")

    token = auth_header.replace("Bearer ", "")
    logging.info(f"Received Authorization header: {auth_header}")

    if not token:
        logging.warning("Token is missing")
        raise HTTPException(status_code=401, detail="Token is missing")

    # Extract user role from the token
    logging.info("About to extract user role from token")
    user_role = extract_user_role_from_token(token)
    logging.info(f"This User_Role is: {user_role} extracted from token from middleware,")

    # Fetch the route function associated with the current request
    route_function = request.scope.get("endpoint")

    # Check permission for the user role against the route's tags
    logging.info("About to check required permission")
    required_permission = next(
        (tag for tag in getattr(route_function, "tags", []) if tag in PERMISSIONS[user_role]), None
    )
    logging.info(f"Required Permission: {required_permission}")

    has_perm = has_permission(user_role, required_permission)
    logging.info(f"Has permission: {has_perm}")

    if required_permission is None:
        logging.error("No permission tag found for this route!")
        raise HTTPException(status_code=403, detail="Endpoint configuration error")
    elif not has_perm:
        raise HTTPException(status_code=403, detail="Not authorized")
    else:
        response = await call_next(request)
        return response

    # None as a fallback
    # if required_permission is not None and not has_permission(user_role, required_permission):
    #     raise HTTPException(status_code=403, detail="Not authorized")
