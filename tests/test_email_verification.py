from datetime import datetime, timedelta
import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.models import User


def test_user_verification_fields(db: Session):
    """Test that the User model has the verification fields."""
    # Create a test user
    user = User(
        email="verify_test@example.com",
        name="Verify Test",
        hashed_password="hashed_password",
        is_active=True,
        created_at=datetime.utcnow(),
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Check that the verification fields exist and have default values
    assert hasattr(user, "is_email_verified")
    assert hasattr(user, "verification_token")
    assert hasattr(user, "verification_token_expires")
    
    # Default value for is_email_verified should be False
    assert user.is_email_verified is False or user.is_email_verified is None
    
    # Default values for token fields should be None
    assert user.verification_token is None
    assert user.verification_token_expires is None


def test_profile_page_shows_verification_status(client, user_headers, regular_user):
    """Test that the profile page shows verification status."""
    # Access the profile page
    response = client.get("/profile", headers=user_headers)
    assert response.status_code == status.HTTP_200_OK
    
    # Check that the verification status is shown
    content = response.text
    assert "Not Verified" in content
    assert "Email verification is planned for a future release" in content


def test_profile_page_shows_verified_status(client, user_headers, db, regular_user):
    """Test that the profile page shows verified status when email is verified."""
    # Update the user to be verified
    db.query(User).filter(User.id == regular_user.id).update({
        "is_email_verified": True
    })
    db.commit()
    
    # Access the profile page
    response = client.get("/profile", headers=user_headers)
    assert response.status_code == status.HTTP_200_OK
    
    # Check that the verified status is shown
    content = response.text
    assert "Verified" in content
    assert "Not Verified" not in content


@pytest.fixture
def verified_user(db, test_password):
    """Create a user with verified email."""
    hashed_password = "hashed_for_testing"  # In real tests, use get_password_hash
    
    user = User(
        email="verified@example.com",
        name="Verified User",
        hashed_password=hashed_password,
        is_active=True,
        created_at=datetime.utcnow(),
        role="user",
        is_email_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_with_token(db, test_password):
    """Create a user with a verification token."""
    hashed_password = "hashed_for_testing"  # In real tests, use get_password_hash
    
    user = User(
        email="token@example.com",
        name="Token User",
        hashed_password=hashed_password,
        is_active=True,
        created_at=datetime.utcnow(),
        role="user",
        is_email_verified=False,
        verification_token="test-verification-token",
        verification_token_expires=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_user_with_expired_token(db, user_with_token):
    """Test user with an expired verification token."""
    # Set the token to be expired
    db.query(User).filter(User.id == user_with_token.id).update({
        "verification_token_expires": datetime.utcnow() - timedelta(hours=1)
    })
    db.commit()
    db.refresh(user_with_token)
    
    # Check that the token is expired
    assert user_with_token.verification_token_expires < datetime.utcnow()
