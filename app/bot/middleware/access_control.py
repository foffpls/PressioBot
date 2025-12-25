"""
Модуль для контролю доступу до команд бота.
"""
import os
import logging
from typing import Set, Optional

logger = logging.getLogger(__name__)

# Кеш для списку дозволених user_id (завантажується один раз)
_allowed_user_ids_cache: Optional[Set[int]] = None


def get_allowed_user_ids() -> Set[int]:
    """
    Отримує список дозволених user_id зі змінної оточення.
    Використовує кешування для оптимізації.
    
    Returns:
        Set[int]: Множина дозволених user_id
    """
    global _allowed_user_ids_cache
    
    # Повертаємо кешоване значення, якщо воно вже завантажено
    if _allowed_user_ids_cache is not None:
        return _allowed_user_ids_cache
    
    allowed_ids_str = os.getenv('ALLOWED_USER_IDS', '')
    if not allowed_ids_str:
        logger.warning("ALLOWED_USER_IDS не встановлено в змінних оточення - доступ заборонено всім")
        _allowed_user_ids_cache = set()
        return _allowed_user_ids_cache
    
    try:
        # Парсимо рядок з ID через кому (наприклад: "123456,789012,345678")
        allowed_ids = {
            int(user_id.strip())
            for user_id in allowed_ids_str.split(',')
            if user_id.strip().isdigit()
        }
        _allowed_user_ids_cache = allowed_ids
        logger.info(f"Завантажено {len(allowed_ids)} дозволених user_id для команди /order")
        return allowed_ids
    except ValueError as e:
        logger.error(f"Помилка при парсингу ALLOWED_USER_IDS: {e}")
        _allowed_user_ids_cache = set()
        return _allowed_user_ids_cache


def is_user_allowed(user_id: int) -> bool:
    """
    Перевіряє, чи дозволено користувачу використовувати команду /order.
    
    Args:
        user_id: ID користувача Telegram
    
    Returns:
        bool: True якщо користувач дозволений, False інакше
    """
    allowed_ids = get_allowed_user_ids()
    
    # Якщо список порожній, доступ заборонено всім
    if not allowed_ids:
        return False
    
    return user_id in allowed_ids


def reload_allowed_user_ids() -> None:
    """
    Скидає кеш дозволених user_id.
    Корисно для перезавантаження списку без перезапуску бота.
    """
    global _allowed_user_ids_cache
    _allowed_user_ids_cache = None
    logger.info("Кеш дозволених user_id скинуто")

