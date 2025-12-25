import logging
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import PriceRange, Modifier, Material, Product

logger = logging.getLogger(__name__)


async def calculate_price(
    session: AsyncSession,
    product_code: str,
    quantity: int,
    material_code: str,
    modifier_codes: list[str]
) -> dict:
    """
    Розраховує ціну та термін виконання замовлення.
    
    Args:
        session: Асинхронна сесія БД
        product_code: Код продукту
        quantity: Кількість одиниць
        material_code: Код матеріалу
        modifier_codes: Список кодів модифікаторів
    
    Returns:
        dict: Словник з ключами price, deadline_days, quantity_used, modifiers_used
    
    Raises:
        ValueError: Якщо продукт, матеріал або ціна не знайдені
    """
    # Валідація вхідних даних
    if not product_code:
        raise ValueError("Код продукту не може бути порожнім")
    if quantity <= 0:
        raise ValueError("Кількість повинна бути більше нуля")
    if not material_code:
        raise ValueError("Код матеріалу не може бути порожнім")
    
    try:
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
                raise ValueError(f"Немає ціни для продукту з кодом: {product_code}")
            quantity = price_obj.range_to
            logger.info(f"Використано максимальний діапазон для продукту {product_code}")

        # --- Ціна за одиницю ---
        range_count = price_obj.range_to - price_obj.range_from + 1
        if range_count <= 0:
            raise ValueError("Невірний діапазон цін")
        
        unit_price = float(price_obj.price) / range_count

        # --- Матеріал ---
        material = (await session.execute(
            select(Material).where(Material.code == material_code)
        )).scalars().first()
        if not material:
            raise ValueError(f"Матеріал з кодом {material_code} не знайдено")
        
        if material.price_multiplier <= 0:
            raise ValueError(f"Невірний множник ціни для матеріалу {material_code}")
        
        unit_price *= float(material.price_multiplier)

        # --- Модифікатори ---
        total_deadline_modifier = 0
        modifiers = []
        if modifier_codes:
            modifiers = (await session.execute(
                select(Modifier).where(Modifier.code.in_(modifier_codes))
            )).scalars().all()
            
            # Перевірка, чи всі модифікатори знайдені
            found_codes = {mod.code for mod in modifiers}
            missing_codes = set(modifier_codes) - found_codes
            if missing_codes:
                logger.warning(f"Модифікатори не знайдені: {missing_codes}")
            
            for mod in modifiers:
                if mod.price_multiplier <= 0:
                    logger.warning(f"Невірний множник ціни для модифікатора {mod.code}")
                else:
                    unit_price *= float(mod.price_multiplier)
            total_deadline_modifier = sum(mod.deadline_modifier_days for mod in modifiers)

        # --- Загальна ціна ---
        total_price = unit_price * quantity
        
        if total_price < 0:
            raise ValueError("Розрахована ціна не може бути від'ємною")

        # --- Термін ---
        base_days = price_obj.product.base_deadline_days
        total_days = base_days + total_deadline_modifier
        
        if total_days < 0:
            logger.warning(f"Термін виконання від'ємний: {total_days}, встановлено 0")
            total_days = 0

        return {
            "price": round(total_price, 2),
            "deadline_days": total_days,
            "quantity_used": quantity,
            "modifiers_used": [mod.name for mod in modifiers]
        }
    except ValueError:
        # Прокидаємо ValueError далі
        raise
    except Exception as e:
        logger.error(f"Неочікувана помилка при розрахунку ціни: {e}", exc_info=True)
        raise ValueError(f"Помилка при розрахунку ціни: {str(e)}")
