from sqlalchemy.ext.asyncio import async_scoped_session
from sqlmodel import Session, select

from src.schemas import Etudiant


class EtudiantService:
    def __init__(
        self,
        trimestre: int,
        *,
        session: Session,
    ) -> None:
        self._trimestre = trimestre
        self._session = session

    def get_etudiant(self, *, code_permanent: str, email: str) -> Etudiant | None:
        etudiant = self._session.exec(
            select(Etudiant).where(
                (
                    (Etudiant.code_permanent == code_permanent)
                    | (Etudiant.email == email)
                )
                & (Etudiant.trimestre == self._trimestre)
            )
        ).first()

        return etudiant

    def get_etudiant_by_id(self, id) -> Etudiant | None:
        return self._session.get(Etudiant, id)
