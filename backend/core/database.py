"""
core/database.py — Async SQLAlchemy engine + session factory.
Connects ONLY to PostgreSQL via DATABASE_URL from environment.
No SQLite fallback — intentional.
"""
import ssl
import urllib.parse
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from core.config import get_settings

settings = get_settings()


def _build_engine_args(database_url: str) -> tuple[str, dict]:
    """
    asyncpg does NOT support the `sslmode` query parameter (that's psycopg2).
    Strip it from the URL and convert to a proper ssl context for connect_args.
    """
    connect_args: dict = {}
    clean_url = database_url

    parsed = urllib.parse.urlparse(database_url)
    if parsed.query:
        params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        ssl_mode = params.pop("sslmode", [None])[0]
        new_query = urllib.parse.urlencode(
            {k: v[0] for k, v in params.items()}
        )
        clean_url = urllib.parse.urlunparse(parsed._replace(query=new_query))

        if ssl_mode in ("require", "verify-ca", "verify-full", "prefer"):
            ssl_ctx = ssl.create_default_context()
            if ssl_mode in ("require", "prefer"):
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE
            connect_args["ssl"] = ssl_ctx

    return clean_url, connect_args


_db_url, _connect_args = _build_engine_args(settings.DATABASE_URL)

# ── Engine ────────────────────────────────────────────────────────────────────
# echo=False in production; flip to True locally for SQL debug output
engine = create_async_engine(
    _db_url,
    echo=(settings.APP_ENV == "development"),
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # recycle stale Neon connections
    connect_args=_connect_args,
)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)
async_session_maker = AsyncSessionLocal


# ── Declarative base (shared by all models) ───────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── FastAPI dependency ────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async DB session per request, always closing it afterwards.
    Use as: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
