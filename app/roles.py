import json
from datetime import datetime

from sqlalchemy.orm import Session

from . import models

DEFAULT_ROLES = {
    "admin": {
        "description": "Full system access",
        "permissions": {
            "view_users": True,
            "manage_users": True,
            "view_roles": True,
            "manage_roles": True,
            "view_system": True,
            "manage_system": True,
            "view_all_books": True,
            "manage_all_books": True,
            "manage_own_books": True,
        },
    },
    "user": {
        "description": "Standard user access",
        "permissions": {
            "view_users": False,
            "manage_users": False,
            "view_roles": False,
            "manage_roles": False,
            "view_system": False,
            "manage_system": False,
            "view_all_books": False,
            "manage_all_books": False,
            "manage_own_books": True,
        },
    },
    "moderator": {
        "description": "User management access",
        "permissions": {
            "view_users": True,
            "manage_users": True,
            "view_roles": True,
            "manage_roles": False,
            "view_system": True,
            "manage_system": False,
            "view_all_books": True,
            "manage_all_books": False,
            "manage_own_books": True,
        },
    },
}


def ensure_default_roles_exist(db: Session):
    """Ensure default roles exist in the database and have correct permissions."""
    for role_name, role_data in DEFAULT_ROLES.items():
        role = db.query(models.Role).filter(models.Role.name == role_name).first()
        if not role:
            # Create new role if it doesn't exist
            role = models.Role(
                name=role_name,
                description=role_data["description"],
                permissions=json.dumps(role_data["permissions"]),
                created_at=datetime.utcnow(),
            )
            db.add(role)
        else:
            # Update existing role permissions to ensure they match the defaults
            current_permissions = json.loads(role.permissions)
            default_permissions = role_data["permissions"]
            # Check if permissions need updating
            if current_permissions != default_permissions:
                role.permissions = json.dumps(default_permissions)
                role.description = role_data["description"]

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise Exception(f"Error ensuring default roles exist: {e}") from e


def has_permission(user: models.User, permission: str) -> bool:
    """Check if a user has a specific permission."""
    import logging

    logger = logging.getLogger(__name__)

    logger.info(
        f"Checking permission '{permission}' for user {user.email if user else 'None'}"
    )

    if not user:
        logger.info("No user provided")
        return False

    if not user.role_info:
        logger.info(f"No role_info found for user {user.email}")
        return False

    try:
        permissions = json.loads(user.role_info.permissions)
        logger.info(f"Loaded permissions for role {user.role}: {permissions}")
        has_perm = permissions.get(permission, False)
        logger.info(f"Permission '{permission}' result: {has_perm}")
        return has_perm
    except (json.JSONDecodeError, AttributeError) as e:
        logger.error(f"Error checking permissions: {e}")
        return False


def requires_permission(permission: str):
    """Decorator to check if a user has a specific permission."""
    from fastapi import Depends
    from fastapi import HTTPException

    from .auth import get_current_active_user

    def decorator(func):
        # Preserve the original function's signature
        from functools import wraps

        @wraps(func)
        async def wrapper(
            *args,
            current_user: models.User = Depends(get_current_active_user),
            **kwargs,
        ):
            if not has_permission(current_user, permission):
                raise HTTPException(
                    status_code=403, detail=f"Permission denied: {permission} required"
                )
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator
