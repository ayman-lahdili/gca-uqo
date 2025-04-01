from fastapi import APIRouter

from app.api.routes import campagnes

api_router = APIRouter()
api_router.include_router(campagnes.router)
