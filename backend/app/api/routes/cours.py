from typing import Any, List, Dict
import zipfile
import io
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import select
from pydantic import BaseModel

from app.api.deps import SessionDep, HoraireDep
from app.models import Campagne, Cours, Seance, Activite, Etudiant, Candidature
from app.schemas.enums import CoursStatus, ChangeType, Campus
from app.schemas.read import CampagneFullRead, CampagneRead, CampagneStatus, CoursFullRead

from app.core.diffs import CoursDiffer

router = APIRouter(prefix="/cours", tags=["campagne"])

# --- Configuration ---
UPLOAD_DIRECTORY = Path("./uploaded_resumes") # Directory to store uploaded files
Path(UPLOAD_DIRECTORY).mkdir(parents=True, exist_ok=True) # Create dir if it doesn't exist

class CandidaturePayload(BaseModel):
    code_permanent: str
    nom: str
    prenom: str
    cycle: int
    campus: str = ""
    programme: str = ""
    email: str = ""

@router.post('/{trimestre}/{sigle}/candidature', response_model=CoursFullRead)
def add_candidature_to_cours(trimestre: int, sigle: str, payload: CandidaturePayload, session: SessionDep):
    cours = session.exec(select(Cours).where((Cours.trimestre == trimestre) & (Cours.sigle == sigle))).first()

    if not cours:
        raise HTTPException(status_code=404, detail="Cours not found")

    student = session.exec(
        select(Etudiant).where(Etudiant.code_permanent == payload.code_permanent and Etudiant.trimestre == trimestre)
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

    candidature =  session.exec(select(Candidature).where((Candidature.sigle == sigle) & (Candidature.trimestre == trimestre) & (Candidature.id_etudiant == student.id))).first()

    if candidature:
        raise HTTPException(status_code=404, detail="Une candidature existe déjà pour ce candidat")
    
    candidature = Candidature(
        id_etudiant=student.id,
        sigle=sigle,
        trimestre=trimestre,
    )

    session.add(candidature)
    session.commit()
    session.refresh(cours, attribute_names=['candidature'])

    return cours


@router.post("/{trimestre}/{sigle}/resumes", response_class=StreamingResponse)
async def download_multiple_resumes(trimestre: int, sigle: str, session: SessionDep):
    """
    Creates a zip file containing all resumes for the given student IDs and trimester.
    """
    print("Downloading resumes...")
    cours = session.exec(select(Cours).where((Cours.trimestre == trimestre) & (Cours.sigle == sigle))).first()

    if not cours:
        raise HTTPException(status_code=404, detail="Cours not found")

    students = [c.etudiant for c in cours.candidature]

    # Validate that all students exist
    if not students:
        raise HTTPException(
            status_code=400,
            detail="Aucun étudiant trouvé pour le cours donné."
        )
    
    # Create an in-memory zip file
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add each student's resume to the zip file
        for student in students:
            # Find the resume file
            file_pattern = f"{student.id}_{trimestre}_resume.*"
            found_files = list(UPLOAD_DIRECTORY.glob(file_pattern))
            
            if not found_files:
                # Skip students with no resume file, or optionally raise an error
                continue
            
            resume_path = found_files[0]
            
            # Format student name for the zip filename
            safe_name = f"{student.nom}_{student.prenom}".replace(" ", "_")
            
            # Add file to zip with a descriptive name
            file_extension = resume_path.suffix
            zip_filename = f"{safe_name}_{student.code_permanent}{file_extension}"
            
            # Read the file and add it to the zip
            zip_file.write(resume_path, arcname=zip_filename)
    
    # Reset the buffer position to the beginning
    zip_buffer.seek(0)
    
    # Return the zip file as a streaming response
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=resumes_{trimestre}.zip"
        }
    )