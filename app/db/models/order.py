# from sqlalchemy import Integer, Numeric, ForeignKey, BigInteger
# from sqlalchemy.orm import Mapped, mapped_column
# from app.db.base import Base
#
# class Order(Base):
#     __tablename__ = "orders"
#
#     id: Mapped[int] = mapped_column(primary_key=True)
#     user_id: Mapped[int] = mapped_column(BigInteger)
#     product_id: Mapped[int] = mapped_column(
#         ForeignKey("products.id")
#     )
#     quantity: Mapped[int] = mapped_column(Integer, nullable=False)
#     final_price: Mapped[float] = mapped_column(Numeric(10, 2))
#     final_deadline_days: Mapped[int] = mapped_column(Integer)

from sqlalchemy import String, Integer, Numeric, ForeignKey, DateTime, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.base import Base

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Telegram user id
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), nullable=False)
    modifiers: Mapped[str] = mapped_column(String, default="")  # список кодів через кому
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    deadline_days: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product = relationship("Product")
    material = relationship("Material")