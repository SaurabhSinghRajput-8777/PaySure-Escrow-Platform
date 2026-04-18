"""
Pusher Channels — private-channel authentication endpoint.

How it works:
  1. Frontend (pusher-js) connects to Pusher and tries to subscribe to
     a private channel, e.g. "private-chat-<invoice_id>".
  2. Pusher JS requires the frontend to call THIS endpoint with the
     socket_id (Pusher-assigned) and channel_name before allowing the
     subscription.
  3. We verify the requesting user is actually a participant of that
     invoice, then return a signed auth token that Pusher validates.

This prevents arbitrary users from subscribing to other people's chats.
"""

import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.invoice import Invoice
from app.services.pusher_service import authenticate_channel

router = APIRouter(prefix="/pusher", tags=["Pusher"])


@router.post("/auth")
def pusher_channel_auth(
    channel_name: str = Form(...),
    socket_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Authenticate a Pusher private-channel subscription.

    The frontend's pusher-js SDK posts here automatically when subscribing
    to a "private-*" channel.  We verify the user is a participant of the
    invoice before issuing the auth token.
    """
    # channel_name format: "private-chat-<invoice_id>"
    prefix = "private-chat-"
    if not channel_name.startswith(prefix):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid channel name format",
        )

    raw_invoice_id = channel_name[len(prefix):]
    try:
        invoice_id = uuid.UUID(raw_invoice_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invoice ID in channel name",
        )

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    # Only the client and the assigned freelancer may subscribe
    if current_user.id != invoice.client_id and current_user.id != invoice.freelancer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to subscribe to this channel",
        )

    auth_response = authenticate_channel(channel_name, socket_id)
    return auth_response
