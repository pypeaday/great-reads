import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from app.main import app
from app.models import User
from app.auth import get_password_hash


@pytest.fixture
def admin_token(db: Session):
    """Create an admin user and return a token for that user."""
    # Create admin user
    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass"),
        name="Admin User",
        role="admin",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(admin)
    db.commit()
    
    # Get token for admin
    client = TestClient(app)
    response = client.post(
        "/token",
        data={"username": "admin@example.com", "password": "adminpass"},
    )
    token = response.json()["access_token"]
    return token


@pytest.fixture
def test_user(db: Session):
    """Create a test user for verification testing."""
    user = User(
        email="testuser@example.com",
        hashed_password=get_password_hash("password"),
        name="Test User",
        role="user",
        is_active=True,
        is_email_verified=False,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_admin_toggle_verification(db: Session, admin_token, test_user):
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
    db.refresh(test_user)
    
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
    db.refresh(test_user)
    
    # Verify that the status was toggled back to False
    assert test_user.is_email_verified is False
    
    # Check that verification token is cleared when setting to unverified
    test_user.verification_token = "test-token"
    test_user.is_email_verified = True
    db.commit()
    
    # Toggle to unverified
    response = client.post(
        f"/admin/users/{test_user.id}/toggle-verification",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Refresh user from database
    db.refresh(test_user)
    
    # Verify token is cleared
    assert test_user.verification_token is None


def test_non_admin_cannot_toggle_verification(db: Session, test_user):
    """Test that non-admin users cannot toggle verification status."""
    # Create regular user
    regular_user = User(
        email="regular@example.com",
        hashed_password=get_password_hash("password"),
        name="Regular User",
        role="user",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(regular_user)
    db.commit()
    
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
