from structlog import BoundLogger
from sqlmodel import Session, select
from fastapi.responses import FileResponse, StreamingResponse

from src.schemas import Etudiant, Candidature, Cours
from src.models.requests import CandidatureForm, CandidaturePayload
from src.models.uqo import Campus

from src.file import StorageProvider
from src.exceptions import (
    StorageError,
    FileDeleteError,
    ResumeNotFoundError,
    CandidatureExistsError,
    NoStudentsFoundError,
)


class CandidatureService:
    def __init__(
        self,
        trimestre: int,
        *,
        session: Session,
        storage: StorageProvider,
        logger: BoundLogger,
    ) -> None:
        self._trimestre = trimestre
        self._session = session
        self._storage = storage
        self._logger = logger

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

    async def get_resumes_for_course(self, cours: Cours) -> StreamingResponse:
        filenames = [c.etudiant.get_file_name for c in cours.candidature]
        if not filenames:
            raise NoStudentsFoundError()

        return self._storage.zip_files(f"resumes_{self._trimestre}", filenames)

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

    async def add_candidature_to_cours(
        self, *, cours: Cours, payload: CandidaturePayload
    ):
        student = self._session.exec(
            select(Etudiant).where(
                (Etudiant.code_permanent == payload.code_permanent)
                & (Etudiant.trimestre == self._trimestre)
            )
        ).first()

        if not student:
            # Create a new student if not found
            student = Etudiant(
                code_permanent=payload.code_permanent,
                email=payload.email,
                nom=payload.nom,
                prenom=payload.prenom,
                cycle=payload.cycle,
                campus=Campus(payload.campus)
                if payload.campus
                else Campus.non_specifie,
                programme=payload.programme,
                trimestre=self._trimestre,
            )
            self._session.add(student)
            self._session.commit()
            self._session.refresh(student)

        assert student.id is not None, "Student ID should not be None after commit."

        candidature = self._session.exec(
            select(Candidature).where(
                (Candidature.sigle == cours.sigle)
                & (Candidature.trimestre == cours.trimestre)
                & (Candidature.id_etudiant == student.id)
            )
        ).first()

        if candidature:
            raise CandidatureExistsError()
            raise HTTPException(
                status_code=404, detail="Une candidature existe déjà pour ce candidat"
            )

        candidature = Candidature(
            id_etudiant=student.id,
            sigle=cours.sigle,
            trimestre=cours.trimestre,
        )

        self._session.add(candidature)
        self._session.commit()
        self._session.refresh(cours, attribute_names=["candidature"])

        return cours
