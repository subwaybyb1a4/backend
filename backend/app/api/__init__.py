from app.api.routes import router as routes_router
from app.api.crowding import router as crowding_router
from app.api.explain import router as explain_router
from app.api.favorites import router as favorites_router

__all__ = [
    "routes_router",
    "crowding_router",
    "explain_router",
    "favorites_router",
]
