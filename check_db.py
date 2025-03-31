from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.auth import get_password_hash
from app.auth import verify_password
from app.database import SQLALCHEMY_DATABASE_URL
from app.models import Role
from app.models import User

# Create engine and session
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Check users
print("\nUsers:")
users = db.query(User).all()
for user in users:
    print(
        f"ID: {user.id}, Email: {user.email}, Role: {user.role}, Active: {user.is_active}"
    )
    print(f"Hashed password: {user.hashed_password}")
    # Test if default password works
    if user.email == "admin@example.com":
        test_password = "admin123"
        is_valid = verify_password(test_password, user.hashed_password)
        print(
            f"Testing password '{test_password}': {'Valid' if is_valid else 'Invalid'}"
        )
        # Print a newly hashed version of the password for comparison
        print(f"New hash of '{test_password}': {get_password_hash(test_password)}")

# Check roles
print("\nRoles:")
roles = db.query(Role).all()
for role in roles:
    print(f"Name: {role.name}, Description: {role.description}")

db.close()
