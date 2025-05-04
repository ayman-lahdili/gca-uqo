from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.handlers import campagnes, candidature, cours, uqo
from src.core.config import settings


def create_app():
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )
    app.include_router(campagnes.router)
    app.include_router(candidature.router)
    app.include_router(cours.router)
    app.include_router(uqo.router)

    if settings.all_cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.all_cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    return app

main = create_app()