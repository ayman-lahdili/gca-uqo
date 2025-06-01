from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request
from sqlmodel import Session
from structlog import BoundLogger

from src.factory import Factory, ProcessContext
from src.config import Settings
from src.dependencies.session import db_session_dependency
from src.dependencies.logger import logger_dependency


@dataclass(slots=True)
class RequestContext:
    """Holds the incoming request and its surrounding context.

    The primary reason for the existence of this class is to allow the
    functions involved in request processing to repeated rebind the request
    logger to include more information, without having to pass both the
    request and the logger separately to every function.
    """

    request: Request
    """The incoming request."""

    session: Session
    """The database session."""

    logger: BoundLogger
    """The request logger, rebound with discovered context."""

    factory: Factory
    """The component factory."""


class ContextDependency:
    """Provide a per-request context as a FastAPI dependency.

    Each request gets a `RequestContext`.  To save overhead, the portions of
    the context that are shared by all requests are collected into the single
    process-global `~factory.ProcessContext` and reused with each
    request.
    """

    def __init__(self) -> None:
        self._settings: Settings | None = None
        self._process_context: ProcessContext | None = None

    async def __call__(
        self,
        *,
        request: Request,
        session: Annotated[Session, Depends(db_session_dependency)],
        logger: Annotated[BoundLogger, Depends(logger_dependency)],
    ) -> RequestContext:
        if not self._settings or not self._process_context:
            raise RuntimeError("ContextDependency not initialized")
        return RequestContext(
            request=request,
            session=session,
            logger=logger,
            factory=Factory(self._process_context, session, logger),
        )

    async def aclose(self) -> None:
        """Clean up the per-process configuration.

        This also invalidates the events publishers until `initialize` is
        called again.
        """
        if self._process_context:
            await self._process_context.aclose()
        self._settings = None
        self._process_context = None

    async def initialize(self, settings: Settings) -> None:
        if self._process_context:
            await self._process_context.aclose()
        self._settings = settings
        self._process_context = await ProcessContext.from_settings(settings)


context_dependency = ContextDependency()
Context = Annotated[RequestContext, Depends(context_dependency)]
"""The dependency that will return the per-request context."""
