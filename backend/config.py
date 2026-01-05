"""Application configuration."""
import logging
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # JWT & Authentication
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    jwt_expiration_minutes: int = 10080
    jwt_secret_key: str
    secret_key: str

    # AI APIs - OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4"
    openai_timeout: int = 180
    openai_college_master_file_id: str = ""
    openai_college_home_state_file_id: str = ""

    # AI APIs - Anthropic & Others
    anthropic_api_key: str
    grok_api_key: str = ""
    default_provider: str = "openai"
    max_tokens: int = 400000

    # College Scorecard API
    college_scorecard_api_key: str = "your_key_here"

    # App Config
    environment: str = "development"
    debug: bool = False
    api_v1_str: str = "/api/v1"
    project_name: str = "TargetAI"
    version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/targetai.log"

    # File Upload
    max_upload_size: int = 10485760
    allowed_extensions: list[str] = ["pdf", "doc", "docx", "txt"]

    # Session
    session_expire_hours: int = 24

    # Analytics
    google_analytics_id: str = ""
    mixpanel_token: str = ""

    # Feature Flags
    enable_profile_matrix: bool = True
    enable_college_matrix: bool = True
    enable_essay_helper: bool = False
    enable_application_tracker: bool = False

    # Data Directory
    project_data_dir: str = "./data"

    # Email/SMTP
    smtp_host: str = "smtp.zoho.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = ""
    from_name: str = "TargetAI"

    # URLs
    backend_api_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Azure Storage
    azure_storage_connection_string: str
    azure_storage_container_name: str = "targetai-gtm"
    azure_storage_account_name: str = ""
    azure_storage_account_key: str = ""
    azure_user_container_name: str = "targetai-gtm"
    azure_intake_container_name: str = "targetai-gtm"

    # MCP Server
    mcp_server_url: str = "http://localhost:8001"
    mcp_api_key: str = ""
    mcp_tool_timeout: int = 200

    # External APIs
    bls_api_key: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""

    # Cache
    cache_ttl_hours: int = 168
    profile_cache_ttl_hours: int = 24

    # Payments - Stripe
    stripe_publishable_key: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # Payments - PayPal
    paypal_client_id: str = ""
    paypal_client_secret: str = ""
    paypal_mode: str = "sandbox"

    # Optional: Pinecone
    pinecone_api_key: str = ""
    pinecone_environment: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings instance
    """
    return Settings()  # type: ignore


def setup_logging() -> None:
    """Configure logging."""
    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
