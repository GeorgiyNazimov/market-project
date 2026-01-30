from datetime import datetime
from uuid import uuid4
from app.database.models.product import Product
from app.database.models.review import Review
from app.database.models.user import User
from app.schemas.review import NewReviewData
from tests.factories.products import product_factory
from tests.factories.users import user_factory


def review_factory(
    text="text",
    rating=5,
    user:User | None = None,
    product:Product | None = None
) -> Review:
    return Review(
        id=uuid4(),
        text=text,
        product_rating=rating,
        user=user or user_factory(),
        product=product or product_factory(),
        created_at=datetime.utcnow()
    )

def new_review_data_factory(
    text="text",
    rating=5
):
    return NewReviewData(
        text=text,
        product_rating=rating
    )