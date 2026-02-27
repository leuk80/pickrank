"""
Vercel Python Serverless entry point.
Routes all /api/* requests to the FastAPI application via the Mangum ASGI adapter.
"""
import os
import sys

# Add the backend/ directory to sys.path so `app.*` imports resolve correctly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from mangum import Mangum  # noqa: E402

from app.main import app  # noqa: E402

handler = Mangum(app, lifespan="off")
