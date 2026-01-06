"""Authentication middleware for API routes."""
from fastapi import Header, HTTPException, status
from typing import Optional

from config import get_settings


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Verify API key from request headers.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        API key if valid

    Raises:
        HTTPException: If API key is missing or invalid
    """
    settings = get_settings()

    # Get expected API key from environment
    expected_api_key = settings.secret_key  # Reusing existing secret_key

    # Check if API key is provided
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Please provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Verify API key
    if x_api_key != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    return x_api_key


def create_api_key_dependency(required: bool = True):
    """Create API key dependency with optional requirement.

    Args:
        required: Whether API key is required

    Returns:
        Dependency function
    """
    async def optional_verify_api_key(x_api_key: Optional[str] = Header(None)):
        if required:
            return await verify_api_key(x_api_key)
        return x_api_key

    return optional_verify_api_key
