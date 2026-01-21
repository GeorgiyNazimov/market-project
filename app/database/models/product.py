import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import UUID, ForeignKey, String, Text, Integer, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    category: Mapped[Optional["Category"]] = relationship(back_populates="products")
    product_rating: Mapped[Optional["ProductAverageRating"]] = relationship("ProductAverageRating", uselist=False, lazy="raise")

    @property
    def avg_rating(self) -> float:
        return self.product_rating.avg_rating if self.product_rating else 0.0

    @property
    def rating_count(self) -> int:
        return self.product_rating.rating_count if self.product_rating else 0