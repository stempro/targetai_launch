"""Weekly log repository for data access."""
import logging
from datetime import date
from typing import Optional

from models.metrics import Phase
from models.weekly_log import WeeklyLog
from storage.blob_client import BlobStorageClient

logger = logging.getLogger(__name__)


class WeeklyLogRepository:
    """Repository for weekly log data access."""

    def __init__(self, storage_client: BlobStorageClient):
        """Initialize repository.

        Args:
            storage_client: Azure Blob Storage client
        """
        self.storage = storage_client

    async def get_log(self, phase: Phase, week_number: int) -> Optional[WeeklyLog]:
        """Get weekly log for a specific phase and week.

        Args:
            phase: Phase (e.g., phase1)
            week_number: Week number (1-8)

        Returns:
            Weekly log or None if not found
        """
        path = f"weekly_logs/{phase.value}/week_{week_number}.json"
        return await self.storage.read(path, WeeklyLog)

    async def save_log(self, log: WeeklyLog) -> WeeklyLog:
        """Save weekly log.

        Args:
            log: Weekly log to save

        Returns:
            Saved log instance
        """
        path = f"weekly_logs/{log.phase.value}/week_{log.week_number}.json"
        await self.storage.write(path, log, etag=log.etag)
        logger.info(f"Saved weekly log for {log.phase.value} week {log.week_number}")
        return log

    async def get_all_logs(self, phase: Phase) -> list[WeeklyLog]:
        """Get all weekly logs for a phase.

        Args:
            phase: Phase to get logs for

        Returns:
            List of weekly logs
        """
        prefix = f"weekly_logs/{phase.value}/"
        blob_names = await self.storage.list_blobs(prefix)

        logs = []
        for blob_name in blob_names:
            log = await self.storage.read(blob_name, WeeklyLog)
            if log:
                logs.append(log)

        # Sort by week number
        logs.sort(key=lambda x: x.week_number)
        return logs

    async def get_current_week_log(self, phase: Phase, week_number: int) -> WeeklyLog:
        """Get or create log for current week.

        Args:
            phase: Current phase
            week_number: Current week number

        Returns:
            Weekly log (existing or newly created)
        """
        existing = await self.get_log(phase, week_number)
        if existing:
            return existing

        # Create new log with default activities based on week
        from datetime import timedelta

        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        activities = self._get_default_activities(phase, week_number)

        new_log = WeeklyLog(
            week_number=week_number,
            phase=phase,
            week_start_date=week_start,
            week_end_date=week_end,
            activities=activities,
        )

        return new_log

    def _get_default_activities(self, phase: Phase, week_number: int) -> list:
        """Get default activities for a week based on action plan and phase.

        Args:
            phase: Current phase
            week_number: Week number

        Returns:
            List of ActivityLog objects
        """
        from models.weekly_log import ActivityLog

        # Phase 1: Counselor Credibility Pilot (8 weeks)
        if phase == Phase.PHASE_1:
            if week_number <= 2:
                tasks = [
                    "Optimize LinkedIn profile with counselor-focused positioning",
                    "Build target list of 50 counselors matching selection criteria",
                    "Send 20 connection requests with personalized notes",
                    "Engage with 10 counselor posts (meaningful comments)",
                    "Draft and publish first LinkedIn thought leadership post",
                    "Prepare demo environment with realistic sample data",
                ]
            elif week_number <= 4:
                tasks = [
                    "Send 15 personalized DMs to engaged connections",
                    "Schedule 8-10 discovery calls",
                    "Conduct discovery calls using provided script",
                    "Score candidates using rubric",
                    "Convert qualified leads to demo sessions",
                    "Publish second thought leadership post",
                ]
            elif week_number <= 6:
                tasks = [
                    "Conduct demo sessions for qualified candidates",
                    "Complete hands-on setup for committed pilots",
                    "Execute Week 1 check-in calls with new pilots",
                    "Ask each pilot for 2-3 referrals",
                    "Document feedback and feature requests",
                    "Continue outreach via referrals",
                ]
            else:
                tasks = [
                    "Reach 10-15 active pilot counselors",
                    "Conduct bi-weekly check-ins with all pilots",
                    "Deploy Week 4 NPS survey",
                    "Analyze feedback themes and prioritize fixes",
                    "Identify 3-5 potential advocate counselors",
                    "Begin Phase 2 planning with validated learnings",
                ]

        # Phase 2: Firm Distribution (Months 2-4, ~8 weeks)
        elif phase == Phase.PHASE_2:
            if week_number <= 2:
                tasks = [
                    "Identify 10-15 target counseling firms",
                    "Research firm structures and decision makers",
                    "Prepare firm partnership pitch deck",
                    "Develop tiered pricing packages for firms",
                    "Create firm admin dashboard demo",
                ]
            elif week_number <= 4:
                tasks = [
                    "Reach out to 5-8 firms with partnership proposals",
                    "Conduct firm demos and Q&A sessions",
                    "Negotiate partnership agreements",
                    "Set up referral program with Phase 1 advocates",
                    "Develop onboarding materials for firm staff",
                ]
            elif week_number <= 6:
                tasks = [
                    "Onboard first 2-3 partner firms",
                    "Train firm counselors on platform usage",
                    "Begin student onboarding through partner firms",
                    "Monitor student per-firm metrics",
                    "Collect firm feedback and iterate",
                ]
            else:
                tasks = [
                    "Reach 3-5 active partner firms",
                    "Achieve 50+ students per top firm",
                    "Measure renewal intent (target 80%+)",
                    "Document firm success stories",
                    "Begin Phase 3 student activation planning",
                ]

        # Phase 3: Student Activation (Months 4-6, ~8 weeks)
        elif phase == Phase.PHASE_3:
            if week_number <= 2:
                tasks = [
                    "Launch personalized student dashboard",
                    "Enable essay clustering visualization",
                    "Deploy task management and timeline features",
                    "Create student onboarding flow",
                    "Set up student-to-student referral program",
                ]
            elif week_number <= 4:
                tasks = [
                    "Drive student activation via counselor invites",
                    "Monitor time-to-first-value (target <10 min)",
                    "Track weekly active rate across all students",
                    "Collect student feedback on core features",
                    "Optimize onboarding based on drop-off data",
                ]
            elif week_number <= 6:
                tasks = [
                    "Achieve 60%+ weekly active rate",
                    "Measure feature adoption across key workflows",
                    "Deploy student NPS survey (target ≥7)",
                    "Identify power users and collect testimonials",
                    "Iterate on high-friction areas",
                ]
            else:
                tasks = [
                    "Validate student engagement targets met",
                    "Document student success stories",
                    "Prepare content marketing strategy",
                    "Design public signup flow for Phase 4",
                    "Begin Phase 4 direct growth planning",
                ]

        # Phase 4: Direct Student & Parent Growth (Month 6+)
        else:  # Phase.PHASE_4
            if week_number <= 2:
                tasks = [
                    "Launch public signup flow",
                    "Set up consumer pricing tiers ($49-99/mo)",
                    "Deploy counselor marketplace",
                    "Begin content marketing campaigns",
                    "Set up referral incentive program",
                ]
            elif week_number <= 4:
                tasks = [
                    "Drive traffic through content marketing",
                    "Monitor paid conversion rate (target 5%+)",
                    "Engage with parents on Reddit/Facebook groups",
                    "Create school counselor partnership program",
                    "Optimize marketing spend and CAC",
                ]
            else:
                tasks = [
                    "Scale to 500+ monthly signups",
                    "Maintain 70%+ 12-month retention",
                    "Expand content and community presence",
                    "Build partnerships with school counselors",
                    "Continuous product iteration and optimization",
                ]

        return [
            ActivityLog(task_id=f"task_{i+1}", task_description=task)
            for i, task in enumerate(tasks)
        ]
