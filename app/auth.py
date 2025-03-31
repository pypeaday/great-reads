import logging
import os
import secrets
import smtplib
from datetime import datetime
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from . import database
from . import models

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Use environment variable for SECRET_KEY or fallback to a default for development
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_secret_key_change_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def verify_password(plain_password, hashed_password):
    """Verify a password against a hash."""
    logger.info("Verifying password")
    result = pwd_context.verify(plain_password, hashed_password)
    logger.info(f"Password verification result: {result}")
    return result


def get_password_hash(password):
    """Hash a password for storing."""
    return pwd_context.hash(password)


def authenticate_user(db: Session, email: str, password: str):
    """Authenticate a user by email and password."""
    logger.info(f"\nAuthentication attempt for email: {email}")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        logger.info("User not found in database")
        return False
    logger.info(
        f"User found - ID: {user.id}, Role: {user.role}, Active: {user.is_active}"
    )
    if not verify_password(password, user.hashed_password):
        logger.info("Password verification failed")
        return False
    if not user.is_active:
        logger.info("User is not active")
        return False
    logger.info("Authentication successful")
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_token_from_cookie(request: Request):
    """Extract token from cookie."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    # Remove 'Bearer ' prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
    return token


def get_optional_current_user_sync(token: str, db: Session):
    """Synchronous version of get_optional_current_user."""
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        user = db.query(models.User).filter(models.User.email == email).first()
        return user
    except JWTError:
        return None


async def get_optional_current_user(
    request: Request = None, db: Session = None
):
    if db is None:
        db = database.get_db()
    """Get the current user from a JWT token in cookie, or None if not authenticated."""
    if not request:
        return None

    token = await get_token_from_cookie(request)
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        user = db.query(models.User).filter(models.User.email == email).first()
        return user
    except JWTError:
        return None


def get_current_user_sync(token: str, db: Session):
    """Synchronous version of get_current_user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        user = db.query(models.User).filter(models.User.email == email).first()
        if user is None:
            raise credentials_exception
        return user
    except JWTError as err:
        raise credentials_exception from err


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = None
):
    """Get the current user from a JWT token."""
    if db is None:
        db = database.get_db()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError as err:
        raise credentials_exception from err
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    token: str = Depends(oauth2_scheme), db: Session = None
):
    if db is None:
        db = database.get_db()
    current_user = await get_current_user(token=token, db=db)
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(token: str = Depends(oauth2_scheme), db: Session = None):
    if db is None:
        db = database.get_db()
    current_user = await get_current_user(token=token, db=db)
    """Get the current user and verify they have admin role."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Admin role required.",
        )
    return current_user


def check_user_role(required_role: str):
    """Dependency function factory to check if user has a specific role."""

    async def check_role(token: str = Depends(oauth2_scheme), db: Session = None):
        if db is None:
            db = database.get_db()
        current_user = await get_current_user(token=token, db=db)
        if not current_user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        if current_user.role != required_role and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized. {required_role.capitalize()} role required.",
            )
        return current_user

    return check_role


def create_default_admin(db: Session):
    """
    Create the default administrator account.
    This should be called when setting up a new instance of the application.
    """
    # Get admin credentials from environment or use defaults
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")  # Change in production!

    # Check if admin already exists
    admin = db.query(models.User).filter(models.User.email == admin_email).first()
    if not admin:
        # Create admin user
        admin = models.User(
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            is_active=True,
            role="admin",
            created_at=datetime.utcnow(),
        )
        db.add(admin)
        try:
            db.commit()
            db.refresh(admin)
            logger.info(f"Created default admin user: {admin_email}")
            logger.info(
                "IMPORTANT: Please change the default admin password in production!"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating admin user: {e}")
            raise
    return admin


def ensure_admin_exists(db: Session):
    """
    Ensure that at least one admin user exists in the system.
    Creates a default admin if none exists.
    """
    # Check if any admin user exists
    admin = db.query(models.User).filter(models.User.role == "admin").first()
    if not admin:
        # Create default admin if no admin exists
        admin = create_default_admin(db)
    return admin


# Email configuration
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.example.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@greatreads.com")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")


def send_email(to_email: str, subject: str, html_content: str):
    """Send an email using SMTP."""
    if not all([EMAIL_HOST, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD]):
        logger.warning("Email settings not configured. Email not sent.")
        return False

    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = EMAIL_FROM
        message["To"] = to_email

        # Attach HTML content
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)

        # Connect to SMTP server and send email
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.sendmail(EMAIL_FROM, to_email, message.as_string())

        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False


def generate_verification_token():
    """Generate a random token for email verification."""
    return secrets.token_urlsafe(32)


def create_verification_token(db: Session, user_id: int):
    """Create a verification token for a user and save it to the database."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None

    # Generate token and set expiration (24 hours from now)
    token = generate_verification_token()
    expiration = datetime.utcnow() + timedelta(hours=24)

    # Update user record
    user.verification_token = token
    user.verification_token_expires = expiration
    db.commit()

    return token


def verify_email(db: Session, token: str):
    """Verify a user's email using the verification token."""
    user = db.query(models.User).filter(
        models.User.verification_token == token,
        models.User.verification_token_expires > datetime.utcnow()
    ).first()

    if not user:
        return False

    # Update user record
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()

    return True


def send_verification_email(db: Session, user_id: int):
    """Send a verification email to a user."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return False

    # Create verification token
    token = create_verification_token(db, user.id)
    if not token:
        return False

    # Create verification URL
    verification_url = f"{APP_BASE_URL}/verify-email?token={token}"

    # Email content
    subject = "Verify Your Great Reads Account"
    html_content = f"""
    <html>
        <body>
            <h2>Welcome to Great Reads!</h2>
            <p>Thank you for registering. Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_url}">Verify Email Address</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>If you did not create an account, you can safely ignore this email.</p>
        </body>
    </html>
    """

    # Send email
    return send_email(user.email, subject, html_content)


def create_password_reset_token(db: Session, email: str):
    """Create a password reset token for a user and save it to the database."""
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return None

    # Generate token and set expiration (1 hour from now)
    token = secrets.token_urlsafe(32)
    expiration = datetime.utcnow() + timedelta(hours=1)

    # Update user record
    user.reset_token = token
    user.reset_token_expires = expiration
    db.commit()

    return token


def verify_password_reset_token(db: Session, token: str):
    """Verify a password reset token."""
    user = db.query(models.User).filter(
        models.User.reset_token == token,
        models.User.reset_token_expires > datetime.utcnow()
    ).first()

    return user


def reset_password(db: Session, token: str, new_password: str):
    """Reset a user's password using a reset token."""
    user = verify_password_reset_token(db, token)
    if not user:
        return False

    # Update password and clear token
    user.hashed_password = get_password_hash(new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return True


def send_password_reset_email(db: Session, email: str):
    """Send a password reset email to a user."""
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        # Don't reveal that the email doesn't exist for security reasons
        # Just pretend we sent the email
        return True

    # Create reset token
    token = create_password_reset_token(db, user.email)
    if not token:
        return False

    # Create reset URL
    reset_url = f"{APP_BASE_URL}/reset-password?token={token}"

    # Email content
    subject = "Reset Your Great Reads Password"
    html_content = f"""
    <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>We received a request to reset your password. Click the link below to create a new password:</p>
            <p><a href="{reset_url}">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you did not request a password reset, you can safely ignore this email.</p>
        </body>
    </html>
    """

    # Send email
    return send_email(user.email, subject, html_content)
