from fastapi import Header, HTTPException, status

from config import settings


def verify_agent_api_key(x_agent_api_key: str | None = Header(default=None)) -> None:
    """
    Optional API key validation for agent ingestion.

    If AGENT_API_KEY is set, requests must include a matching X-Agent-Api-Key.
    If unset, ingestion remains open for backward compatibility.
    """

    expected = (settings.AGENT_API_KEY or "").strip()
    if not expected:
        return

    provided = (x_agent_api_key or "").strip()
    if provided != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing agent API key",
        )

