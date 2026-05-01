from datetime import datetime
from random import randint
from uuid import uuid4

from app.database.models.product import Product
from app.database.models.review import Review
from app.database.models.user import User
from app.schemas.review import NewReviewData, ReviewUpdateData
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


def review_update_data_factory(
    text: str | None = "updated_review_text",
    new_rating: int | None = None,
):
    return ReviewUpdateData(
        text=text,
        product_rating=new_rating if new_rating is not None else randint(1, 5),
    )
