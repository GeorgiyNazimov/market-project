import logging
from redis.asyncio import Redis, ConnectionPool
from app.api.dependencies import settings

logger = logging.getLogger("api.infra")

class RedisInfra:
    def __init__(self):
        self.cache_pool: ConnectionPool | None = None
        self.state_pool: ConnectionPool | None = None
        
        self.cache_client: Redis | None = None
        self.state_client: Redis | None = None

    def init_pools(self) -> None:
        self.cache_pool = ConnectionPool.from_url(
            settings.REDIS_CACHE_URL, max_connections=30, decode_responses=True
        )
        self.cache_client = Redis(connection_pool=self.cache_pool)
        
        self.state_pool = ConnectionPool.from_url(
            settings.REDIS_STATE_URL, max_connections=20, decode_responses=True
        )
        self.state_client = Redis(connection_pool=self.state_pool)
        
        logger.info("Both Redis pools (Cache & State) successfully initialized.")

    async def close_pools(self) -> None:
        if self.cache_pool:
            await self.cache_pool.disconnect()
        if self.state_pool:
            await self.state_pool.disconnect()
        logger.info("Both Redis pools successfully closed.")

redis_infra = RedisInfra()
