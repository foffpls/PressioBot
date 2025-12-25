import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Order

logger = logging.getLogger(__name__)


async def create_order(
    session: AsyncSession,
    user_id: int,
    product_id: int,
    quantity: int,
    material_id: int,
    modifier_codes: list[str],
    price: float,
    deadline_days: int
) -> Order:
    """
    Створює нове замовлення в базі даних.
    
    Args:
        session: Асинхронна сесія БД
        user_id: ID користувача
        product_id: ID продукту
        quantity: Кількість одиниць
        material_id: ID матеріалу
        modifier_codes: Список кодів модифікаторів
        price: Ціна замовлення
        deadline_days: Термін виконання в днях
    
    Returns:
        Order: Створений об'єкт замовлення
    
    Raises:
        ValueError: При некоректних вхідних даних
        Exception: При помилках збереження в БД
    """
    # Валідація вхідних даних
    if user_id <= 0:
        raise ValueError("ID користувача повинен бути більше нуля")
    if product_id <= 0:
        raise ValueError("ID продукту повинен бути більше нуля")
    if quantity <= 0:
        raise ValueError("Кількість повинна бути більше нуля")
    if material_id <= 0:
        raise ValueError("ID матеріалу повинен бути більше нуля")
    if price < 0:
        raise ValueError("Ціна не може бути від'ємною")
    if deadline_days < 0:
        raise ValueError("Термін виконання не може бути від'ємним")
    
    try:
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
        logger.info(f"Створено замовлення #{order.id} для користувача {user_id}")
        return order
    except Exception as e:
        logger.error(f"Помилка при створенні замовлення: {e}", exc_info=True)
        await session.rollback()
        raise
