"""
Vercel Serverless Entry Point
──────────────────────────────────────────────────────────────────────────────
Vercel's Python runtime looks for a file inside the `api/` directory that
exports a callable named `handler`.

Mangum wraps our FastAPI ASGI app into an AWS Lambda-compatible handler
(which Vercel's runtime is built on top of).  All HTTP traffic routed via
vercel.json ends up here.

lifespan="off"  → Disables ASGI lifespan events (startup/shutdown) which are
                   not supported in the Vercel function model.
──────────────────────────────────────────────────────────────────────────────
"""

from mangum import Mangum
from app.main import app

handler = Mangum(app, lifespan="off")
