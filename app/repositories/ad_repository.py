import asyncpg

from app.telemetry.metrics import DB_QUERY_DURATION


class AdRepository:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def create(
        self,
        user_id: int,
        name: str,
        description: str,
        category: int,
        images_qty: int = 0,
    ) -> int:
        async with self._pool.acquire() as conn:
            with DB_QUERY_DURATION.labels(query_type="insert").time():
                return await conn.fetchval(
                    """
                    INSERT INTO ads (user_id, name, description, category, images_qty)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                    """,
                    user_id,
                    name,
                    description,
                    category,
                    images_qty,
                )

    async def get_with_user_by_id(self, item_id: int) -> asyncpg.Record | None:
        async with self._pool.acquire() as conn:
            with DB_QUERY_DURATION.labels(query_type="select").time():
                return await conn.fetchrow(
                    """
                    SELECT a.id, a.images_qty, a.description, a.category, u.is_verified
                    FROM ads a
                    JOIN users u ON a.user_id = u.id
                    WHERE a.id = $1
                    """,
                    item_id,
                )
