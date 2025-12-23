from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Order

async def create_order(
    session: AsyncSession,
    user_id: int,
    product_id: int,
    quantity: int,
    material_id: int,
    modifier_codes: list[str],
    price: float,
    deadline_days: int
):
    modifiers_str = ",".join(modifier_codes) if modifier_codes else ""
    order = Order(
        user_id=user_id,
        product_id=product_id,
        quantity=quantity,
        material_id=material_id,
        modifiers=modifiers_str,
        price=price,
        deadline_days=deadline_days
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order
