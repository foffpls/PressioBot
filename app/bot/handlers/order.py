from datetime import datetime, date
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from sqlalchemy import select, func

from app.db.session import AsyncSessionLocal
from app.db.models import Order, Product, Material, Modifier
from app.bot.states import OrderFSM
from app.bot.middleware.access_control import is_user_allowed

logger = logging.getLogger(__name__)

router = Router()


# /order
@router.message(Command("order"))
async def order_start(message: Message, state: FSMContext):
    """
    Запускає процес пошуку замовлень за датою.
    Доступ тільки для дозволених користувачів.
    
    Args:
        message: Повідомлення з командою
        state: FSM контекст для збереження стану
    """
    # Перевірка доступу
    user_id = message.from_user.id if message.from_user else None
    if not user_id or not is_user_allowed(user_id):
        logger.warning(f"Спроба доступу до /order від недозволеного користувача: {user_id}")
        await message.answer("❌ У вас немає доступу до цієї команди.")
        return
    
    try:
        await message.answer(
            "📅 Введіть дату у форматі:\n<b>23.12.2025</b>\n"
            "Або введіть /cancel для скасування",
            parse_mode="HTML"
        )
        await state.set_state(OrderFSM.waiting_date)
    except Exception as e:
        logger.error(f"Помилка при запуску команди /order: {e}", exc_info=True)
        await message.answer("❌ Виникла помилка. Спробуйте пізніше.")


# Обробка /cancel в стані waiting_date
@router.message(Command("cancel"), OrderFSM.waiting_date)
async def cancel_order(message: Message, state: FSMContext):
    """
    Скасовує пошук замовлень.
    
    Args:
        message: Повідомлення з командою
        state: FSM контекст
    """
    await state.clear()
    await message.answer("✅ Операцію скасовано.")


@router.message(OrderFSM.waiting_date)
async def order_by_date(message: Message, state: FSMContext):
    """
    Обробляє введену дату та показує замовлення за цю дату.
    Доступ тільки для дозволених користувачів.
    
    Args:
        message: Повідомлення з датою
        state: FSM контекст для збереження стану
    """
    # Перевірка доступу (навіть якщо користувач вже в стані)
    user_id = message.from_user.id if message.from_user else None
    if not user_id or not is_user_allowed(user_id):
        logger.warning(f"Спроба доступу до order_by_date від недозволеного користувача: {user_id}")
        await state.clear()
        await message.answer("❌ У вас немає доступу до цієї команди.")
        return
    
    try:
        if not message.text:
            await message.answer("❌ Будь ласка, введіть дату.")
            return
        
        # Перевірка на команду /cancel (якщо не спрацював Command filter)
        if message.text.strip() == "/cancel":
            await state.clear()
            await message.answer("✅ Операцію скасовано.")
            return
        
        target_date = datetime.strptime(message.text, "%d.%m.%Y").date()
        
        # Валідація дати: не може бути в далекому майбутньому (більше 100 років)
        from datetime import date as date_class
        max_date = date_class.today().replace(year=date_class.today().year + 100)
        if target_date > max_date:
            await message.answer("❌ Дата не може бути більше ніж через 100 років.")
            return
        
        # Дата не може бути раніше 2000 року (якщо це не потрібно)
        min_date = date_class(2000, 1, 1)
        if target_date < min_date:
            await message.answer("❌ Дата не може бути раніше 2000 року.")
            return
            
    except ValueError:
        await message.answer("❌ Невірний формат дати. Приклад: 23.12.2025")
        return

    try:
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
                if order.modifiers and order.modifiers.strip():
                    modifier_codes.update(code.strip() for code in order.modifiers.split(",") if code.strip())

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
                    modifiers_map.get(code.strip(), code.strip())
                    for code in order.modifiers.split(",")
                    if code.strip()
                )
                if order.modifiers and order.modifiers.strip() else "—"
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

        # Розбиваємо на частини, якщо повідомлення занадто велике (ліміт Telegram - 4096 символів)
        full_text = "\n".join(response)
        max_length = 4000  # Залишаємо запас
        
        if len(full_text) <= max_length:
            await message.answer(full_text)
        else:
            # Розбиваємо на частини
            current_part = []
            current_length = 0
            
            for order_text in response:
                if current_length + len(order_text) + 1 > max_length:
                    if current_part:
                        await message.answer("\n".join(current_part))
                    current_part = [order_text]
                    current_length = len(order_text)
                else:
                    current_part.append(order_text)
                    current_length += len(order_text) + 1
            
            if current_part:
                await message.answer("\n".join(current_part))
        
        await state.clear()
    except Exception as e:
        logger.error(f"Помилка при отриманні замовлень: {e}", exc_info=True)
        await message.answer("❌ Виникла помилка при отриманні замовлень. Спробуйте пізніше.")
        await state.clear()
