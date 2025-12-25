import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from app.bot.states import CalcFSM
from app.bot.keyboards import products_kb, materials_kb, modifiers_kb
from app.db.session import AsyncSessionLocal
from app.db.models import Product, Material, Modifier
from app.db.repositories.product_repo import get_product_by_code
from app.db.repositories.material_repo import get_material_by_code
from app.db.repositories.modifier_repo import get_modifiers_by_codes
from app.services.price_engine import calculate_price
from app.services.order_service import create_order

logger = logging.getLogger(__name__)

router = Router()


# --- /start ---
@router.message(F.text == "/start")
async def start_bot(message: Message, state: FSMContext):
    """
    Обробляє команду /start - привітання та інструкції.
    
    Args:
        message: Повідомлення з командою
        state: FSM контекст
    """
    await state.clear()
    await message.answer(
        "👋 Привіт! Я бот-калькулятор поліграфії.\n"
        "Щоб розрахувати вартість, введіть команду /calc\n"
        "Щоб вивести список замовлень, введіть команду /order (лише адміністратор)\n"
        "Щоб скасувати поточну операцію, введіть /cancel"
    )


# --- /cancel ---
@router.message(F.text == "/cancel")
async def cancel_operation(message: Message, state: FSMContext):
    """
    Скасовує поточну операцію калькуляції.
    
    Args:
        message: Повідомлення з командою
        state: FSM контекст
    """
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("❌ Немає активної операції для скасування.")
        return
    
    await state.clear()
    await message.answer("✅ Операцію скасовано. Можете почати нову командою /calc")


# --- /calc ---
@router.message(F.text == "/calc")
async def start_calc(message: Message, state: FSMContext):
    """
    Запускає процес калькуляції ціни.
    
    Args:
        message: Повідомлення з командою
        state: FSM контекст для збереження стану
    """
    try:
        async with AsyncSessionLocal() as session:
            products = (await session.execute(select(Product))).scalars().all()
        
        if not products:
            await message.answer("❌ Наразі немає доступних продуктів.")
            return

        msg = await message.answer(
            "Оберіть продукт:",
            reply_markup=products_kb(products)
        )
        await state.set_state(CalcFSM.product)
        await state.update_data(message_ids=[msg.message_id])
    except Exception as e:
        logger.error(f"Помилка при запуску калькуляції: {e}", exc_info=True)
        await message.answer("❌ Виникла помилка. Спробуйте пізніше.")


# --- Вибір продукту ---
@router.callback_query(CalcFSM.product)
async def select_product(callback: CallbackQuery, state: FSMContext):
    """
    Обробляє вибір продукту користувачем.
    
    Args:
        callback: CallbackQuery з даними про вибір
        state: FSM контекст для збереження стану
    """
    try:
        # Перевірка наявності callback.data та callback.message
        if not callback.data:
            await callback.answer("❌ Помилка: дані не отримано", show_alert=True)
            return
        
        if not callback.message:
            logger.error("callback.message is None")
            return
        
        data = await state.get_data()
        message_ids = data.get("message_ids", [])
        
        # Обмеження на кількість збережених message_ids (максимум 50)
        MAX_MESSAGE_IDS = 50
        if len(message_ids) >= MAX_MESSAGE_IDS:
            message_ids = message_ids[-MAX_MESSAGE_IDS + 1:]  # Залишаємо останні
        
        message_ids.append(callback.message.message_id)
        
        # Валідація коду продукту
        async with AsyncSessionLocal() as session:
            product = await get_product_by_code(session, callback.data)
            if not product:
                await callback.answer("❌ Продукт не знайдено", show_alert=True)
                return
        
        await state.update_data(
            message_ids=message_ids,
            product=callback.data
        )

        msg = await callback.message.answer("Введіть кількість:")
        message_ids.append(msg.message_id)
        await state.update_data(message_ids=message_ids)

        await state.set_state(CalcFSM.quantity)
        await callback.answer()
    except Exception as e:
        logger.error(f"Помилка при виборі продукту: {e}", exc_info=True)
        await callback.answer("❌ Виникла помилка. Спробуйте ще раз.", show_alert=True)


