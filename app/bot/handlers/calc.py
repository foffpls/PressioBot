from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from app.bot.states import CalcFSM
from app.bot.keyboards import products_kb, materials_kb, modifiers_kb
from app.db.session import AsyncSessionLocal
from app.db.models import Product, Material, Modifier
from app.services.price_engine import calculate_price

router = Router()


# --- /start ---
@router.message(F.text == "/start")
async def start_bot(message: Message):
    await message.answer(
        "👋 Привіт! Я бот-калькулятор поліграфії.\n"
        "Щоб розрахувати вартість, введіть команду /calc"
    )


# --- /calc ---
@router.message(F.text == "/calc")
async def start_calc(message: Message, state: FSMContext):
    async with AsyncSessionLocal() as session:
        products = (await session.execute(select(Product))).scalars().all()

    msg = await message.answer(
        "Оберіть продукт:",
        reply_markup=products_kb(products)
    )
    await state.set_state(CalcFSM.product)
    await state.update_data(message_ids=[msg.message_id])  # зберігаємо id для видалення пізніше


# --- Вибір продукту ---
@router.callback_query(CalcFSM.product)
async def select_product(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data["message_ids"].append(callback.message.message_id)
    await state.update_data(data)

    await state.update_data(product=callback.data)

    msg = await callback.message.answer("Введіть кількість:")
    data = await state.get_data()
    data["message_ids"].append(msg.message_id)
    await state.update_data(data)

    await state.set_state(CalcFSM.quantity)
    await callback.answer()


# --- Введення кількості ---
@router.message(CalcFSM.quantity)
async def enter_quantity(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введіть число")
        return

    await state.update_data(quantity=int(message.text))

    # Додаємо id цього повідомлення
    data = await state.get_data()
    data["message_ids"].append(message.message_id)
    await state.update_data(data)

    async with AsyncSessionLocal() as session:
        materials = (await session.execute(select(Material))).scalars().all()

    msg = await message.answer(
        "Оберіть матеріал:",
        reply_markup=materials_kb(materials)
    )
    data = await state.get_data()
    data["message_ids"].append(msg.message_id)
    await state.update_data(data)

    await state.set_state(CalcFSM.material)


# --- Вибір матеріалу ---
@router.callback_query(CalcFSM.material)
async def select_material(callback: CallbackQuery, state: FSMContext):
    await state.update_data(material=callback.data)

    async with AsyncSessionLocal() as session:
        modifiers = (await session.execute(select(Modifier))).scalars().all()

    msg = await callback.message.answer(
        "Оберіть додаткові послуги (можна кілька):",
        reply_markup=modifiers_kb(modifiers, selected_codes=[])
    )
    data = await state.get_data()
    data["message_ids"].append(msg.message_id)
    await state.update_data(data)

    await state.update_data(modifiers=[])
    await state.set_state(CalcFSM.modifiers)
    await callback.answer()


# --- Вибір модифікаторів ---
@router.callback_query(CalcFSM.modifiers)
async def select_modifiers(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("modifiers", [])

    if callback.data == "done":
        async with AsyncSessionLocal() as session:
            # Розрахунок ціни
            result = await calculate_price(
                session=session,
                product_code=data["product"],
                quantity=data["quantity"],
                material_code=data["material"],
                modifier_codes=selected
            )

            # Отримуємо об'єкти для відображення назв
            product_obj = (await session.execute(
                select(Product).where(Product.code == data['product'])
            )).scalar_one()
            material_obj = (await session.execute(
                select(Material).where(Material.code == data['material'])
            )).scalar_one()
            modifiers_objs = (await session.execute(
                select(Modifier).where(Modifier.code.in_(selected))
            )).scalars().all()
        modifiers_names = ", ".join([m.name for m in modifiers_objs]) if modifiers_objs else "немає"

        # --- Зберігаємо замовлення в БД ---
        async with AsyncSessionLocal() as session:
            from app.services.order_service import create_order  # твоя функція збереження
            await create_order(
                session=session,
                user_id=callback.from_user.id,
                product_id=product_obj.id,
                quantity=data['quantity'],
                material_id=material_obj.id,
                modifier_codes=selected,
                price=result['price'],
                deadline_days=result['deadline_days']
            )

        # Видаляємо всі проміжні повідомлення (включно з введеною кількістю)
        for msg_id in data.get("message_ids", []):
            try:
                await callback.message.bot.delete_message(
                    chat_id=callback.message.chat.id,
                    message_id=msg_id
                )
            except:
                pass

        # Відправляємо результат новим повідомленням
        await callback.message.answer(
            f"🖨 Продукт: {product_obj.name}\n"
            f"🔢 Кількість: {data['quantity']}\n"
            f"📄 Матеріал: {material_obj.name}\n"
            f"⚙️ Додаткові послуги: {modifiers_names}\n\n"
            f"💰 Вартість: {result['price']} грн\n"
            f"⏱️ Термін: {result['deadline_days']} дн."
        )

        await state.clear()
        await callback.answer()
        return

    # Додаємо або видаляємо код модифікатора
    if callback.data in selected:
        selected.remove(callback.data)
    else:
        selected.append(callback.data)
    await state.update_data(modifiers=selected)

    # Динамічно оновлюємо клавіатуру
    async with AsyncSessionLocal() as session:
        modifiers = (await session.execute(select(Modifier))).scalars().all()
    await callback.message.edit_reply_markup(
        reply_markup=modifiers_kb(modifiers, selected)
    )
    await callback.answer()

