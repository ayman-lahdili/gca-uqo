from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Request, Path, HTTPException
from sqlmodel import Session

from src.core.db import engine
from src.core.uqo import UQOHoraireService
from src.core.file import StorageProvider, LocalStorageProvider


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]


async def get_horaire_service(
    trimestre: Annotated[int, Path()], request: Request
) -> UQOHoraireService:
    # If trimestre is not provided as a path parameter, try to get it from the request
    if trimestre is None and request is not None:
        # Extract trimestre from the path parameters
        path_params = request.path_params
        if "trimestre" in path_params:
            trimestre = int(path_params["trimestre"])
        else:
            raise HTTPException(
                status_code=400, detail="Trimestre not found in path parameters."
            )

    # Create and return the service
    return UQOHoraireService(trimestre=trimestre)


HoraireDep = Annotated[UQOHoraireService, Depends(get_horaire_service)]


async def get_storage_provider() -> StorageProvider:
    return LocalStorageProvider("./uploaded_resumes")


StorageDep = Annotated[StorageProvider, Depends(get_storage_provider)]