# --- Введення кількості ---
@router.message(CalcFSM.quantity)
async def enter_quantity(message: Message, state: FSMContext):
    """
    Обробляє введення кількості користувачем.
    
    Args:
        message: Повідомлення з кількістю
        state: FSM контекст для збереження стану
    """
    try:
        if not message.text or not message.text.isdigit():
            await message.answer("❌ Введіть коректне число")
            return
        
        quantity = int(message.text)
        MIN_QUANTITY = 1
        MAX_QUANTITY = 1_000_000  # Максимальна кількість
        
        if quantity < MIN_QUANTITY:
            await message.answer(f"❌ Кількість повинна бути не менше {MIN_QUANTITY}")
            return
        
        if quantity > MAX_QUANTITY:
            await message.answer(f"❌ Кількість не може перевищувати {MAX_QUANTITY:,}")
            return

        data = await state.get_data()
        if "product" not in data:
            await message.answer("❌ Помилка: продукт не вибрано. Почніть спочатку /calc")
            await state.clear()
            return

        message_ids = data.get("message_ids", [])
        
        # Обмеження на кількість збережених message_ids
        MAX_MESSAGE_IDS = 50
        if len(message_ids) >= MAX_MESSAGE_IDS:
            message_ids = message_ids[-MAX_MESSAGE_IDS + 1:]
        
        message_ids.append(message.message_id)
        
        await state.update_data(
            quantity=quantity,
            message_ids=message_ids
        )

        async with AsyncSessionLocal() as session:
            materials = (await session.execute(select(Material))).scalars().all()
        
        if not materials:
            await message.answer("❌ Наразі немає доступних матеріалів.")
            await state.clear()
            return

        msg = await message.answer(
            "Оберіть матеріал:",
            reply_markup=materials_kb(materials)
        )
        message_ids.append(msg.message_id)
        await state.update_data(message_ids=message_ids)

        await state.set_state(CalcFSM.material)
    except Exception as e:
        logger.error(f"Помилка при введенні кількості: {e}", exc_info=True)
        await message.answer("❌ Виникла помилка. Спробуйте ще раз.")


# --- Вибір матеріалу ---
@router.callback_query(CalcFSM.material)
async def select_material(callback: CallbackQuery, state: FSMContext):
    """
    Обробляє вибір матеріалу користувачем.
    
    Args:
        callback: CallbackQuery з даними про вибір
        state: FSM контекст для збереження стану
    """
    try:
        # Перевірка наявності callback.data та callback.message
        if not callback.data:
            await callback.answer("❌ Помилка: дані не отримано", show_alert=True)
            return
        
        if not callback.message:
            logger.error("callback.message is None")
            return
        
        data = await state.get_data()
        if "quantity" not in data or "product" not in data:
            await callback.answer("❌ Помилка: дані не збережені. Почніть спочатку /calc", show_alert=True)
            await state.clear()
            return
        
        # Валідація коду матеріалу
        async with AsyncSessionLocal() as session:
            material = await get_material_by_code(session, callback.data)
            if not material:
                await callback.answer("❌ Матеріал не знайдено", show_alert=True)
                return
            
            modifiers = (await session.execute(select(Modifier))).scalars().all()

        message_ids = data.get("message_ids", [])
        
        # Обмеження на кількість збережених message_ids
        MAX_MESSAGE_IDS = 50
        if len(message_ids) >= MAX_MESSAGE_IDS:
            message_ids = message_ids[-MAX_MESSAGE_IDS + 1:]
        
        await state.update_data(
            material=callback.data,
            modifiers=[],
            message_ids=message_ids
        )

        msg = await callback.message.answer(
            "Оберіть додаткові послуги (можна кілька):",
            reply_markup=modifiers_kb(modifiers, selected_codes=[])
        )
        message_ids.append(msg.message_id)
        await state.update_data(message_ids=message_ids)

        await state.set_state(CalcFSM.modifiers)
        await callback.answer()
    except Exception as e:
        logger.error(f"Помилка при виборі матеріалу: {e}", exc_info=True)
        await callback.answer("❌ Виникла помилка. Спробуйте ще раз.", show_alert=True)


