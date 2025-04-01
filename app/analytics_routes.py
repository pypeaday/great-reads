"""Analytics routes for the book tracking app."""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from . import analytics
from . import auth
from . import models
from .database import get_db

# Get templates function
def get_templates(request: Request):
    """Get templates from app state."""
    return request.app.state.templates

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    responses={404: {"description": "Not found"}},
)





@router.get("/", response_class=HTMLResponse)
async def view_analytics(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """View analytics dashboard for the current user."""

    # Get reading stats
    stats = analytics.get_reading_stats(db, current_user.id)

    # Get monthly reading data for chart
    monthly_data = analytics.get_monthly_reading_data(db, current_user.id)
    
    # Get books timeline data
    books_timeline = analytics.get_books_timeline(db, current_user.id)

    templates = get_templates(request)
    return templates.TemplateResponse(
        "analytics/dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "stats": stats,
            "monthly_data": monthly_data,
            "books_timeline": books_timeline,
        },
    )
