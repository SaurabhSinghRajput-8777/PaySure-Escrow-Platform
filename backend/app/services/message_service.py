import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.message import Message
from app.schemas.message import MessageCreate, MessageResponse


def send_message(db: Session, data: MessageCreate, sender_id: uuid.UUID) -> Message:
    """
    Stores a new message in the DB, then broadcasts it via Pusher Channels
    so all connected frontend clients receive it in real-time without polling.
    Verifies the sender is a participant in this invoice (client or freelancer).
    """
    from app.models.invoice import Invoice

    invoice = db.query(Invoice).filter(Invoice.id == data.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    # Only the client or assigned freelancer can message
    if invoice.client_id != sender_id and invoice.freelancer_id != sender_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project participants can send messages",
        )

    message = Message(
        invoice_id=data.invoice_id,
        sender_id=sender_id,
        content=data.content,
        file_url=data.file_url,
        file_name=data.file_name,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    # ── Broadcast via Pusher Channels ─────────────────────────────────────────
    # This fires a "new-message" event on "private-chat-<invoice_id>".
    # The try/except ensures a Pusher outage never breaks the HTTP response —
    # the message is already safely persisted to DB above.
    try:
        from app.services.pusher_service import trigger_new_message
        enriched = enrich_message_response(message)
        trigger_new_message(str(data.invoice_id), enriched.model_dump(mode="json"))
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning(f"Pusher broadcast failed: {exc}")

    return message



def get_messages_for_invoice(
    db: Session, invoice_id: uuid.UUID, requester_id: uuid.UUID
) -> list[Message]:
    """
    Returns all messages for a given invoice, ordered oldest-first.
    Verifies the requester is a participant.
    """
    from app.models.invoice import Invoice

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    # Admin can also view messages
    from app.models.user import User, UserRole
    user = db.query(User).filter(User.id == requester_id).first()
    is_admin = user and user.role == UserRole.admin

    if not is_admin and invoice.client_id != requester_id and invoice.freelancer_id != requester_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these messages",
        )

    return (
        db.query(Message)
        .filter(Message.invoice_id == invoice_id)
        .order_by(Message.created_at.asc())
        .all()
    )


def enrich_message_response(msg: Message) -> MessageResponse:
    """Build a MessageResponse with sender name/role from the loaded relationship."""
    return MessageResponse(
        id=msg.id,
        invoice_id=msg.invoice_id,
        sender_id=msg.sender_id,
        sender_name=msg.sender.full_name if msg.sender else None,
        sender_role=msg.sender.role.value if msg.sender else None,
        content=msg.content,
        file_url=msg.file_url,
        file_name=msg.file_name,
        created_at=msg.created_at,
    )
