from sqlalchemy import String, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Product(Base):
    """
    Модель продукту поліграфії.
    
    Attributes:
        id: Унікальний ідентифікатор
        code: Унікальний код продукту (використовується для пошуку)
        name: Назва продукту
        unit: Одиниця виміру
        base_deadline_days: Базовий термін виконання в днях
        price_ranges: Зв'язок з діапазонами цін
    """
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    base_deadline_days: Mapped[int] = mapped_column(Integer, nullable=False)

    price_ranges = relationship(
        "PriceRange",
        back_populates="product",
        cascade="all, delete"
    )
    
    __table_args__ = (
        Index('idx_product_code', 'code'),  # Додатковий індекс для швидкого пошуку
    )