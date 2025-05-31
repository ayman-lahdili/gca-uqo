from typing import Any, List

from fastapi import APIRouter, HTTPException, Depends

from src.dependencies.context import Context
from src.dependencies.campagne import CurrentCampagne
from src.dependencies.cours import CurrentCourse
from src.dependencies.activite import CurrentActivite
from src.dependencies.groupe import CurrentGroupe, get_current_groupe

from src.models.responses import (
    CampagneFullResponse,
    CampagneResponse,
    SeanceResponse,
    CoursResponse,
    ApprovalResponse,
)
from src.models.requests import (
    CampagneCreateRequest,
    CampagneUpdateRequest,
    SeanceUpdateRequest,
)
from src.exceptions import CampagneTooAhead, ActiviteNotFoundError

router = APIRouter(tags=["campagne"])


@router.post(
    "/v1/campagne", 
    response_model=CampagneFullResponse,
)
async def create_campagne(
    *,
    payload: CampagneCreateRequest,
    context: Context,
) -> Any:
    campagne_service = context.factory.create_campagne_service()

    if campagne_service.get_campagne(payload.trimestre):
        raise HTTPException(
            status_code=404,
            detail=f"Campagne already exists for trimestre {payload.trimestre}",
        )
    
    try:
        campagne = await campagne_service.add_campagne(payload)
        return campagne
    except CampagneTooAhead:
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de créer une campagne pour le trimestre {payload.trimestre} car il est plus de 3 trimestres dans le futur.",
        )

@router.get(
    "/v1/campagne", 
    response_model=List[CampagneResponse]
)
async def get_campagnes(
    *,
    context: Context
) -> Any:
    campagne_service = context.factory.create_campagne_service()
    return await campagne_service.get_campagne_list()


@router.get(
    "/v1/campagne/{trimestre}", 
    response_model=CampagneFullResponse
)
def get_campagne_by_trimestre(
    *,
    campagne: CurrentCampagne,
) -> Any:
    return campagne


@router.get("/v1/campagne/{trimestre}/cours", response_model=List[CoursResponse])
def get_cours_by_trimestre(
    *,
    campagne: CurrentCampagne,
) -> Any:
    return campagne.cours


@router.put("/v1/campagne/{trimestre}", response_model=CampagneFullResponse)
async def update_campagne(
    *,
    campagne: CurrentCampagne,
    payload: CampagneUpdateRequest,
    context: Context,
) -> Any:
    campagne_service = context.factory.create_campagne_service()
    try:
        return await campagne_service.update_campagne(campagne, payload)
    except ValueError:
        raise HTTPException(status_code=400, detail="Configuration de campagne invalide")


@router.post("/v1/campagne/{trimestre}/sync", response_model=CampagneFullResponse)
async def sync_campagne(
    trimestre: int,
    campagne: CurrentCampagne,
    context: Context,
) -> Any:
    uqo_service = context.factory.create_uqo_horaire_service(trimestre=trimestre)
    return await uqo_service.sync_courses(campagne)


@router.patch(
    "/v1/campagne/{trimestre}/{sigle}/changes/approve", response_model=ApprovalResponse
)
async def approve_course(
    *,
    trimestre: int,
    cours: CurrentCourse, 
    context: Context
):
    cours_service = context.factory.create_cours_service(trimestre)
    return await cours_service.approve_changes(cours)


@router.patch(
    "/v1/campagne/{trimestre}/{sigle}/{groupe}/changes/approve",
    response_model=ApprovalResponse,
)
async def approve_seance(
    *,
    trimestre: int, 
    groupe: CurrentGroupe,
    context: Context
):
    groupe_service = context.factory.create_groupe_service(trimestre)
    return await groupe_service.approve_changes(groupe)


@router.patch(
    "/v1/campagne/{trimestre}/{sigle}/{groupe}/{activite_id}/changes/approve",
    response_model=ApprovalResponse,
    dependencies=[
        Depends(get_current_groupe)
    ]
)
async def approve_activite(
    *, 
    trimestre: int, 
    activite: CurrentActivite, 
    context: Context
):
    groupe_service = context.factory.create_groupe_service(trimestre)
    return await groupe_service.approve_changes_activite(activite)


@router.put("/v1/campagne/{trimestre}/{sigle}/{groupe}", response_model=SeanceResponse)
async def modify_activity(
    *,
    trimestre: int,
    groupe: CurrentGroupe,
    payload: SeanceUpdateRequest,
    context: Context,
):
    try:
        groupe_service = context.factory.create_groupe_service(trimestre)
        return await groupe_service.update_groupe(groupe=groupe, payload=payload)
    except ActiviteNotFoundError:
        raise HTTPException(status_code=404, detail="Activite introuvable")
