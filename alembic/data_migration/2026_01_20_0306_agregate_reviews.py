import asyncio
from collections import defaultdict
from datetime import datetime
from uuid import UUID
from sqlalchemy import select, tuple_, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection.session import get_session
from app.database.models.review import Review
from app.database.models.user import User
from app.database.models.product_avg_rating import ProductAverageRating
from app.schemas.review import NewReviewData

BATCH_SIZE = 1000

async def migrate_all_reviews():
    async for session in get_session():
        while True:
            results = (await session.execute(
                select(Review).where(Review.agregated.is_(None))
                .order_by(Review.created_at, Review.id)
                .limit(BATCH_SIZE)
            )).scalars().all()

            if not results:
                break

            batch_counts = defaultdict(lambda: [0, 0, 0, 0, 0])
            product_rating_sum = defaultdict(int)
            product_total_count = defaultdict(int)

            for review in results:
                rating = review.product_rating
                batch_counts[review.product_id][rating-1] += 1
                product_rating_sum[review.product_id] += rating
                product_total_count[review.product_id] += 1
            
            for product_id, counts in batch_counts.items():
                rating_sum = product_rating_sum[product_id]
                total = product_total_count[product_id]

                stmt = insert(ProductAverageRating).values(
                    product_id=product_id,
                    rating_1_count=counts[0],
                    rating_2_count=counts[1],
                    rating_3_count=counts[2],
                    rating_4_count=counts[3],
                    rating_5_count=counts[4],
                    rating_count=total,
                    avg_rating=rating_sum / total
                ).on_conflict_do_update(
                    index_elements=[ProductAverageRating.product_id],
                    set_={
                        "rating_1_count": ProductAverageRating.rating_1_count + counts[0],
                        "rating_2_count": ProductAverageRating.rating_2_count + counts[1],
                        "rating_3_count": ProductAverageRating.rating_3_count + counts[2],
                        "rating_4_count": ProductAverageRating.rating_4_count + counts[3],
                        "rating_5_count": ProductAverageRating.rating_5_count + counts[4],
                        "rating_count": ProductAverageRating.rating_count + total,
                        "avg_rating": (
                            (ProductAverageRating.avg_rating * ProductAverageRating.rating_count + rating_sum)
                            / (ProductAverageRating.rating_count + total)
                        )
                    }
                )

                await session.execute(stmt)
            
            update_stmt = (
                update(Review)
                .where(Review.id.in_([r.id for r in results]))
                .values(agregated=True)
            )
            await session.execute(update_stmt)

            await session.commit()

if __name__ == "__main__":
    asyncio.run(migrate_all_reviews())