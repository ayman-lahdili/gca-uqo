from sqlmodel import Session, select

from src.schemas import Cours
from src.models.responses import ApprovalResponse, ChangeInfo, ChangeType


class CoursService:
    def __init__(
        self,
        trimestre: int,
        *,
        session: Session,
    ) -> None:
        self._trimestre = trimestre
        self._session = session

    async def get_course(self, sigle: str) -> Cours | None:
        return self._session.exec(
            select(Cours).where(
                (Cours.trimestre == self._trimestre) & (Cours.sigle == sigle)
            )
        ).first()

    async def approve_changes(self, cours: Cours) -> ApprovalResponse:
        approved_change = ChangeInfo(**cours.change)

        if approved_change.change_type == ChangeType.MODIFIED:
            for field, value in approved_change.value.items():
                setattr(cours, field, value["new"])

            cours.change["change_type"] = ChangeType.UNCHANGED
            cours.change["value"] = {}

            self._session.add(cours)

        self._session.commit()

        return ApprovalResponse(
            entity=cours.model_dump(), change=approved_change, approved=True
        )
