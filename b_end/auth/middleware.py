from .roles import UserRole
from .permissions import PERMISSIONS
from fastapi import Request, HTTPException
from decouple import config
import jwt

SECRET_KEY = config('JWT_SECRET_KEY')


def extract_user_role_from_token(token: str) -> UserRole:
    """
    Decode the token and extract the user role.
    For now, this is simulated to always return VISITOR.
    Decode a JWT or other token format: remaining to be seen what will we use;
    """
    # TODO: Implement JWT decoding and verification
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])  # WIll be adjusted on algorithm as necessary
        return UserRole(payload.get("role", UserRole.VISITOR))
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    # stub
    # Always returning a VISITOR role
    # return UserRole.VISITOR


def has_permission(user_role: UserRole, permission: str) -> bool:
    """
    Check if the user has the required permission based on their role.
    """
    return PERMISSIONS.get(user_role, {}).get(permission, False)


async def auth_middleware(request: Request, call_next):
    # Extract the token from the request headers. This assumes a header format of "Authorization: Bearer TOKEN"
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")

    user_role = extract_user_role_from_token(token)

    # In this dummy implementation required_permission is determined from the path.
    # You might want to adjust this logic to fit your routes and permissions.
    required_permission = request.url.path

    if not has_permission(user_role, required_permission):
        raise HTTPException(status_code=403, detail="Not authorized")

    response = await call_next(request)
    return response
