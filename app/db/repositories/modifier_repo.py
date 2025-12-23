from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Modifier

async def get_modifiers_by_codes(
    session: AsyncSession,
    codes: list[str]
) -> list[Modifier]:
    if not codes:
        return []

    result = await session.execute(
        select(Modifier).where(Modifier.code.in_(codes))
    )
    return result.scalars().all()
