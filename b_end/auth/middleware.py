from .roles import UserRole
from .permissions import PERMISSIONS
from fastapi import Request, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from decouple import config
from jwt import PyJWTError
import jwt
from .jwt import get_user, users_db

PUBLIC_ENDPOINTS = {"/token"}

SECRET_KEY = config('JWT_SECRET_KEY')
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        user = get_user(users_db, username=username)
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return user


def extract_user_role_from_token(token: str) -> UserRole:
    """
    Decode the token and extract the user role.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return UserRole(payload.get("role", UserRole.VISITOR))
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def has_permission(user_role: UserRole, permission: str) -> bool:
    """
    Check if the user has the required permission based on their role.
    """
    return PERMISSIONS.get(user_role, {}).get(permission, False)


async def auth_middleware(request: Request, call_next):
    # If it's a public endpoint, bypass the checks.
    if request.url.path in PUBLIC_ENDPOINTS:
        return await call_next(request)

    # Extract the token from the request headers. This assumes a header format of "Authorization: Bearer TOKEN"
    auth_header = request.headers.get("Authorization", "")
    if not auth_header or "Bearer " not in auth_header:
        raise HTTPException(status_code=401, detail="Token is missing or not formatted correctly")
    token = auth_header.replace("Bearer ", "")
    print(f"Received Authorization header: {auth_header}")

    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")

    user_role = extract_user_role_from_token(token)
    print(f"This is the usrRole:{user_role} extracted from token from middleware,")
    # Fetch the route function associated with the current request
    route_function = request.scope.get("endpoint")

    # Extract the required permission from the route's tags
    required_permission = next(
        (tag for tag in getattr(route_function, "tags", []) if tag in PERMISSIONS[user_role]), None
    )

    if not required_permission or not has_permission(user_role, required_permission):
        raise HTTPException(status_code=403, detail="Not authorized")

    response = await call_next(request)
    return response
