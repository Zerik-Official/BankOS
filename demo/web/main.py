"""Demo web entrypoint: the Jinja frontend served next to the BankOS API.

Run from the repository root:

    python -m uvicorn demo.web.main:app --port 8000
"""

# Standard library
from pathlib import Path

# Third-party
from fastapi.staticfiles import StaticFiles

# Project imports
from app.main import create_app
from demo.web.auth import LoginRequiredError, redirect_to_login
from demo.web.routes import router as web_router

WEB_DIR = Path(__file__).resolve().parent

app = create_app()
# The demo owns the root path for its landing page, so the API index moves out of the way.
app.router.routes[:] = [route for route in app.router.routes if getattr(route, "path", None) != "/"]
app.include_router(web_router)
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
app.add_exception_handler(LoginRequiredError, redirect_to_login)
