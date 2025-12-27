"""WSGI entrypoint for production servers (e.g., gunicorn)."""

from app_pwa import app

__all__ = ["app"]
