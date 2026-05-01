from .chat_routes import router as chat_router
from .indexing_routes import router as indexing_router
from .system_routes import router as system_router

__all__ = ["chat_router", "indexing_router", "system_router"]
