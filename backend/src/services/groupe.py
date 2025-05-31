from sqlmodel import Session, select

from src.schemas import Seance, Activite, Candidature
from src.models.requests import SeanceUpdateRequest
from src.models.responses import ApprovalResponse, ChangeInfo, ChangeType
from src.models.uqo import ActiviteStatus
from src.exceptions import ActiviteNotFoundError


class GroupeService:
    def __init__(
        self,
        trimestre: int,
        *,
        session: Session,
    ) -> None:
        self._trimestre = trimestre
        self._session = session

    async def get_groupe(self, *, sigle: str, groupe: str) -> Seance | None:
        return self._session.exec(
            select(Seance).where(
                Seance.trimestre == self._trimestre,
                Seance.sigle == sigle,
                Seance.groupe == groupe,
            )
        ).first()

    async def get_activite(self, *, activite_id: int) -> Activite | None:
        return self._session.exec(
            select(Activite).where(Activite.id == activite_id)
        ).first()

    async def approve_changes(self, seance: Seance) -> ApprovalResponse:
        approved_change = ChangeInfo(**seance.change)

        if approved_change.change_type == ChangeType.MODIFIED:
            for field, value in approved_change.value.items():
                setattr(seance, field, value["new"])

            seance.change["change_type"] = ChangeType.UNCHANGED
            seance.change["value"] = {}

            self._session.add(seance)

        if approved_change.change_type == ChangeType.ADDED:
            seance.change["change_type"] = ChangeType.UNCHANGED
            seance.change["value"] = {}

        if approved_change.change_type == ChangeType.REMOVED:
            self._session.delete(seance)

        self._session.commit()

        return ApprovalResponse(
            entity=seance.model_dump(), change=approved_change, approved=True
        )

    async def approve_changes_activite(self, activite: Activite) -> ApprovalResponse:
        approved_change = ChangeInfo(**activite.change)

        if approved_change.change_type == ChangeType.ADDED:
            activite.change["change_type"] = ChangeType.UNCHANGED
            activite.change["value"] = {}

        if approved_change.change_type == ChangeType.REMOVED:
            self._session.delete(activite)

        self._session.commit()

        return ApprovalResponse(
            entity=activite.model_dump(), change=approved_change, approved=True
        )

    async def update_groupe(
        self, *, groupe: Seance, payload: SeanceUpdateRequest
    ) -> Seance:
        for act in payload.activite:
            activite = await self.get_activite(activite_id=act.id)

            if not activite:
                raise ActiviteNotFoundError()
                raise HTTPException(status_code=404, detail="Activite not found")

            if act.candidature is not None:
                # Reset candidature
                activite.responsable = []
                self._session.add(activite)
                self._session.flush()

                # Assign new list from payload
                for candidature_id in act.candidature:
                    print("actact.candidature:", act.candidature)
                    candidature = self._session.exec(
                        select(Candidature).where(Candidature.id == candidature_id)
                    ).first()

                    if not candidature:
                        print("Candidature not found")
                        continue

                    activite.responsable.append(candidature)

                self._session.add(activite)
            if act.nombre_seance:
                activite.nombre_seance = act.nombre_seance
                self._session.add(activite)
            if act.status:
                activite.status = ActiviteStatus(act.status)

            self._session.refresh(activite, attribute_names=["responsable"])
        self._session.commit()
        self._session.refresh(groupe, attribute_names=["activite"])

        return groupe
