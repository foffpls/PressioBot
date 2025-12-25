from datetime import datetime
from sqlalchemy import Integer, Numeric, ForeignKey, BigInteger, String, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Order(Base):
    """
    Модель замовлення поліграфії.
    
    Attributes:
        id: Унікальний ідентифікатор замовлення
        user_id: ID користувача Telegram
        product_id: ID продукту
        material_id: ID матеріалу
        quantity: Кількість одиниць
        price: Загальна ціна замовлення
        deadline_days: Термін виконання в днях
        modifiers: Список кодів модифікаторів через кому
        created_at: Дата та час створення замовлення
        product: Зв'язок з продуктом
        material: Зв'язок з матеріалом
    """
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    price: Mapped[float] = mapped_column(Numeric(10, 2))
    deadline_days: Mapped[int] = mapped_column(Integer)

    modifiers: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    product = relationship("Product")
    material = relationship("Material")
    
    __table_args__ = (
        Index('idx_order_created_at', 'created_at'),  # Для швидкого пошуку за датою
        Index('idx_order_user_id', 'user_id'),  # Для пошуку замовлень користувача
        Index('idx_order_user_created', 'user_id', 'created_at'),  # Композитний індекс
    )