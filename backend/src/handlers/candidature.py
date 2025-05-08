from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse

from src.dependencies.campagne import get_current_campagne
from src.dependencies.etudiant import ensure_etudiant_does_not_exist, CurrentEtudiant
from src.dependencies.context import Context

from src.schemas.responses import EtudiantFullResponse, Message
from src.schemas.requests import CandidatureForm

from src.exceptions import StorageError, ResumeNotFoundError

router = APIRouter(tags=["candidature"])


@router.post(
    "/v1/{trimestre}/candidature/",
    response_model=EtudiantFullResponse,
    dependencies=[
        Depends(get_current_campagne),
        Depends(ensure_etudiant_does_not_exist),
    ],
)
async def create_candidature(
    context: Context,
    trimestre: int,
    form: CandidatureForm = Depends(),
):
    try:
        candidature_service = context.factory.create_candidature_service(trimestre)
        etudiant = await candidature_service.add_candidature(form)
        return etudiant
    except StorageError:
        raise HTTPException(
            status_code=500,
            detail="Une erreur s'est produite lors de l'enregistrement du fichier.",
        )


@router.get(
    "/v1/{trimestre}/candidature/{etudiant_id}/resume",
    response_class=FileResponse,
    dependencies=[
        Depends(get_current_campagne),
    ],
)
async def download_candidature_resume(
    etudiant_id: int,
    trimestre: int,
    current_etudiant: CurrentEtudiant,
    context: Context,
):
    try:
        candidature_service = context.factory.create_candidature_service(trimestre)
        return await candidature_service.get_resume(current_etudiant)
    except ResumeNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"CV introuvable pour l'étudiant {etudiant_id} pour le trimester {trimestre}.",
        )


@router.get(
    "/v1/{trimestre}/candidature/",
    response_model=list[EtudiantFullResponse],
    dependencies=[
        Depends(get_current_campagne),
    ],
)
async def get_candidatures(trimestre: int, context: Context):
    candidature_service = context.factory.create_candidature_service(trimestre)
    return await candidature_service.get_all_candidature()


@router.put(
    "/v1/{trimestre}/candidature/{etudiant_id}",
    response_model=EtudiantFullResponse,
    dependencies=[
        Depends(get_current_campagne),
    ],
)
async def update_student(
    context: Context,
    trimestre: int,
    current_etudiant: CurrentEtudiant,
    form: CandidatureForm = Depends(),
):
    try:
        candidature_service = context.factory.create_candidature_service(trimestre)
        return await candidature_service.update_candidature(current_etudiant, form)
    except StorageError:
        raise HTTPException(
            status_code=500,
            detail="Une erreur s'est produite lors de l'enregistrement du fichier.",
        )


@router.delete(
    "/v1/{trimestre}/candidature/{etudiant_id}",
    dependencies=[
        Depends(get_current_campagne),
    ],
)
async def delete_student(
    trimestre: int,
    current_etudiant: CurrentEtudiant,
    context: Context,
):
    candidature_service = context.factory.create_candidature_service(trimestre)
    await candidature_service.remove_candidature(current_etudiant)

    return Message(message="Student and associated candidatures deleted successfully.")
