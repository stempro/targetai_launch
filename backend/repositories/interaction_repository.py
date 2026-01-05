"""Interaction repository for data access."""
import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from models.interaction import Interaction, InteractionType
from storage.blob_client import BlobStorageClient

logger = logging.getLogger(__name__)


class InteractionRepository:
    """Repository for interaction data access."""

    def __init__(self, storage_client: BlobStorageClient):
        """Initialize repository.

        Args:
            storage_client: Azure Blob Storage client
        """
        self.storage = storage_client

    async def get_by_id(self, interaction_id: str) -> Optional[Interaction]:
        """Get interaction by ID.

        Args:
            interaction_id: Unique interaction identifier

        Returns:
            Interaction instance or None if not found
        """
        # Find in global index first to get counselor_id
        global_index = await self.storage.read_raw("interactions/global-index.json")
        if not global_index:
            return None

        for item in global_index.get("interactions", []):
            if item["id"] == interaction_id:
                counselor_id = item["counselor_id"]
                path = f"interactions/{counselor_id}/{interaction_id}.json"
                return await self.storage.read(path, Interaction)

        return None

    async def get_by_counselor(self, counselor_id: str) -> list[Interaction]:
        """Get all interactions for a specific counselor.

        Args:
            counselor_id: Counselor ID

        Returns:
            List of interactions for that counselor
        """
        # Read counselor's interaction index
        index_path = f"interactions/{counselor_id}/index.json"
        index_data = await self.storage.read_raw(index_path)

        if not index_data:
            return []

        interaction_ids = index_data.get("interactions", [])

        # Fetch all interactions
        interactions: list[Interaction] = []
        for iid in interaction_ids:
            path = f"interactions/{counselor_id}/{iid}.json"
            interaction = await self.storage.read(path, Interaction)
            if interaction:
                interactions.append(interaction)

        # Sort by date descending (most recent first)
        interactions.sort(key=lambda x: x.date, reverse=True)
        return interactions

    async def save(self, interaction: Interaction) -> Interaction:
        """Save or update interaction.

        Args:
            interaction: Interaction instance to save

        Returns:
            Saved interaction instance
        """
        # Generate ID if new
        if not interaction.id:
            interaction.id = f"int-{uuid4().hex[:8]}"

        # Save interaction document
        path = f"interactions/{interaction.counselor_id}/{interaction.id}.json"
        await self.storage.write(path, interaction, etag=interaction.etag)

        # Update counselor index
        await self._update_counselor_index(interaction.counselor_id, interaction.id)

        # Update global index
        await self._update_global_index(interaction)

        logger.info(f"Saved interaction: {interaction.id} for counselor {interaction.counselor_id}")
        return interaction

    async def get_recent(self, limit: int = 50) -> list[Interaction]:
        """Get recent interactions across all counselors.

        Args:
            limit: Maximum number to return

        Returns:
            List of recent interactions
        """
        global_index = await self.storage.read_raw("interactions/global-index.json")
        if not global_index:
            return []

        # Global index should be sorted by date already
        interaction_refs = global_index.get("interactions", [])[:limit]

        interactions: list[Interaction] = []
        for ref in interaction_refs:
            path = f"interactions/{ref['counselor_id']}/{ref['id']}.json"
            interaction = await self.storage.read(path, Interaction)
            if interaction:
                interactions.append(interaction)

        return interactions

    async def get_by_type(
        self, interaction_type: InteractionType, counselor_id: Optional[str] = None
    ) -> list[Interaction]:
        """Get interactions by type.

        Args:
            interaction_type: Type of interaction
            counselor_id: Optional counselor ID to filter

        Returns:
            List of matching interactions
        """
        if counselor_id:
            all_interactions = await self.get_by_counselor(counselor_id)
        else:
            # Get from global index
            global_index = await self.storage.read_raw("interactions/global-index.json")
            if not global_index:
                return []

            all_interactions = []
            for ref in global_index.get("interactions", []):
                path = f"interactions/{ref['counselor_id']}/{ref['id']}.json"
                interaction = await self.storage.read(path, Interaction)
                if interaction:
                    all_interactions.append(interaction)

        return [i for i in all_interactions if i.type == interaction_type]

    async def count_by_type(
        self, interaction_type: InteractionType, since: Optional[datetime] = None
    ) -> int:
        """Count interactions of a specific type.

        Args:
            interaction_type: Type to count
            since: Optional datetime to count from

        Returns:
            Number of interactions matching criteria
        """
        interactions = await self.get_by_type(interaction_type)

        if since:
            interactions = [i for i in interactions if i.date >= since]

        return len(interactions)

    async def _update_counselor_index(self, counselor_id: str, interaction_id: str) -> None:
        """Add interaction ID to counselor's index.

        Args:
            counselor_id: Counselor ID
            interaction_id: Interaction ID to add
        """
        index_path = f"interactions/{counselor_id}/index.json"
        index_data = await self.storage.read_raw(index_path)

        if not index_data:
            index_data = {"counselor_id": counselor_id, "interactions": []}

        if interaction_id not in index_data["interactions"]:
            index_data["interactions"].append(interaction_id)
            await self.storage.write_raw(index_path, index_data)

    async def _update_global_index(self, interaction: Interaction) -> None:
        """Add interaction to global index.

        Args:
            interaction: Interaction to add
        """
        global_index = await self.storage.read_raw("interactions/global-index.json")
        if not global_index:
            global_index = {"interactions": []}

        # Check if already exists
        existing = next(
            (i for i in global_index["interactions"] if i["id"] == interaction.id), None
        )

        if not existing:
            # Add new entry
            global_index["interactions"].insert(
                0,  # Add at beginning (most recent)
                {
                    "id": interaction.id,
                    "counselor_id": interaction.counselor_id,
                    "type": interaction.type,
                    "date": interaction.date.isoformat(),
                },
            )

            # Keep only last 1000 in index
            global_index["interactions"] = global_index["interactions"][:1000]

            await self.storage.write_raw("interactions/global-index.json", global_index)
