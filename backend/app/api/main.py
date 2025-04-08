from fastapi import APIRouter

from app.api.routes import campagnes, candidature, cours, uqo

api_router = APIRouter()
api_router.include_router(campagnes.router)
api_router.include_router(candidature.router)
api_router.include_router(cours.router)
api_router.include_router(uqo.router)
