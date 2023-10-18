from .roles import UserRole
from .permissions import PERMISSIONS
from fastapi import Request, HTTPException, Depends
from decouple import config
import jwt

SECRET_KEY = config('JWT_SECRET_KEY')

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
    # Extract the token from the request headers. This assumes a header format of "Authorization: Bearer TOKEN"
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")

    user_role = extract_user_role_from_token(token)

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
