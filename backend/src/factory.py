from dataclasses import dataclass
from sqlmodel import Session

from typing import Self
from src.config import Settings

from src.services.uqo import UQOCoursService, UQOProgrammeService 

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

    @classmethod
    async def from_config(cls, settings: Settings) -> Self:
        return cls(
            settings=settings
        )
    
    async def aclose(self) -> None:
        """Clean up a process context.

        Called during shutdown, or before recreating the process context using
        a different configuration.
        """
        pass


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
        return UQOCoursService()
    
    def create_uqo_programme_service(self) -> UQOProgrammeService:
        return UQOProgrammeService()
    