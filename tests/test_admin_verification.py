import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import User
from app.auth import get_password_hash


@pytest.fixture
def admin_token(test_db: Session):
    """Create an admin user and return a token for that user."""
    # Create admin user
    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass"),
        name="Admin User",
        role="admin",
        is_active=True
    )
    test_db.add(admin)
    test_db.commit()
    
    # Get token for admin
    client = TestClient(app)
    response = client.post(
        "/token",
        data={"username": "admin@example.com", "password": "adminpass"},
    )
    token = response.json()["access_token"]
    return token


@pytest.fixture
def test_user(test_db: Session):
    """Create a test user for verification testing."""
    user = User(
        email="testuser@example.com",
        hashed_password=get_password_hash("password"),
        name="Test User",
        role="user",
        is_active=True,
        is_email_verified=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


def test_admin_toggle_verification(test_db: Session, admin_token, test_user):
    """Test that an admin can toggle a user's email verification status."""
    client = TestClient(app)
    
    # Initial state - user should not be verified
    assert test_user.is_email_verified is False
    
    # Admin toggles verification status
    response = client.post(
        f"/admin/users/{test_user.id}/toggle-verification",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Refresh user from database
    test_db.refresh(test_user)
    
    # Verify that the status was toggled to True
    assert test_user.is_email_verified is True
    
    # Toggle again to set back to False
    response = client.post(
        f"/admin/users/{test_user.id}/toggle-verification",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Refresh user from database
    test_db.refresh(test_user)
    
    # Verify that the status was toggled back to False
    assert test_user.is_email_verified is False
    
    # Check that verification token is cleared when setting to unverified
    test_user.verification_token = "test-token"
    test_user.is_email_verified = True
    test_db.commit()
    
    # Toggle to unverified
    response = client.post(
        f"/admin/users/{test_user.id}/toggle-verification",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Refresh user from database
    test_db.refresh(test_user)
    
    # Verify token is cleared
    assert test_user.verification_token is None


def test_non_admin_cannot_toggle_verification(test_db: Session, test_user):
    """Test that non-admin users cannot toggle verification status."""
    # Create regular user
    regular_user = User(
        email="regular@example.com",
        hashed_password=get_password_hash("password"),
        name="Regular User",
        role="user",
        is_active=True
    )
    test_db.add(regular_user)
    test_db.commit()
    
    # Get token for regular user
    client = TestClient(app)
    response = client.post(
        "/token",
        data={"username": "regular@example.com", "password": "password"},
    )
    token = response.json()["access_token"]
    
    # Try to toggle verification as regular user
    response = client.post(
        f"/admin/users/{test_user.id}/toggle-verification",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should be forbidden
    assert response.status_code == 403
