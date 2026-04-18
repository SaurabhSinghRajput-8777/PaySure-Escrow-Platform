"""
Pusher Channels service — replaces the in-memory WebSocketManager.

Architecture:
  1. Frontend connects to Pusher directly using the pusher-js SDK.
  2. Frontend authenticates by calling POST /api/v1/pusher/auth with its JWT.
  3. When a REST message is POSTed, we call trigger_new_message() here,
     which fires a "new-message" event on the private channel.
  4. All subscribed frontend clients receive the event instantly via Pusher's
     infrastructure — no persistent server process required.
"""

import logging
from typing import Any

import pusher

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton Pusher client
# ---------------------------------------------------------------------------
# Built once at import time.  Because Vercel may spin up multiple instances,
# this is NOT shared state — each instance has its own SDK client, but they
# all talk to Pusher's cloud, so events reach every subscriber regardless.
# ---------------------------------------------------------------------------

_client: pusher.Pusher | None = None


def _get_client() -> pusher.Pusher:
    """Lazily initialise the Pusher client so missing env vars don't crash startup."""
    global _client
    if _client is None:
        if not settings.PUSHER_APP_ID:
            raise RuntimeError(
                "Pusher is not configured. "
                "Set PUSHER_APP_ID, PUSHER_KEY, PUSHER_SECRET, PUSHER_CLUSTER in your .env"
            )
        _client = pusher.Pusher(
            app_id=settings.PUSHER_APP_ID,
            key=settings.PUSHER_KEY,
            secret=settings.PUSHER_SECRET,
            cluster=settings.PUSHER_CLUSTER,
            ssl=True,
        )
    return _client


def trigger_new_message(invoice_id: str, payload: dict[str, Any]) -> None:
    """
    Broadcast a 'new-message' event on the private invoice channel.

    Channel name format: ``private-chat-<invoice_id>``
    Only users authenticated via /api/v1/pusher/auth can subscribe.
    """
    channel = f"private-chat-{invoice_id}"
    try:
        _get_client().trigger(channel, "new-message", payload)
        logger.debug(f"Pusher event fired → channel={channel}")
    except Exception as exc:
        # Pusher failure must NEVER break the HTTP response — just log it.
        logger.warning(f"Pusher trigger failed for channel={channel}: {exc}")


def authenticate_channel(channel_name: str, socket_id: str) -> dict:
    """
    Generate a Pusher auth signature for a private channel subscription.
    Called by the /api/v1/pusher/auth endpoint after verifying the user
    is a legit participant of the invoice.
    """
    return _get_client().authenticate(channel=channel_name, socket_id=socket_id)
