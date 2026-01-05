"""Timeline repository for data access."""
import logging
from datetime import date
from typing import Optional

from models.timeline import CurrentPhase, Milestone, TimelineData, Phase, PhaseTransition
from storage.blob_client import BlobStorageClient

logger = logging.getLogger(__name__)


class TimelineRepository:
    """Repository for timeline data access."""

    def __init__(self, storage_client: BlobStorageClient):
        """Initialize repository.

        Args:
            storage_client: Azure Blob Storage client
        """
        self.storage = storage_client

    async def get_current_phase(self) -> Optional[CurrentPhase]:
        """Get current phase information.

        Returns:
            Current phase or None if not initialized
        """
        return await self.storage.read("timeline/current-phase.json", CurrentPhase)

    async def save_current_phase(self, current_phase: CurrentPhase) -> CurrentPhase:
        """Save current phase.

        Args:
            current_phase: Current phase to save

        Returns:
            Saved current phase instance
        """
        await self.storage.write(
            "timeline/current-phase.json", current_phase, etag=current_phase.etag
        )
        logger.info(f"Saved current phase: {current_phase.phase}, week {current_phase.week_number}")
        return current_phase

    async def get_timeline(self) -> Optional[TimelineData]:
        """Get complete timeline data.

        Returns:
            Timeline data or None if not initialized
        """
        return await self.storage.read("timeline/timeline.json", TimelineData)

    async def save_timeline(self, timeline: TimelineData) -> TimelineData:
        """Save complete timeline.

        Args:
            timeline: Timeline data to save

        Returns:
            Saved timeline instance
        """
        await self.storage.write("timeline/timeline.json", timeline, etag=timeline.etag)
        logger.info("Saved timeline data")
        return timeline

    async def get_milestones(self) -> list[Milestone]:
        """Get all milestones.

        Returns:
            List of all milestones
        """
        timeline = await self.get_timeline()
        if not timeline:
            return []
        return timeline.milestones

    async def add_milestone(self, milestone: Milestone) -> None:
        """Add a new milestone.

        Args:
            milestone: Milestone to add
        """
        timeline = await self.get_timeline()
        if not timeline:
            # Initialize timeline
            current_phase = await self.get_current_phase()
            if not current_phase:
                raise ValueError("Must initialize current phase first")

            timeline = TimelineData(
                current_phase=current_phase, milestones=[], phase_history=[]
            )

        timeline.milestones.append(milestone)
        await self.save_timeline(timeline)
        logger.info(f"Added milestone: {milestone.name}")

    async def update_milestone(self, milestone: Milestone) -> None:
        """Update an existing milestone.

        Args:
            milestone: Milestone to update
        """
        timeline = await self.get_timeline()
        if not timeline:
            raise ValueError("Timeline not initialized")

        # Find and update
        for i, m in enumerate(timeline.milestones):
            if m.id == milestone.id:
                timeline.milestones[i] = milestone
                await self.save_timeline(timeline)
                logger.info(f"Updated milestone: {milestone.name}")
                return

        raise ValueError(f"Milestone not found: {milestone.id}")

    async def transition_phase(self, new_phase: Phase, transition: PhaseTransition) -> None:
        """Transition to a new phase.

        Args:
            new_phase: New phase to transition to
            transition: Transition record
        """
        # Update current phase
        current_phase = await self.get_current_phase()
        if not current_phase:
            raise ValueError("Current phase not initialized")

        current_phase.phase = new_phase
        current_phase.week_number = 1
        current_phase.phase_start_date = date.today()
        current_phase.days_in_phase = 0
        await self.save_current_phase(current_phase)

        # Record transition in timeline
        timeline = await self.get_timeline()
        if not timeline:
            timeline = TimelineData(
                current_phase=current_phase,
                milestones=[],
                phase_history=[],
            )

        timeline.phase_history.append(transition)
        timeline.current_phase = current_phase
        await self.save_timeline(timeline)

        logger.info(f"Transitioned to {new_phase}")
