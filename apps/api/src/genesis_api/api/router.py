from fastapi import APIRouter

from genesis_api.api.routes.auth import router as auth_router
from genesis_api.api.routes.health import router as health_router
from genesis_api.api.routes.release import router as release_router
from genesis_api.api.routes.simulation import router as simulation_router
from genesis_api.api.routes.worlds import router as worlds_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(release_router)
api_router.include_router(worlds_router)
api_router.include_router(simulation_router)
