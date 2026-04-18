from datetime import datetime
from random import randint
from typing import List
from uuid import uuid4

from app.database.models.product import Product
from app.database.models.review import Review
from app.database.models.user import User
from app.schemas.product import NewReviewData
from tests.factories.products import product_factory
from tests.factories.users import user_factory


def review_factory(
    rating: int = 5, user: User | None = None, product: Product | None = None, **kwargs
) -> Review:
    return Review(
        id=kwargs.get("id", uuid4()),
        text=kwargs.get("text", "review text"),
        product_rating=rating,
        user=user or user_factory(),
        product=product or product_factory(),
        created_at=kwargs.get("created_at", datetime.utcnow()),
    )


def new_review_data_factory(text: str = "text", rating: int = 5):
    return NewReviewData(text=text, product_rating=rating)


def multiple_products_factory(count: int = 2) -> List[Review]:
    base_time = datetime.utcnow()
    return [
        Review(
            id=uuid4(),
            text="text",
            product_rating=randint(1, 5),
            user=user or user_factory(),
            product=product or product_factory(),
            created_at=datetime.utcnow() + timedelta(i),
        )
        for i in range(count)
    ]
