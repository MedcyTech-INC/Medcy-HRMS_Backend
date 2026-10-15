from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

import os
import socket

# Engine configuration depending on DB backend
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# Handle Docker localhost-to-host resolution seamlessly
db_url = settings.DATABASE_URL
if not is_sqlite and os.path.exists('/.dockerenv') and ('@127.0.0.1:' in db_url or '@localhost:' in db_url):
    try:
        socket.gethostbyname('host.docker.internal')
        db_url = db_url.replace('@127.0.0.1:', '@host.docker.internal:').replace('@localhost:', '@host.docker.internal:')
    except Exception:
        pass

engine_kwargs = {
    "echo": settings.DEBUG,
}

if not is_sqlite:
    engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 10,
        "pool_pre_ping": True,
    })

engine = create_async_engine(
    db_url,
    **engine_kwargs
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
