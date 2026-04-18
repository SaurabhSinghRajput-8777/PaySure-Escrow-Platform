# ──────────────────────────────────────────────────────────────────────────────
# REMOVED — In-Memory WebSocket Manager
# ──────────────────────────────────────────────────────────────────────────────
# This file previously managed in-process WebSocket rooms.
# It has been removed: Vercel serverless functions are stateless, so in-memory
# state is lost between invocations.
#
# Replacement: Pusher Channels (cloud-managed pub/sub)
#   → app/services/pusher_service.py
# ──────────────────────────────────────────────────────────────────────────────
