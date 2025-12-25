import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession
)
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Отримуємо змінні оточення з перевіркою на None
DB_USER = os.getenv('DB_USER') or ''
DB_PASSWORD = os.getenv('DB_PASSWORD') or ''
DB_HOST = os.getenv('DB_HOST') or 'localhost'
DB_PORT = os.getenv('DB_PORT') or '5432'
DB_NAME = os.getenv('DB_NAME') or ''

# Перевірка обов'язкових змінних
if not all([DB_USER, DB_PASSWORD, DB_NAME]):
    raise ValueError(
        "Не встановлено обов'язкові змінні оточення: "
        "DB_USER, DB_PASSWORD, DB_NAME"
    )

DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:"
    f"{DB_PASSWORD}@"
    f"{DB_HOST}:"
    f"{DB_PORT}/"
    f"{DB_NAME}"
)

# Використовуємо змінну оточення для контролю echo (для продакшену встановити DB_ECHO=false)
DB_ECHO = os.getenv('DB_ECHO', 'false').lower() == 'true'

# Налаштування connection pool
POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '5'))
MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '10'))
POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))

engine = create_async_engine(
    DATABASE_URL,
    echo=DB_ECHO,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_pre_ping=True,  # Перевірка з'єднань перед використанням
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
