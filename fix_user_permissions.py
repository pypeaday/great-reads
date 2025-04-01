import json
import sys
from datetime import datetime

from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal, engine

def fix_user_permissions():
    """Fix the permissions for the user role in the database."""
    db = SessionLocal()
    try:
        # Get the user role
        user_role = db.query(models.Role).filter(models.Role.name == "user").first()
        
        if not user_role:
            print("User role not found in database")
            return
        
        # Define the correct permissions for the user role
        correct_permissions = {
            "view_users": False,
            "manage_users": False,
            "view_roles": False,
            "manage_roles": False,
            "view_system": False,
            "manage_system": False,
            "view_all_books": False,
            "manage_all_books": False,
            "manage_own_books": True,
        }
        
        # Convert to JSON string
        permissions_json = json.dumps(correct_permissions)
        
        # Update the user role permissions
        user_role.permissions = permissions_json
        
        # Commit the changes
        db.commit()
        
        print(f"Successfully updated permissions for the user role: {permissions_json}")
        
    except Exception as e:
        db.rollback()
        print(f"Error updating user role permissions: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_user_permissions()
