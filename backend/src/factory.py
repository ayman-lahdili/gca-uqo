from dataclasses import dataclass
from sqlmodel import Session

from typing import Self
from src.config import Settings

from src.schemas.uqo import UQOCours, UQOProgramme
from src.services.uqo import UQOCoursService, UQOProgrammeService, UQOHoraireService
from src.cache import UQOCache

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
    uqo_cours_cache: UQOCache[list[UQOCours]]

    @classmethod
    async def from_config(cls, settings: Settings) -> Self:
        return cls(
            settings=settings,
            uqo_cours_cache=UQOCache(list[UQOCours]),
        )
    
    async def aclose(self) -> None:
        """Clean up a process context.

        Called during shutdown, or before recreating the process context using
        a different configuration.
        """
        await self.uqo_cours_cache.clear()


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

    def __init__(
        self,
        context: ProcessContext,
        session: Session,
    ) -> None:
        self.session = session
        self._context = context
    
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
        )
    
    def create_uqo_programme_service(self) -> UQOProgrammeService:
        return UQOProgrammeService()

    def create_uqo_horaire_service(self, trimestre: int) -> UQOHoraireService:
        return UQOHoraireService(trimestre)
    