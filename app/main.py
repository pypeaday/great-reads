from fastapi import FastAPI, Depends, HTTPException, Request, Form, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import os
import json
from dotenv import load_dotenv

# Base imports
from . import (
    models,
    database,
    themes,
    auth,
    auth_routes,
    roles,
    jinja_filters,
    book_routes,
)

# Conditional imports based on features
try:
    from . import admin_routes

    ADMIN_ENABLED = True
except ImportError:
    ADMIN_ENABLED = False

from .auth import get_optional_current_user, get_optional_current_user_sync

# Load environment variables
load_dotenv()

app = FastAPI(title="Book Tracker")
templates = Jinja2Templates(directory="app/templates")

# Store templates in app state for access in routes
app.state.templates = templates

# Register custom Jinja2 filters
jinja_filters.register_filters(templates)


# Add middleware to handle HTMX PUT/DELETE requests
@app.middleware("http")
async def handle_htmx_methods(request: Request, call_next):
    if request.method == "POST" and "hx-request" in request.headers:
        # Only read form for HTMX requests
        form = await request.form()
        if "_method" in form and form["_method"] in ["PUT", "DELETE"]:
            request.scope["method"] = form["_method"]
    return await call_next(request)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:8000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add middleware to extract token from cookies
@app.middleware("http")
async def cookie_to_authorization(request: Request, call_next):
    import logging

    logger = logging.getLogger(__name__)

    # Extract token from cookie
    token = request.cookies.get("access_token")
    logger.info(f"Cookie token: {token}")

    # Check if we have a token and no authorization header already exists
    has_auth_header = False
    for k, v in request.scope.get("headers", []):
        if k.decode().lower() == "authorization":
            has_auth_header = True
            logger.info("Found existing auth header")
            break

    # Create a modified scope with the authorization header if token exists and no auth header
    if token and not has_auth_header:
        # Get the original headers as a list of tuples
        headers = list(request.scope.get("headers", []))

        # Add the authorization header
        # If token doesn't start with 'Bearer ', add it
        if not token.startswith("Bearer "):
            auth_value = f"Bearer {token}"
        else:
            auth_value = token
        logger.info(f"Adding auth header: {auth_value}")
        headers.append((b"authorization", auth_value.encode()))

        # Update the scope headers
        request.scope["headers"] = headers
        logger.info("Updated request headers with token")

    # Process the request and get the response
    response = await call_next(request)
    logger.info(f"Response status code: {response.status_code}")
    return response


# Include auth routes
app.include_router(auth_routes.router)

# Include routers
if ADMIN_ENABLED:
    app.include_router(admin_routes.router)

app.include_router(book_routes.router)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Default theme
DEFAULT_THEME = "gruvbox-dark"


def get_current_theme(request: Request) -> tuple[themes.ThemeColors, str]:
    """Get the current theme colors based on user preference, cookie, or default"""
    # Try to get current user
    db = database.SessionLocal()
    try:
        current_user = get_optional_current_user_sync(
            request.cookies.get("access_token"), db
        )

        # Get theme from user preference if logged in
        if current_user and current_user.theme_preference:
            theme_name = current_user.theme_preference
        else:
            # Fall back to cookie or default
            theme_name = request.cookies.get("theme", DEFAULT_THEME)

        theme = themes.get_theme(theme_name)
        if not theme:
            theme = themes.get_theme(DEFAULT_THEME)
            theme_name = DEFAULT_THEME

        return theme, theme_name
    finally:
        db.close()


def set_theme_cookie(response: HTMLResponse, theme_name: str) -> None:
    """Set theme cookie with standard parameters"""
    response.set_cookie(
        key="theme",
        value=theme_name,
        max_age=31536000,  # 1 year
        httponly=False,  # Allow JavaScript to read the cookie
        samesite=os.getenv("COOKIE_SAMESITE", "lax"),
        secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
    )


# API Models
class ThemeColors(BaseModel):
    bg: str
    bg1: str
    bg2: str
    fg: str
    fg1: str
    accent: str
    accent_hover: str
    success: str
    error: str


def init_db(db_session=None):
    """Initialize database with admin user and default roles"""
    print("Initializing database...")
    try:
        if db_session is None:
            with database.SessionLocal() as db:
                # Create admin user if it doesn't exist
                admin = auth.ensure_admin_exists(db)
                print(f"Admin user confirmed: {admin.email}")

                # Create default roles if they don't exist
                roles.ensure_default_roles_exist(db)
                print("Default roles confirmed")
                return True
        else:
            # Use provided session (for testing)
            admin = auth.ensure_admin_exists(db_session)
            print(f"Admin user confirmed: {admin.email}")

            # Create default roles if they don't exist
            roles.ensure_default_roles_exist(db_session)
            print("Default roles confirmed")
            return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False


# Initialize database in production, but not in test environment
if os.getenv("TESTING") != "true":
    init_db()


@app.get("/")
def home(request: Request, db: Session = Depends(database.get_db)):
    # Get current user from token cookie if available
    access_token = request.cookies.get("access_token")
    current_user = None
    books = []

    books_by_status = {}
    if access_token:
        # Token is stored without Bearer prefix
        try:
            current_user = auth.get_optional_current_user_sync(access_token, db)
            if current_user:
                # Get all user's books grouped by status
                books = (
                    db.query(models.Book)
                    .filter(models.Book.user_id == current_user.id)
                    .order_by(models.Book.updated_at.desc())
                    .all()
                )

                # Group books by status
                for status in models.BookStatus:
                    status_books = [b for b in books if b.status == status]
                    if status_books:
                        books_by_status[status] = status_books
        except Exception as e:
            # Invalid token, ignore and proceed as anonymous user
            print(f"Authentication error: {e}")
            pass

    theme, current_theme = get_current_theme(request)
    context = {
        "request": request,
        "theme": theme,
        "current_theme": current_theme,
        "user": current_user,
        "books_by_status": books_by_status,
        "book_statuses": list(models.BookStatus),
    }

    response = templates.TemplateResponse("index.html", context)
    set_theme_cookie(response, current_theme)
    return response


@app.get("/settings")
def settings_page(
    request: Request,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_optional_current_user),
):
    theme, current_theme = get_current_theme(request)
    # Create a dict of theme names and their colors
    theme_previews = {name: colors for name, colors in themes.THEMES.items()}
    # Sort themes alphabetically for consistent display
    theme_previews = dict(sorted(theme_previews.items()))

    response = templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "user": current_user,
            "theme_previews": theme_previews,
            "current_theme": current_theme,
            "theme": theme,
        },
    )
    set_theme_cookie(response, current_theme)
    return response


@app.post("/settings/theme")
def update_theme(
    request: Request,
    theme_name: str = Form(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_optional_current_user),
):
    if theme_name not in themes.THEMES:
        raise HTTPException(status_code=400, detail="Invalid theme")

    # Update user's theme preference if logged in
    if current_user:
        current_user.theme_preference = theme_name
        db.commit()

    # Create response with theme cookie
    response = HTMLResponse("", status_code=200)
    set_theme_cookie(response, theme_name)

    # Add HTMX headers for client-side updates
    response.headers["HX-Trigger"] = "themeChanged"
    response.headers["HX-Trigger-After-Settle"] = json.dumps(
        {"showMessage": "Theme updated successfully"}
    )

    return response


# JSON API endpoints
@app.get("/api/theme/{theme_name}", response_model=ThemeColors)
def get_theme_colors(theme_name: str):
    theme = themes.get_theme(theme_name)
    if not theme:
        raise HTTPException(status_code=404, detail=f"Theme '{theme_name}' not found")
    return theme
