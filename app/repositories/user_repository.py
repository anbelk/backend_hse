import asyncpg

from app.telemetry.metrics import DB_QUERY_DURATION


class UserRepository:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def create(self, is_verified: bool = False) -> int:
        async with self._pool.acquire() as conn:
            with DB_QUERY_DURATION.labels(query_type="insert").time():
                return await conn.fetchval(
                    "INSERT INTO users (is_verified) VALUES ($1) RETURNING id",
                    is_verified,
                )

    async def get_by_id(self, user_id: int) -> asyncpg.Record | None:
        async with self._pool.acquire() as conn:
            with DB_QUERY_DURATION.labels(query_type="select").time():
                return await conn.fetchrow(
                    "SELECT id, is_verified FROM users WHERE id = $1",
                    user_id,
                )
