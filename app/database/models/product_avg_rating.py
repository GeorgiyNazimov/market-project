import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import UUID, Float, ForeignKey, Index, String, Text, Integer, DateTime, Numeric, desc
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProductAverageRating(Base):
    __tablename__ = "product_average_ratings"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        primary_key=True
    )

    rating_1_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rating_2_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rating_3_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rating_4_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rating_5_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    rating_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_rating: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)