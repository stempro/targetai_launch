"""Counselor repository for data access."""
import logging
from typing import Optional
from uuid import uuid4

from models.counselor import Counselor, PipelineStage, Specialization
from storage.blob_client import BlobStorageClient

logger = logging.getLogger(__name__)


class CounselorIndex:
    """Index of all counselor IDs."""
    counselors: list[str]


class CounselorRepository:
    """Repository for counselor data access."""

    def __init__(self, storage_client: BlobStorageClient):
        """Initialize repository.

        Args:
            storage_client: Azure Blob Storage client
        """
        self.storage = storage_client
        self.index_path = "counselors/index.json"

    async def get_by_id(self, counselor_id: str) -> Optional[Counselor]:
        """Get counselor by ID.

        Args:
            counselor_id: Unique counselor identifier

        Returns:
            Counselor instance or None if not found
        """
        path = f"counselors/{counselor_id}.json"
        return await self.storage.read(path, Counselor)

    async def get_all(self) -> list[Counselor]:
        """Get all counselors.

        Returns:
            List of all counselor instances
        """
        # Read index
        index_data = await self.storage.read_raw(self.index_path)
        if not index_data:
            logger.debug("No counselor index found")
            return []

        counselor_ids = index_data.get("counselors", [])

        # Fetch all counselors
        counselors: list[Counselor] = []
        for cid in counselor_ids:
            counselor = await self.get_by_id(cid)
            if counselor:
                counselors.append(counselor)

        return counselors

    async def save(self, counselor: Counselor) -> Counselor:
        """Save or update counselor.

        Args:
            counselor: Counselor instance to save

        Returns:
            Saved counselor instance
        """
        # Generate ID if new
        if not counselor.id:
            counselor.id = f"counsel-{uuid4().hex[:8]}"

        # Save counselor document
        path = f"counselors/{counselor.id}.json"
        await self.storage.write(path, counselor, etag=counselor.etag)

        # Update index
        await self._update_index(counselor.id)

        logger.info(f"Saved counselor: {counselor.id}")
        return counselor

    async def delete(self, counselor_id: str) -> bool:
        """Delete counselor.

        Args:
            counselor_id: Counselor ID to delete

        Returns:
            True if deleted, False if not found
        """
        path = f"counselors/{counselor_id}.json"
        deleted = await self.storage.delete(path)

        if deleted:
            await self._remove_from_index(counselor_id)
            logger.info(f"Deleted counselor: {counselor_id}")

        return deleted

    async def search(
        self,
        min_score: Optional[int] = None,
        stage: Optional[PipelineStage] = None,
        specialization: Optional[list[Specialization]] = None,
        region: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> list[Counselor]:
        """Search counselors by criteria.

        Args:
            min_score: Minimum total score
            stage: Pipeline stage filter
            specialization: List of specializations to match
            region: Geographic region
            tags: Tags to match

        Returns:
            List of matching counselors
        """
        all_counselors = await self.get_all()
        results: list[Counselor] = []

        for counselor in all_counselors:
            # Apply filters
            if min_score and counselor.scoring.total_score < min_score:
                continue

            if stage and counselor.pipeline.stage != stage:
                continue

            if specialization and not any(
                s in counselor.metadata.specialization for s in specialization
            ):
                continue

            if region and counselor.metadata.region != region:
                continue

            if tags and not any(t in counselor.tags for t in tags):
                continue

            results.append(counselor)

        return results

    async def get_by_stage(self, stage: PipelineStage) -> list[Counselor]:
        """Get all counselors in a specific pipeline stage.

        Args:
            stage: Pipeline stage to filter by

        Returns:
            List of counselors in that stage
        """
        return await self.search(stage=stage)

    async def get_high_priority(self, min_score: int = 12) -> list[Counselor]:
        """Get high-priority counselors (score >= min_score).

        Args:
            min_score: Minimum score threshold (default: 12)

        Returns:
            List of high-priority counselors
        """
        return await self.search(min_score=min_score)

    async def count(self) -> int:
        """Count total counselors.

        Returns:
            Total number of counselors
        """
        index_data = await self.storage.read_raw(self.index_path)
        if not index_data:
            return 0
        return len(index_data.get("counselors", []))

    async def count_by_stage(self, stage: PipelineStage) -> int:
        """Count counselors in a specific stage.

        Args:
            stage: Pipeline stage to count

        Returns:
            Number of counselors in that stage
        """
        counselors = await self.get_by_stage(stage)
        return len(counselors)

    async def _update_index(self, counselor_id: str) -> None:
        """Add counselor ID to index if not already present.

        Args:
            counselor_id: ID to add to index
        """
        index_data = await self.storage.read_raw(self.index_path)
        if not index_data:
            index_data = {"counselors": []}

        if counselor_id not in index_data["counselors"]:
            index_data["counselors"].append(counselor_id)
            await self.storage.write_raw(self.index_path, index_data)
            logger.debug(f"Added {counselor_id} to index")

    async def _remove_from_index(self, counselor_id: str) -> None:
        """Remove counselor ID from index.

        Args:
            counselor_id: ID to remove from index
        """
        index_data = await self.storage.read_raw(self.index_path)
        if not index_data:
            return

        if counselor_id in index_data["counselors"]:
            index_data["counselors"].remove(counselor_id)
            await self.storage.write_raw(self.index_path, index_data)
            logger.debug(f"Removed {counselor_id} from index")
