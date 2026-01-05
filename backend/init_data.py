"""Initialize database with default data."""
import asyncio
import logging
from datetime import date, datetime

from config import get_settings, setup_logging
from dependencies import get_storage_client
from models.metrics import (
    CurrentMetrics,
    Phase as MetricsPhase,
    Phase1Targets,
    Phase2Targets,
    Phase3Targets,
    Phase4Targets,
)
from models.timeline import CurrentPhase, Phase

logger = logging.getLogger(__name__)


async def initialize_metrics(storage_client):
    """Initialize current metrics with default values."""
    logger.info("Initializing current metrics...")

    # Check if metrics already exist
    existing = await storage_client.read("metrics/current.json", CurrentMetrics)
    if existing:
        logger.info("Current metrics already exist, skipping initialization")
        return

    # Create default metrics
    metrics = CurrentMetrics(
        as_of=datetime.utcnow(),
        current_phase=MetricsPhase.PHASE_1,
        current_week=1,
        total_counselors=0,
        total_connections=0,
        total_discovery_calls=0,
        total_demos=0,
        total_pilots_onboarded=0,
        active_pilots=0,
        partner_firms=0,
        total_students=0,
        active_students=0,
        monthly_signups=0,
        paid_users=0,
        mrr=0.0,
        current_nps=None,
        current_weekly_active_rate=None,
        total_referrals=0,
        total_feedback_items=0,
        positioning_phrases_validated=0,
        phase1_targets=Phase1Targets(
            pilots_onboarded_min=10,
            pilots_onboarded_max=15,
            nps_target=8.0,
            weekly_active_rate_target=70.0,
            referrals_target=10,
            feedback_items_target=30,
            positioning_phrases_target=3,
        ),
        phase2_targets=Phase2Targets(
            partner_firms_min=3,
            partner_firms_max=5,
            students_per_firm_target=50,
            renewal_intent_target=80.0,
            total_students_target=150,
        ),
        phase3_targets=Phase3Targets(
            weekly_active_rate_target=60.0,
            time_to_first_value_minutes=10,
            student_nps_target=7.0,
            feature_adoption_rate_target=70.0,
        ),
        phase4_targets=Phase4Targets(
            paid_conversion_rate_target=5.0,
            retention_12mo_target=70.0,
            monthly_signups_target=500,
            cac_target=50.0,
        ),
    )

    await storage_client.write("metrics/current.json", metrics)
    logger.info("✓ Current metrics initialized")


async def initialize_timeline(storage_client):
    """Initialize current phase with default values."""
    logger.info("Initializing current phase...")

    # Check if timeline already exists
    existing = await storage_client.read("timeline/current-phase.json", CurrentPhase)
    if existing:
        logger.info("Current phase already exists, skipping initialization")
        return

    # Create default phase
    today = date.today()
    current_phase = CurrentPhase(
        phase=Phase.PHASE_1,
        week_number=1,
        phase_start_date=today,
        current_date=today,
        days_in_phase=0,
        weeks_remaining_in_phase=7,  # Phase 1 is 8 weeks
        on_schedule=True,
    )

    await storage_client.write("timeline/current-phase.json", current_phase)
    logger.info("✓ Current phase initialized")




async def main():
    """Main initialization function."""
    setup_logging()
    logger.info("Starting database initialization...")

    settings = get_settings()
    storage_client = get_storage_client()

    try:
        await initialize_metrics(storage_client)
        await initialize_timeline(storage_client)

        logger.info("✅ Database initialization complete!")

    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
