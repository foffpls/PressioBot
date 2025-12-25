from sqlalchemy import String, Integer, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Modifier(Base):
    """
    Модель модифікатора (додаткової послуги) для поліграфії.
    
    Attributes:
        id: Унікальний ідентифікатор
        code: Унікальний код модифікатора (використовується для пошуку)
        name: Назва модифікатора
        price_multiplier: Множник ціни (наприклад, 1.15 для +15%)
        deadline_modifier_days: Додаткові дні до терміну виконання
    """
    __tablename__ = "modifiers"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    price_multiplier: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    deadline_modifier_days: Mapped[int] = mapped_column(Integer, default=0)
    
    __table_args__ = (
        Index('idx_modifier_code', 'code'),  # Додатковий індекс для швидкого пошуку
    )
