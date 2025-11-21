"""
Routes Package

This package contains FastAPI route definitions:
- ingestion_routes: Document ingestion endpoints
- agent_routes: QA agent endpoints

"""

from backend.routes.ingestion_routes import router as ingestion_router
from backend.routes.agent_routes import router as agent_router

__all__ = [
    "ingestion_router",
    "agent_router",
]