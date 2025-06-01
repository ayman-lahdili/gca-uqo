from typing import Self, Any
from dataclasses import dataclass

from httpx import AsyncClient
from sqlalchemy import Engine
from sqlmodel import Session
import structlog
from structlog import BoundLogger

from src.config import Settings

from src.models.uqo import UQOCours, UQOProgramme
from src.services.uqo import UQOCoursService, UQOProgrammeService, UQOHoraireService
from src.services import (
    CampagneService,
    EtudiantService,
    CandidatureService,
    CoursService,
    GroupeService,
)
from src.file import StorageProvider, LocalStorageProvider
from src.cache import AsyncCache

from src.dependencies.http_client import http_client_dependency


@dataclass(frozen=True, slots=True)
class ProcessContext:
    """Per-process application context.

    This object caches all of the per-process singletons that can be reused
    for every request and only need to be recreated if the application
    configuration changes.  This does not include the database session; each
    request creates a new scoped session that's removed at the end of the
    session to ensure that all transactions are committed or abandoned.
    """

    settings: Settings
    uqo_cours_cache: AsyncCache[list[UQOCours]]
    uqo_programme_cache: AsyncCache[list[UQOProgramme]]
    uqo_horaire_cache: AsyncCache[list[dict[str, Any]]]
    storage_provider: StorageProvider
    http_client: AsyncClient

    @classmethod
    async def from_settings(cls, settings: Settings) -> Self:
        return cls(
            settings=settings,
            uqo_cours_cache=AsyncCache(18000),
            uqo_programme_cache=AsyncCache(18000),
            uqo_horaire_cache=AsyncCache(18000),
            storage_provider=LocalStorageProvider(settings.STORAGE_DIRECTORY),
            http_client=await http_client_dependency(),
        )

    async def aclose(self) -> None:
        """Clean up a process context.

        Called during shutdown, or before recreating the process context using
        a different configuration.
        """
        await self.uqo_cours_cache.clear()
        await self.uqo_programme_cache.clear()


class Factory:
    """Build components.

    Uses the contents of a `ProcessContext` to construct the components of the
    application on demand.

    Parameters
    ----------
    context
        Shared process context.
    session
        Database session.
    """

    @classmethod
    async def create(cls, settings: Settings, engine: Engine) -> Self:
        logger = structlog.get_logger("gca-uqo")
        session = Session(engine)
        context = await ProcessContext.from_settings(settings)
        return cls(context, session, logger)

    def __init__(
        self, context: ProcessContext, session: Session, logger: BoundLogger
    ) -> None:
        self.session = session
        self._context = context
        self._logger = logger

    async def aclose(self) -> None:
        """Shut down the factory.

        After this method is called, the factory object is no longer valid and
        must not be used.
        """
        try:
            await self._context.aclose()
        finally:
            self.session.close()

    def create_uqo_course_service(self) -> UQOCoursService:
        return UQOCoursService(
            cours_cache=self._context.uqo_cours_cache,
            http_client=self._context.http_client,
            logger=self._logger,
        )

    def create_uqo_programme_service(self) -> UQOProgrammeService:
        return UQOProgrammeService(
            programme_cache=self._context.uqo_programme_cache,
            http_client=self._context.http_client,
            logger=self._logger,
        )

    def create_uqo_horaire_service(self, trimestre: int) -> UQOHoraireService:
        return UQOHoraireService(
            trimestre,
            horaire_cache=self._context.uqo_horaire_cache,
            session=self.session,
            http_client=self._context.http_client,
            logger=self._logger,
        )

    def create_campagne_service(self) -> CampagneService:
        return CampagneService(session=self.session, logger=self._logger)

    def create_etudiant_service(self, trimestre: int) -> EtudiantService:
        return EtudiantService(trimestre, session=self.session, logger=self._logger)

    def create_candidature_service(self, trimestre: int) -> CandidatureService:
        return CandidatureService(
            trimestre,
            session=self.session,
            storage=self._context.storage_provider,
            logger=self._logger,
        )

    def create_cours_service(self, trimestre: int) -> CoursService:
        return CoursService(trimestre, session=self.session, logger=self._logger)

    def create_groupe_service(self, trimestre: int) -> GroupeService:
        return GroupeService(trimestre, session=self.session, logger=self._logger)
