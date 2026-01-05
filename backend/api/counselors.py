"""Counselor API routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from dependencies import get_counselor_repository
from models.counselor import Counselor, PipelineStage, Specialization
from repositories.counselor_repository import CounselorRepository

router = APIRouter()


@router.get("/", response_model=list[Counselor])
async def list_counselors(
    repo: CounselorRepository = Depends(get_counselor_repository),
):
    """Get all counselors."""
    return await repo.get_all()


@router.get("/{counselor_id}", response_model=Counselor)
async def get_counselor(
    counselor_id: str,
    repo: CounselorRepository = Depends(get_counselor_repository),
):
    """Get counselor by ID."""
    counselor = await repo.get_by_id(counselor_id)
    if not counselor:
        raise HTTPException(status_code=404, detail="Counselor not found")
    return counselor


@router.post("/", response_model=Counselor, status_code=201)
async def create_counselor(
    counselor: Counselor,
    repo: CounselorRepository = Depends(get_counselor_repository),
):
    """Create new counselor."""
    return await repo.save(counselor)


@router.put("/{counselor_id}", response_model=Counselor)
async def update_counselor(
    counselor_id: str,
    counselor: Counselor,
    repo: CounselorRepository = Depends(get_counselor_repository),
):
    """Update counselor."""
    existing = await repo.get_by_id(counselor_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Counselor not found")

    counselor.id = counselor_id
    return await repo.save(counselor)


@router.delete("/{counselor_id}", status_code=204)
async def delete_counselor(
    counselor_id: str,
    repo: CounselorRepository = Depends(get_counselor_repository),
):
    """Delete counselor."""
    deleted = await repo.delete(counselor_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Counselor not found")


@router.get("/search/by-criteria", response_model=list[Counselor])
async def search_counselors(
    min_score: Optional[int] = None,
    stage: Optional[PipelineStage] = None,
    region: Optional[str] = None,
    repo: CounselorRepository = Depends(get_counselor_repository),
):
    """Search counselors by criteria."""
    return await repo.search(
        min_score=min_score,
        stage=stage,
        region=region,
    )


@router.get("/filter/high-priority", response_model=list[Counselor])
async def get_high_priority_counselors(
    min_score: int = 12,
    repo: CounselorRepository = Depends(get_counselor_repository),
):
    """Get high-priority counselors."""
    return await repo.get_high_priority(min_score=min_score)


@router.get("/filter/by-stage/{stage}", response_model=list[Counselor])
async def get_counselors_by_stage(
    stage: PipelineStage,
    repo: CounselorRepository = Depends(get_counselor_repository),
):
    """Get counselors in a specific pipeline stage."""
    return await repo.get_by_stage(stage)


@router.get("/stats/pipeline", response_model=dict)
async def get_pipeline_stats(
    repo: CounselorRepository = Depends(get_counselor_repository),
):
    """Get counselor distribution across pipeline stages."""
    total = await repo.count()
    stats = {}

    for stage in PipelineStage:
        count = await repo.count_by_stage(stage)
        stats[stage.value] = count

    return {
        "total": total,
        "by_stage": stats,
    }
