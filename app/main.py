"""
Тестовий файл для перевірки розрахунку ціни.
УВАГА: Це тестовий файл, не використовується в основному коді.
Рекомендується перенести в папку tests/ або видалити.
"""
import asyncio
import logging
from app.db.session import AsyncSessionLocal
from app.services.price_engine import calculate_price

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_calculation():
    """Тестова функція для перевірки розрахунку ціни."""
    try:
        async with AsyncSessionLocal() as session:
            result = await calculate_price(
                session=session,
                product_code="business_card",
                quantity=250,
                material_code="paper_350",
                modifier_codes=["lamination"]
            )
            print("Результат розрахунку:", result)
    except Exception as e:
        logger.error(f"Помилка при тестуванні: {e}", exc_info=True)
        print(f"Помилка: {e}")


if __name__ == "__main__":
    asyncio.run(test_calculation())
