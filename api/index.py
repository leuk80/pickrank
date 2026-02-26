"""
Vercel Python Serverless entry point.
Routes all /api/* requests to the FastAPI application via the Mangum ASGI adapter.
"""
import os
import sys

# Make the backend package importable from this file's parent directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mangum import Mangum

from backend.app.main import app  # noqa: E402

handler = Mangum(app, lifespan="off")
