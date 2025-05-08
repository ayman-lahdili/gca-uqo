from sqlmodel import select
from sqlmodel import Session

from src.models import Campagne


class CampagneService:
    def __init__(
        self,
        *,
        session: Session,
    ) -> None:
        self._session = session

    def get_campagne(self, trimestre: int) -> Campagne | None:
        campagne = self._session.exec(
            select(Campagne).where(Campagne.trimestre == trimestre)
        ).first()
        return campagne
