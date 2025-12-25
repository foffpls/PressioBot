from datetime import datetime, date

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from sqlalchemy import select, func

from app.db.session import AsyncSessionLocal
from app.db.models import Order, Product, Material, Modifier


router = Router()


class OrderFSM(StatesGroup):
    waiting_date = State()


# /order
@router.message(Command("order"))
async def order_start(message: Message, state: FSMContext):
    await message.answer(
        "📅 Введіть дату у форматі:\n<b>23.12.2025</b>",
        parse_mode="HTML"
    )
    await state.set_state(OrderFSM.waiting_date)


@router.message(OrderFSM.waiting_date)
async def order_by_date(message: Message, state: FSMContext):
    try:
        target_date = datetime.strptime(message.text, "%d.%m.%Y").date()
    except ValueError:
        await message.answer("❌ Невірний формат дати. Приклад: 23.12.2025")
        return

    async with AsyncSessionLocal() as session:
        # Отримуємо всі замовлення за дату
        result = await session.execute(
            select(Order, Product, Material)
            .join(Product, Product.id == Order.product_id)
            .join(Material, Material.id == Order.material_id)
            .where(func.date(Order.created_at) == target_date)
            .order_by(Order.created_at)
        )
        rows = result.all()

        if not rows:
            await message.answer("📭 Замовлень за цю дату не знайдено.")
            await state.clear()
            return

        # --- Збираємо всі коди модифікаторів ---
        modifier_codes: set[str] = set()
        for order, _, _ in rows:
            if order.modifiers:
                modifier_codes.update(order.modifiers.split(","))

        # --- Завантажуємо назви модифікаторів ---
        modifiers_map: dict[str, str] = {}
        if modifier_codes:
            mods = await session.execute(
                select(Modifier).where(Modifier.code.in_(modifier_codes))
            )
            modifiers_map = {m.code: m.name for m in mods.scalars()}

    # --- Формуємо відповідь ---
    response: list[str] = []

    for order, product, material in rows:
        modifiers_names = (
            ", ".join(
                modifiers_map.get(code, code)
                for code in order.modifiers.split(",")
            )
            if order.modifiers else "—"
        )

        response.append(
            f"🆔 #{order.id}\n"
            f"🖨 Продукт: {product.name}\n"
            f"📄 Матеріал: {material.name}\n"
            f"🔢 Кількість: {order.quantity}\n"
            f"⚙️ Додаткові послуги: {modifiers_names}\n"
            f"💰 Вартість: {order.price} грн\n"
            f"⏱ Термін: {order.deadline_days} дн.\n"
            f"────────────"
        )

    await message.answer("\n".join(response))
    await state.clear()
