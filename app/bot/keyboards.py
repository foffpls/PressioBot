from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def products_kb(products: List) -> InlineKeyboardMarkup:
    """
    Створює клавіатуру зі списком продуктів.
    
    Args:
        products: Список об'єктів Product з атрибутами name та code
    
    Returns:
        InlineKeyboardMarkup: Клавіатура з продуктами
    """
    if not products:
        return InlineKeyboardMarkup(inline_keyboard=[])
    
    keyboard = []
    for p in products:
        if not hasattr(p, 'name') or not hasattr(p, 'code'):
            continue
        # Перевірка обмеження Telegram на довжину callback_data (64 байти)
        code = str(p.code)
        if len(code.encode('utf-8')) > 64:
            continue
        keyboard.append([InlineKeyboardButton(text=p.name, callback_data=code)])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def materials_kb(materials: List) -> InlineKeyboardMarkup:
    """
    Створює клавіатуру зі списком матеріалів.
    
    Args:
        materials: Список об'єктів Material з атрибутами name та code
    
    Returns:
        InlineKeyboardMarkup: Клавіатура з матеріалами
    """
    if not materials:
        return InlineKeyboardMarkup(inline_keyboard=[])
    
    keyboard = []
    for m in materials:
        if not hasattr(m, 'name') or not hasattr(m, 'code'):
            continue
        # Перевірка обмеження Telegram на довжину callback_data (64 байти)
        code = str(m.code)
        if len(code.encode('utf-8')) > 64:
            continue
        keyboard.append([InlineKeyboardButton(text=m.name, callback_data=code)])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def modifiers_kb(modifiers: List, selected_codes: List[str]) -> InlineKeyboardMarkup:
    """
    Створює клавіатуру зі списком модифікаторів з можливістю множинного вибору.
    
    Args:
        modifiers: Список об'єктів Modifier з атрибутами name та code
        selected_codes: Список кодів вибраних модифікаторів
    
    Returns:
        InlineKeyboardMarkup: Клавіатура з модифікаторами та кнопкою "Готово"
    """
    keyboard = []
    
    if modifiers:
        for m in modifiers:
            if not hasattr(m, 'name') or not hasattr(m, 'code'):
                continue
            # Перевірка обмеження Telegram на довжину callback_data (64 байти)
            code = str(m.code)
            if len(code.encode('utf-8')) > 64:
                continue
            
            text = f"{'✅ ' if code in selected_codes else ''}{m.name}"
            keyboard.append([InlineKeyboardButton(text=text, callback_data=code)])

    # Кнопка завершення
    keyboard.append([InlineKeyboardButton(text="Готово", callback_data="done")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
