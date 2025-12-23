from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Material

async def get_material_by_code(
    session: AsyncSession,
    code: str
) -> Material | None:
    result = await session.execute(
        select(Material).where(Material.code == code)
    )
    return result.scalar_one_or_none()
