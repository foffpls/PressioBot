from sqlalchemy import Integer, Numeric, ForeignKey, BigInteger, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    price: Mapped[float] = mapped_column(Numeric(10, 2))
    deadline_days: Mapped[int] = mapped_column(Integer)

    modifiers: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(DateTime, server_default=func.now())

    product = relationship("Product")
    material = relationship("Material")