# --- Вибір модифікаторів ---
@router.callback_query(CalcFSM.modifiers)
async def select_modifiers(callback: CallbackQuery, state: FSMContext):
    """
    Обробляє вибір модифікаторів та завершення калькуляції.
    
    Args:
        callback: CallbackQuery з даними про вибір
        state: FSM контекст для збереження стану
    """
    try:
        # Перевірка наявності callback.data та callback.message
        if not callback.data:
            await callback.answer("❌ Помилка: дані не отримано", show_alert=True)
            return
        
        if not callback.message:
            logger.error("callback.message is None")
            return
        
        data = await state.get_data()
        
        # Валідація наявності необхідних даних
        required_fields = ["product", "quantity", "material"]
        if not all(field in data for field in required_fields):
            await callback.answer("❌ Помилка: дані не збережені. Почніть спочатку /calc", show_alert=True)
            await state.clear()
            return
        
        selected = data.get("modifiers", [])

        if callback.data == "done":
            async with AsyncSessionLocal() as session:
                try:
                    # Розрахунок ціни
                    result = await calculate_price(
                        session=session,
                        product_code=data["product"],
                        quantity=data["quantity"],
                        material_code=data["material"],
                        modifier_codes=selected
                    )

                    # Отримуємо об'єкти для відображення назв через репозиторії
                    product_obj = await get_product_by_code(session, data['product'])
                    material_obj = await get_material_by_code(session, data['material'])
                    
                    if not product_obj:
                        raise ValueError("Продукт не знайдено")
                    if not material_obj:
                        raise ValueError("Матеріал не знайдено")
                    
                    modifiers_objs = await get_modifiers_by_codes(session, selected) if selected else []
                    modifiers_names = ", ".join([m.name for m in modifiers_objs]) if modifiers_objs else "немає"

                    # --- Зберігаємо замовлення в БД ---
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
                except ValueError as e:
                    logger.error(f"Помилка валідації при розрахунку: {e}")
                    await callback.answer(f"❌ {str(e)}", show_alert=True)
                    return
                except Exception as e:
                    logger.error(f"Помилка при розрахунку ціни: {e}", exc_info=True)
                    await callback.answer("❌ Помилка при розрахунку ціни. Спробуйте пізніше.", show_alert=True)
                    return

            # Видаляємо всі проміжні повідомлення
            message_ids = data.get("message_ids", [])
            if callback.message:
                for msg_id in message_ids:
                    try:
                        await callback.message.bot.delete_message(
                            chat_id=callback.message.chat.id,
                            message_id=msg_id
                        )
                    except Exception as e:
                        # Логуємо помилки видалення, але не зупиняємо виконання
                        logger.warning(f"Не вдалося видалити повідомлення {msg_id}: {e}")

            # Відправляємо результат новим повідомленням
            if callback.message:
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

        # Перевірка наявності callback.data
        if not callback.data:
            await callback.answer("❌ Помилка: дані не отримано", show_alert=True)
            return
        
        # Додаємо або видаляємо код модифікатора
        if callback.data in selected:
            selected.remove(callback.data)
        else:
            selected.append(callback.data)
        await state.update_data(modifiers=selected)

        # Динамічно оновлюємо клавіатуру
        try:
            async with AsyncSessionLocal() as session:
                modifiers = (await session.execute(select(Modifier))).scalars().all()
            
            if callback.message:
                await callback.message.edit_reply_markup(
                    reply_markup=modifiers_kb(modifiers, selected)
                )
        except Exception as e:
            logger.warning(f"Не вдалося оновити клавіатуру: {e}")
            # Спробуємо відправити нове повідомлення замість редагування
            if callback.message:
                await callback.message.answer(
                    "Оберіть додаткові послуги (можна кілька):",
                    reply_markup=modifiers_kb(modifiers, selected)
                )
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Помилка при виборі модифікаторів: {e}", exc_info=True)
        await callback.answer("❌ Виникла помилка. Спробуйте ще раз.", show_alert=True)
