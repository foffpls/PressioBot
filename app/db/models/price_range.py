from sqlalchemy import Integer, Numeric, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class PriceRange(Base):
    """
    Модель діапазону цін для продукту.
    
    Attributes:
        id: Унікальний ідентифікатор
        product_id: ID продукту
        range_from: Початок діапазону кількості (включно)
        range_to: Кінець діапазону кількості (включно)
        price: Ціна за весь діапазон
        product: Зв'язок з продуктом
    """
    __tablename__ = "price_ranges"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    range_from: Mapped[int] = mapped_column(Integer, nullable=False)
    range_to: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    product = relationship(
        "Product",
        back_populates="price_ranges"
    )
    
    __table_args__ = (
        Index('idx_price_range_product', 'product_id'),  # Для швидкого пошуку за продуктом
        Index('idx_price_range_quantity', 'product_id', 'range_from', 'range_to'),  # Для пошуку за кількістю
    )
