from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.engine import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing a transactional async database session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
