# ──────────────────────────────────────────────────────────────────────────────
# REMOVED — WebSocket Chat Endpoint
# ──────────────────────────────────────────────────────────────────────────────
# This file previously housed the /ws/chat/{invoice_id} WebSocket endpoint.
#
# It has been removed as part of the Vercel serverless migration.
# Vercel does not support long-lived WebSocket connections.
#
# Replacement: Real-time chat is now powered by Pusher Channels.
#   • Backend  → app/services/pusher_service.py  (trigger_new_message)
#   • Auth     → app/api/v1/pusher_auth.py        (POST /api/v1/pusher/auth)
#   • Frontend → Use pusher-js SDK to subscribe to "private-chat-<invoice_id>"
# ──────────────────────────────────────────────────────────────────────────────
