from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.handlers import campagnes, candidature, cours, uqo
from src.config import settings
from src.dependencies.context import context_dependency


def create_app():
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        await context_dependency.initialize(settings)
        yield
        await context_dependency.aclose()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
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
