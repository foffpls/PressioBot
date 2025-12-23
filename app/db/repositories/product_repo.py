from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Product

async def get_product_by_code(
    session: AsyncSession,
    code: str
) -> Product | None:
    result = await session.execute(
        select(Product).where(Product.code == code)
    )
    return result.scalar_one_or_none()
