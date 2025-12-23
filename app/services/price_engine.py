from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import PriceRange, Modifier, Material, Product

async def calculate_price(
    session: AsyncSession,
    product_code: str,
    quantity: int,
    material_code: str,
    modifier_codes: list[str]
):
    # --- Знаходимо PriceRange та продукт ---
    price_obj = (await session.execute(
        select(PriceRange)
        .options(selectinload(PriceRange.product))
        .join(PriceRange.product)
        .where(
            Product.code == product_code,
            PriceRange.range_from <= quantity,
            PriceRange.range_to >= quantity
        )
    )).scalars().first()

    if not price_obj:
        # Беремо найбільший діапазон для продукту
        price_obj = (await session.execute(
            select(PriceRange)
            .options(selectinload(PriceRange.product))
            .join(PriceRange.product)
            .where(Product.code == product_code)
            .order_by(PriceRange.range_to.desc())
        )).scalars().first()

        if not price_obj:
            raise ValueError("Немає ціни для заданого продукту")
        quantity = price_obj.range_to

    # --- Ціна за одиницю ---
    range_count = price_obj.range_to - price_obj.range_from + 1
    unit_price = float(price_obj.price) / range_count

    # --- Матеріал ---
    material = (await session.execute(
        select(Material).where(Material.code == material_code)
    )).scalars().first()
    if not material:
        raise ValueError("Матеріал не знайдено")
    unit_price *= float(material.price_multiplier)

    # --- Модифікатори ---
    total_deadline_modifier = 0
    modifiers = []
    if modifier_codes:
        modifiers = (await session.execute(
            select(Modifier).where(Modifier.code.in_(modifier_codes))
        )).scalars().all()
        for mod in modifiers:
            unit_price *= float(mod.price_multiplier)
        total_deadline_modifier = sum(mod.deadline_modifier_days for mod in modifiers)

    # --- Загальна ціна ---
    total_price = unit_price * quantity

    # --- Термін ---
    base_days = price_obj.product.base_deadline_days
    total_days = base_days + total_deadline_modifier

    return {
        "price": round(total_price, 2),
        "deadline_days": total_days,
        "quantity_used": quantity,
        "modifiers_used": [mod.name for mod in modifiers]
    }
