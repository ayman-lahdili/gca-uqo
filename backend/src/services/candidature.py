from sqlmodel import Session, select
from fastapi.responses import FileResponse

from src.schemas import Etudiant, Candidature
from src.models.requests import CandidatureForm
from src.file import StorageProvider
from src.exceptions import StorageError, FileDeleteError, ResumeNotFoundError


class CandidatureService:
    def __init__(
        self, trimestre: int, *, session: Session, storage: StorageProvider
    ) -> None:
        self._trimestre = trimestre
        self._session = session
        self._storage = storage

    async def add_candidature(self, form: CandidatureForm) -> Etudiant:
        new_etudiant = Etudiant(
            code_permanent=form.code_permanent,
            email=form.email,
            nom=form.nom,
            prenom=form.prenom,
            cycle=form.cycle,
            campus=form.campus,
            programme=form.programme,
            trimestre=self._trimestre,
        )
        self._session.add(new_etudiant)
        self._session.flush()

        assert new_etudiant.id is not None, (
            "Student ID should not be None after commit."
        )

        for course in form.courses:
            candidature = Candidature(
                id_etudiant=new_etudiant.id,
                sigle=course.sigle,
                titre=course.titre,
                trimestre=self._trimestre,
                note=course.note,
            )
            self._session.add(candidature)

        self._session.flush()

        if form.resume:
            try:
                self._storage.save_file(new_etudiant.get_file_name, form.resume)
            except Exception as e:
                self._session.rollback()
                raise StorageError(e)
            finally:
                await form.resume.close()

        self._session.commit()
        self._session.refresh(new_etudiant)

        return new_etudiant

    async def update_candidature(self, etudiant: Etudiant, form: CandidatureForm):
        if form.nom:
            etudiant.nom = form.nom
        if form.prenom:
            etudiant.prenom = form.prenom
        if form.cycle:
            etudiant.cycle = form.cycle
        if form.email:
            etudiant.email = form.email
        if form.campus:
            etudiant.campus = form.campus
        if form.programme:
            etudiant.programme = form.programme

        self._session.add(etudiant)
        self._session.flush()

        assert etudiant.id is not None, "Student ID should not be None after commit."

        if form.courses is not None:
            existing_candidatures = etudiant.candidature

            existing_sigles = {c.sigle for c in existing_candidatures}
            new_sigles = {course.sigle for course in form.courses}
            sigles_to_add = new_sigles - existing_sigles
            sigles_to_remove = existing_sigles - new_sigles

            for course in existing_candidatures:
                if course.sigle in sigles_to_remove:
                    self._session.delete(course)
                else:
                    course.note = [c for c in form.courses if c.sigle == course.sigle][
                        0
                    ].note

                processed_cours = set()
                for cours in form.courses:
                    if cours.sigle in processed_cours:
                        continue
                    if cours.sigle in sigles_to_add:
                        candidature = Candidature(
                            id_etudiant=etudiant.id,
                            sigle=cours.sigle,
                            titre=cours.titre,
                            trimestre=self._trimestre,
                            note=cours.note,
                        )
                        self._session.add(candidature)

            self._session.flush()

        if form.resume:
            try:
                self._storage.save_file(etudiant.get_file_name, form.resume)
            except Exception as e:
                self._session.rollback()
                raise StorageError(e)
            finally:
                await form.resume.close()

        self._session.commit()
        self._session.refresh(etudiant, attribute_names=["candidature"])

        return etudiant

    async def get_resume(self, etudiant: Etudiant) -> FileResponse:
        try:
            return self._storage.read_file(etudiant.get_file_name)
        except FileNotFoundError:
            raise ResumeNotFoundError()

    async def get_all_candidature(self) -> list[Etudiant]:
        return list(
            self._session.exec(
                select(Etudiant).where(Etudiant.trimestre == self._trimestre)
            ).all()
        )

    async def remove_candidature(self, etudiant: Etudiant) -> None:
        try:
            self._storage.delete_file(etudiant.get_file_name)
        except Exception:
            raise FileDeleteError

        self._session.delete(etudiant)
        self._session.commit()
