from sqlalchemy import String, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    price_multiplier: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
