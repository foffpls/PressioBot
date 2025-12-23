from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def products_kb(products):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=p.name, callback_data=p.code)]
            for p in products
        ]
    )

def materials_kb(materials):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=m.name, callback_data=m.code)]
            for m in materials
        ]
    )


def modifiers_kb(modifiers, selected_codes: list[str]):
    keyboard = []
    for m in modifiers:
        text = f"{'✅ ' if m.code in selected_codes else ''}{m.name}"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=m.code)])

    # Кнопка завершення
    keyboard.append([InlineKeyboardButton(text="Готово", callback_data="done")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
