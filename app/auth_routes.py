import logging
from datetime import datetime
from datetime import timedelta

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import auth
from . import database
from . import models
from . import schemas
from . import themes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_current_theme(request: Request) -> tuple[themes.ThemeColors, str]:
    """Get the current theme colors based on cookie or default"""
    theme_name = request.cookies.get("theme", "gruvbox-dark")
    theme = themes.get_theme(theme_name)
    if not theme:
        theme = themes.get_theme("gruvbox-dark")
        theme_name = "gruvbox-dark"
    return theme, theme_name


def set_theme_cookie(response: HTMLResponse, theme_name: str) -> None:
    """Set theme cookie with standard parameters"""
    response.set_cookie(
        key="theme",
        value=theme_name,
        max_age=31536000,  # 1 year
        httponly=False,  # Allow JavaScript to read the cookie
        samesite="lax",
        secure=False,  # Allow non-HTTPS for local development
    )


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(request: Request, db: Session = Depends(database.get_db)):
    """API endpoint for obtaining a token."""
    form_data = await request.form()
    username = form_data.get("username")
    password = form_data.get("password")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username and password are required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth.authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Display registration page."""
    theme, current_theme = get_current_theme(request)
    
    # Generate captcha for the registration form
    from .utils import generate_captcha
    captcha_challenge, captcha_answer = generate_captcha()
    
    # Store captcha answer in session
    request.session["captcha_answer"] = captcha_answer
    
    response = templates.TemplateResponse(
        "register.html",
        {
            "request": request, 
            "theme": theme, 
            "current_theme": current_theme,
            "captcha_challenge": captcha_challenge,
        },
    )
    set_theme_cookie(response, current_theme)
    return response


@router.post("/register", response_class=HTMLResponse)
async def register_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    captcha: str = Form(...),
    db: Session = Depends(database.get_db),
):
    """Register a new user."""
    theme, current_theme = get_current_theme(request)
    
    # Generate a new captcha for the form in case of validation errors
    from .utils import generate_captcha
    new_captcha_challenge, new_captcha_answer = generate_captcha()
    
    # Get the stored captcha answer from session
    stored_captcha_answer = request.session.get("captcha_answer")
    
    # Validate captcha
    if not stored_captcha_answer or captcha.upper() != stored_captcha_answer:
        # Store the new captcha answer for the next attempt
        request.session["captcha_answer"] = new_captcha_answer
        
        response = templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "theme": theme,
                "current_theme": current_theme,
                "error": "Invalid security code",
                "captcha_error": "Please enter the correct security code",
                "captcha_challenge": new_captcha_challenge,
            },
        )
        set_theme_cookie(response, current_theme)
        return response

    # Validate inputs
    if password != confirm_password:
        # Store the new captcha answer for the next attempt
        request.session["captcha_answer"] = new_captcha_answer
        
        response = templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "theme": theme,
                "current_theme": current_theme,
                "error": "Passwords do not match",
                "captcha_challenge": new_captcha_challenge,
            },
        )
        set_theme_cookie(response, current_theme)
        return response

    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.email == email).first()
    if existing_user:
        # Store the new captcha answer for the next attempt
        request.session["captcha_answer"] = new_captcha_answer
        
        response = templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "theme": theme,
                "current_theme": current_theme,
                "error": "Email already registered",
                "captcha_challenge": new_captcha_challenge,
            },
        )
        set_theme_cookie(response, current_theme)
        return response

    # Create new user with default role
    hashed_password = auth.get_password_hash(password)
    new_user = models.User(
        email=email,
        hashed_password=hashed_password,
        created_at=datetime.utcnow(),
        is_active=True,
        role="user",  # Set default role
        theme_preference="gruvbox-dark",  # Set default theme
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Clear the captcha from session
    if "captcha_answer" in request.session:
        del request.session["captcha_answer"]

    # Create success response with toast notification
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.headers["HX-Trigger"] = (
        '{"showToast": {"message": "Registration successful! Please log in.", "type": "success"}}'
    )
    set_theme_cookie(response, current_theme)
    return response


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Display login page."""
    theme, current_theme = get_current_theme(request)
    response = templates.TemplateResponse(
        "login.html",
        {"request": request, "theme": theme, "current_theme": current_theme},
    )
    set_theme_cookie(response, current_theme)
    return response


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    db: Session = Depends(database.get_db),
):
    """Log in a user."""
    form = await request.form()
    email = form.get("email")
    password = form.get("password")
    remember_me = form.get("remember_me")
    theme, current_theme = get_current_theme(request)

    logger.info(f"Login attempt - Email: {email}")

    # Authenticate user
    user = auth.authenticate_user(db, email, password)
    logger.info(f"Authentication result: {'Success' if user else 'Failed'}")

    if not user:
        logger.info("Authentication failed - returning error response")
        response = templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "theme": theme,
                "current_theme": current_theme,
                "error": "Invalid email or password",
            },
        )
        set_theme_cookie(response, current_theme)
        return response

    # Create access token with longer expiration if remember_me is checked
    if remember_me:
        # 30 days if remember me is checked
        access_token_expires = timedelta(days=30)
    else:
        # Default 30 minutes
        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    logger.info(f"Created access token for user: {user.email}")

    # Create success response with token cookie
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    # Set cookie max_age to match token expiration
    max_age = 30 * 24 * 60 * 60 if remember_me else 1800  # 30 days or 30 minutes
    
    import os
    # Get environment variables for cookie settings
    cookie_secure = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    cookie_samesite = os.getenv("COOKIE_SAMESITE", "strict")
    
    logger.info(f"Setting access_token cookie (secure: {cookie_secure}, samesite: {cookie_samesite})")
    response.set_cookie(
        key="access_token",
        value=access_token,  # Store just the token, middleware will add 'Bearer'
        httponly=True,
        max_age=max_age,
        samesite=cookie_samesite,
        secure=cookie_secure,
        path="/",  # Ensure cookie is sent for all paths
    )
    response.headers["HX-Trigger"] = (
        '{"showToast": {"message": "Login successful!", "type": "success"}}'
    )
    set_theme_cookie(response, current_theme)
    logger.info("Login successful - returning redirect response")
    return response


@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    """Log out a user."""
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    response.headers["HX-Trigger"] = (
        '{"showToast": {"message": "Logged out successfully", "type": "success"}}'
    )
    return response


# Create a dependency that will check for authenticated user
def user_dependency(
    token: str = Depends(auth.oauth2_scheme), db: Session = Depends(database.get_db)
):
    return auth.get_current_user_sync(token, db)


@router.get("/profile", response_class=HTMLResponse)
async def profile(
    request: Request,
    current_user: models.User = Depends(user_dependency),
    db: Session = Depends(database.get_db),
):
    """Display user profile with analytics."""
    theme, current_theme = get_current_theme(request)
    
    # Get reading stats
    from . import analytics
    stats = analytics.get_reading_stats(db, current_user.id)
    
    # Get monthly reading data for chart
    monthly_data = analytics.get_monthly_reading_data(db, current_user.id)
    
    # Get books timeline data
    books_timeline = analytics.get_books_timeline(db, current_user.id)

    response = templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "theme": theme,
            "current_theme": current_theme,
            "user": current_user,
            "stats": stats,
            "monthly_data": monthly_data,
            "books_timeline": books_timeline,
        },
    )
    set_theme_cookie(response, current_theme)
    return response
