from .roles import UserRole
from .permissions import PERMISSIONS


def has_permission(user_role: UserRole, permission: str) -> bool:
    """
    Check if the user has the required permission based on their role.
    """
    return PERMISSIONS.get(user_role, {}).get(permission, False)
