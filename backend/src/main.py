from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.handlers import campagnes, candidature, cours, uqo
from src.config import Settings, settings
from src.dependencies.context import context_dependency
from src.dependencies.session import db_session_dependency
from src.dependencies.http_client import http_client_dependency


def create_app(settings: Settings):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        await context_dependency.initialize(settings)
        await db_session_dependency.initialize(
            settings.SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False}
        )

        yield

        await http_client_dependency.aclose()
        await db_session_dependency.aclose()
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


app = create_app(settings)
