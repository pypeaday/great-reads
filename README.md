# Great Reads

A book tracking application that helps readers never lose track of their books.

## Self-Hosting Instructions

### Quick Start (Docker | Recommended)

1. Clone the repository:
```bash
git clone https://github.com/pypeaday/great-reads.git
cd great-reads
```

2. Copy the example environment file and configure it:
```bash
cp .env.example .env
```

You only need to change 3 things:

```
# JWT configuration
JWT_SECRET_KEY=dev_secret_key_change_in_production

# Admin user configuration
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123
```

3. Build and run the application:
```bash
docker compose up --build
```

Visit `http://localhost:8000` to see your application running.

### Quick Start (Python)

1. Clone the repository:
```bash
git clone https://github.com/pypeaday/great-reads.git
cd great-reads
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e "."
```

4. Copy the example environment file and configure it:
```bash
cp .env.example .env
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

Visit `http://localhost:8000` to see your application running.

### Demo User

A demo user with sample books is automatically created when you first run the application. You can log in with these credentials:

- **Email**: demo@example.com
- **Password**: demo

## Features

- **Book Tracking**: Add, update, and organize your reading collection
- **Reading Status**: Track books as "want to read", "currently reading", or "finished"
- **Notes & Ratings**: Add personal notes and ratings for each book
- **FastAPI Backend**: High-performance Python web framework
- **HTMX Integration**: Modern interactivity without complex JavaScript
- **SQLite Database**: Simple, file-based database with SQLAlchemy ORM
- **User Authentication**: Email/password authentication with JWT tokens
- **Theme Support**: Dark/light theme switching

## Environment Variables

Configure these variables in your `.env` file:

- `DATABASE_URL`: SQLite database URL (default: sqlite:///./app.db)
- `JWT_SECRET_KEY`: Secret key for JWT token generation
- `ADMIN_EMAIL`: Default admin user email
- `ADMIN_PASSWORD`: Default admin user password
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `ENVIRONMENT`: Development or production mode

## Developer Information

### Project Structure

```
.
├── app/                  # Application source code
│   ├── __init__.py
│   ├── main.py          # FastAPI application setup
│   ├── database.py      # Database configuration
│   ├── models.py        # SQLAlchemy models
│   ├── auth.py          # Authentication logic
│   ├── htmx.py          # HTMX utility functions
│   ├── static/          # Static assets
│   └── templates/       # HTML templates
├── migrations/          # Database migrations
└── tests/               # Test suite
```

### Development Setup

For development, install the development dependencies:

```bash
pip install -e ".[dev]"
```

#### Adding New Routes

1. Create a new route file in the `app` directory
2. Define your routes using FastAPI's router
3. Include the router in `main.py`

Example:
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/my-route")
def my_route():
    return {"message": "Hello"}
```

### Production Deployment

Before deploying to production:

1. Set a secure `JWT_SECRET_KEY`
2. Change default admin credentials
3. Set `ENVIRONMENT=production`
4. Configure proper CORS settings
5. Enable HTTPS
6. Set appropriate cookie security flags

## License

This project is licensed under the MIT License - see the LICENSE file for details.
