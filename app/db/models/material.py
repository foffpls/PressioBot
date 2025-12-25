from sqlalchemy import String, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Material(Base):
    """
    Модель матеріалу для поліграфії.
    
    Attributes:
        id: Унікальний ідентифікатор
        code: Унікальний код матеріалу (використовується для пошуку)
        name: Назва матеріалу
        price_multiplier: Множник ціни (наприклад, 1.2 для +20%)
    """
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    price_multiplier: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    
    __table_args__ = (
        Index('idx_material_code', 'code'),  # Додатковий індекс для швидкого пошуку
    )
