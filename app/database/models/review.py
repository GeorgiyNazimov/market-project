import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import UUID, ForeignKey, Index, String, Text, Integer, DateTime, Numeric, desc, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        Index(None, "created_at", "id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    text: Mapped[str] = mapped_column(String, nullable=False)
    product_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    agregated: Mapped[bool] = mapped_column(Boolean, nullable=True)