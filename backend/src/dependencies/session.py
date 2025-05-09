from collections.abc import Generator
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import Engine
from sqlmodel import Session, create_engine

from src.providers.file import StorageProvider, LocalStorageProvider


async def get_storage_provider() -> StorageProvider:
    return LocalStorageProvider("./uploaded_resumes")
StorageDep = Annotated[StorageProvider, Depends(get_storage_provider)]

"""Database session dependency"""
class DatabaseSessionDependency:
    def __init__(self) -> None:
        self._engine: Engine | None = None

    def __call__(self) -> Generator[Session, None, None]:
        if not self._engine:
            raise RuntimeError("db_session_dependency not initialized")
        with Session(self._engine) as session:
            yield session

    async def aclose(self) -> None:
        """SHut down the database engine."""
        if self._engine:
            self._engine.dispose()
            self._engine = None

    async def initialize(
        self,
        url: str,
        password: str | None = None,
        *,
        connect_args: dict[str, Any] | None = None,
    ):
        if self._engine:
            self._engine.dispose()
        kwargs: dict[str, Any] = {}
        if connect_args:
            kwargs["connect_args"] = connect_args
        self._engine = create_engine(url, **kwargs)


db_session_dependency = DatabaseSessionDependency()
"""The dependency that will return the sync session proxy."""

SessionDep = Annotated[Session, Depends(db_session_dependency)]
