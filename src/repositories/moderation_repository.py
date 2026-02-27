from datetime import datetime, timezone

import asyncpg


class ModerationRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create_pending(self, item_id: int) -> int:
        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                """
                INSERT INTO moderation_results (item_id, status)
                VALUES ($1, 'pending')
                RETURNING id
                """,
                item_id,
            )

    async def get_oldest_pending_by_item_id(self, item_id: int) -> int | None:
        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                """
                SELECT id FROM moderation_results
                WHERE item_id = $1 AND status = 'pending'
                ORDER BY created_at ASC
                LIMIT 1
                """,
                item_id,
            )

    async def get_by_id(self, task_id: int) -> asyncpg.Record | None:
        async with self._pool.acquire() as conn:
            return await conn.fetchrow(
                """
                SELECT id, item_id, status, is_violation, probability,
                       error_message, created_at, processed_at
                FROM moderation_results
                WHERE id = $1
                """,
                task_id,
            )

    async def update_completed(
        self, task_id: int, is_violation: bool, probability: float
    ) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE moderation_results
                SET status = 'completed', is_violation = $2, probability = $3,
                    processed_at = $4
                WHERE id = $1
                """,
                task_id,
                is_violation,
                probability,
                datetime.now(timezone.utc).replace(tzinfo=None),
            )

    async def update_failed(self, task_id: int, error_message: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE moderation_results
                SET status = 'failed', error_message = $2, processed_at = $3
                WHERE id = $1
                """,
                task_id,
                error_message,
                datetime.now(timezone.utc).replace(tzinfo=None),
            )
