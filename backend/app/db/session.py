from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator
from app.core.config import settings


# NullPool is required for Vercel serverless:
# Each function invocation is stateless — a persistent connection pool would
# accumulate stale connections on the DB side and never release them.
# NullPool opens a fresh connection per request and closes it immediately after.
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,       # No persistent pool — safe for serverless
    pool_pre_ping=True,       # Verifies connection health before use
    echo=settings.DEBUG,      # Logs all SQL queries to console in DEBUG mode
)

# Factory that creates new Session objects bound to our engine
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,   # We manually commit transactions for safety
    autoflush=False,    # We manually flush to control when changes hit the DB
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency — yields a DB session per request
    and guarantees it closes even if an error occurs.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()