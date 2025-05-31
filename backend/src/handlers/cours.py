from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import select
from pydantic import BaseModel

from src.dependencies.session import SessionDep, StorageDep
from src.schemas import Cours, Etudiant, Candidature
from src.models.uqo import Campus
from src.models.responses import (
    CoursFullResponse,
)

router = APIRouter(tags=["cours"])


class CandidaturePayload(BaseModel):
    code_permanent: str
    nom: str
    prenom: str
    cycle: int
    campus: str = ""
    programme: str = ""
    email: str = ""


@router.post(
    "/v1/cours/{trimestre}/{sigle}/candidature", response_model=CoursFullResponse
)
def add_candidature_to_cours(
    trimestre: int, sigle: str, payload: CandidaturePayload, session: SessionDep
):
    cours = session.exec(
        select(Cours).where((Cours.trimestre == trimestre) & (Cours.sigle == sigle))
    ).first()

    if not cours:
        raise HTTPException(status_code=404, detail="Cours not found")

    student = session.exec(
        select(Etudiant).where(
            (Etudiant.code_permanent == payload.code_permanent)
            & (Etudiant.trimestre == trimestre)
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
            campus=Campus(payload.campus) if payload.campus else Campus.non_specifie,
            programme=payload.programme,
            trimestre=trimestre,
        )
        session.add(student)
        session.commit()
        session.refresh(student)

    assert student.id is not None, "Student ID should not be None after commit."

    candidature = session.exec(
        select(Candidature).where(
            (Candidature.sigle == sigle)
            & (Candidature.trimestre == trimestre)
            & (Candidature.id_etudiant == student.id)
        )
    ).first()

    if candidature:
        raise HTTPException(
            status_code=404, detail="Une candidature existe déjà pour ce candidat"
        )

    candidature = Candidature(
        id_etudiant=student.id,
        sigle=sigle,
        trimestre=trimestre,
    )

    session.add(candidature)
    session.commit()
    session.refresh(cours, attribute_names=["candidature"])

    return cours


@router.post("/v1/cours/{trimestre}/{sigle}/resumes", response_class=StreamingResponse)
async def download_multiple_resumes(
    trimestre: int, sigle: str, session: SessionDep, storage: StorageDep
):
    """
    Creates a zip file containing all resumes for the given student IDs and trimester.
    """
    print("Downloading resumes...")
    cours = session.exec(
        select(Cours).where((Cours.trimestre == trimestre) & (Cours.sigle == sigle))
    ).first()

    if not cours:
        raise HTTPException(status_code=404, detail="Cours not found")

    filenames = [c.etudiant.get_file_name for c in cours.candidature]

    # Validate that all students exist
    if not filenames:
        raise HTTPException(
            status_code=400, detail="Aucun étudiant trouvé pour le cours donné."
        )

    return storage.zip_files("resumes_{trimestre}", filenames)
