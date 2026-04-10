"""NetSight WebSocket handlers.

Exports the FastAPI APIRouter containing all WebSocket endpoints so that
the application server can mount them at the appropriate prefix.
"""

from __future__ import annotations

from .handlers import router

__all__ = ["router"]
