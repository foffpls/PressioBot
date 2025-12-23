from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import PriceRange

async def get_price_by_quantity(
    session: AsyncSession,
    product_id: int,
    quantity: int
) -> float | None:
    result = await session.execute(
        select(PriceRange.price)
        .where(
            PriceRange.product_id == product_id,
            PriceRange.range_from <= quantity,
            PriceRange.range_to >= quantity
        )
    )
    return result.scalar_one_or_none()
