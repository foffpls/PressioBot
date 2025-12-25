import asyncio
import os
import logging
import signal
from logging.handlers import RotatingFileHandler
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from app.bot.handlers import calc, order
from app.db.session import engine

# Створюємо папку для логів, якщо її немає
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Налаштування рівня логування зі змінної оточення
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, LOG_LEVEL, logging.INFO)

# Формат логів
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Налаштування логування
# Консольний handler (завжди активний)
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

# Файловий handler з ротацією
# Максимальний розмір файлу: 10 МБ, зберігаємо 5 резервних копій
log_file = LOG_DIR / "bot.log"
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10 * 1024 * 1024,  # 10 МБ
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(log_level)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

# Налаштування root logger
logging.basicConfig(
    level=log_level,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[console_handler, file_handler]
)

logger = logging.getLogger(__name__)
logger.info(f"Логування налаштовано. Рівень: {LOG_LEVEL}. Файл: {log_file.absolute()}")

bot: Bot | None = None
dp: Dispatcher | None = None


async def on_startup():
    """Виконується при запуску бота"""
    logger.info("Бот запущено")


async def on_shutdown():
    """Виконується при завершенні роботи бота"""
    logger.info("Завершення роботи бота...")
    # Закриваємо з'єднання з БД
    await engine.dispose()
    logger.info("З'єднання з БД закрито")


async def main():
    """
    Головна функція запуску бота.
    
    Налаштовує бота, реєструє роутери та запускає polling.
    """
    global bot, dp
    
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN не встановлено в змінних оточення")
        return
    
    bot = Bot(token=bot_token)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Реєстрація роутерів
    dp.include_router(calc.router)
    dp.include_router(order.router)
    
    # Обробка подій
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    try:
        logger.info("Запуск polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Помилка при роботі бота: {e}", exc_info=True)
    finally:
        await on_shutdown()


def signal_handler(signum, frame):
    """
    Обробник сигналів для graceful shutdown.
    
    Args:
        signum: Номер сигналу
        frame: Поточний stack frame
    """
    logger.info(f"Отримано сигнал {signum}, завершення роботи...")
    # Aiogram автоматично обробить KeyboardInterrupt через polling
    # Тут просто логуємо подію


if __name__ == "__main__":
    # Реєстрація обробників сигналів для graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Отримано сигнал переривання")
    except Exception as e:
        logger.error(f"Критична помилка: {e}", exc_info=True)
