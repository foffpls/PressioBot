import asyncio
from app.db.session import AsyncSessionLocal
from app.services.price_engine import calculate_price

async def test_calculation():
    async with AsyncSessionLocal() as session:
        result = await calculate_price(
            session=session,
            product_code="business_card",
            quantity=250,
            material_code="paper_350",
            modifier_codes=["lamination"]
        )
        print(result)

asyncio.run(test_calculation())
