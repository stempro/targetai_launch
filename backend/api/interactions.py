"""Interaction API routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from dependencies import get_interaction_repository
from models.interaction import Interaction, InteractionType
from repositories.interaction_repository import InteractionRepository

router = APIRouter()


@router.get("/{interaction_id}", response_model=Interaction)
async def get_interaction(
    interaction_id: str,
    repo: InteractionRepository = Depends(get_interaction_repository),
):
    """Get interaction by ID."""
    interaction = await repo.get_by_id(interaction_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@router.get("/counselor/{counselor_id}", response_model=list[Interaction])
async def get_counselor_interactions(
    counselor_id: str,
    repo: InteractionRepository = Depends(get_interaction_repository),
):
    """Get all interactions for a counselor."""
    return await repo.get_by_counselor(counselor_id)


@router.post("/", response_model=Interaction, status_code=201)
async def create_interaction(
    interaction: Interaction,
    repo: InteractionRepository = Depends(get_interaction_repository),
):
    """Create new interaction."""
    return await repo.save(interaction)


@router.get("/recent/all", response_model=list[Interaction])
async def get_recent_interactions(
    limit: int = 50,
    repo: InteractionRepository = Depends(get_interaction_repository),
):
    """Get recent interactions across all counselors."""
    return await repo.get_recent(limit=limit)


@router.get("/filter/by-type/{interaction_type}", response_model=list[Interaction])
async def get_interactions_by_type(
    interaction_type: InteractionType,
    counselor_id: Optional[str] = None,
    repo: InteractionRepository = Depends(get_interaction_repository),
):
    """Get interactions by type."""
    return await repo.get_by_type(interaction_type, counselor_id=counselor_id)
