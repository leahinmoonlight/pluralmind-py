import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Self

import httpx

from ._config import config
from ._types import (
    CacheHit,
    System,
    TwitchId,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CachedSystem:
    system: System | None
    timestamp: float


class AsyncPluralmindClient:
    def __init__(self) -> None:
        self._httpx = httpx.AsyncClient(base_url='https://pluralmind.chat/api/v2', timeout=5)
        self._pending_fetches: dict[TwitchId, asyncio.Task[System | None]] = {}
        self._system_cache: dict[TwitchId, CachedSystem] = {}

    def get_cached_system(self, id: TwitchId) -> CacheHit | None:
        """
        Retrieves the previously cached system data, along with whether the
        data should be considered expired. Returns None if no cached data
        exists for the given id.
        """
        cached = self._system_cache.get(id)
        if not cached:
            return

        return CacheHit(
            system=cached.system,
            expired=time.time() - cached.timestamp >= config.cache_duration,
        )

    async def _fetch_system(self, id: TwitchId) -> System | None:
        try:
            response = await self._httpx.get(f'/system/{id}')
            if response.status_code == 404:
                return None

            response.raise_for_status()
            return response.json()
        finally:
            self._pending_fetches.pop(id, None)

    def load_system(self, id: TwitchId) -> asyncio.Task[System | None]:
        """
        Loads information about a system from the Pluralmind API.
        When called with an ID that is already being loaded, that initial
        call's task will be reused rather than starting another load.
        Note: You generally should not need to call this directly. It is
        recommended to use `get_system` instead since that handles caching.
        """
        # Check if there's already a pending fetch for this system
        if id in self._pending_fetches:
            return self._pending_fetches[id]

        self._pending_fetches[id] = asyncio.create_task(self._fetch_system(id))
        return self._pending_fetches[id]

    async def get_system(self, id: TwitchId) -> System | None:
        """
        Returns information about a system for a given Twitch ID or username,
        or None if no system is associated with the given ID.
        This attempts to use cached data first, but will load fresh data if no
        cached data exists, or the cached data is expired.
        Note: This function will never raise an exception. If an API request
        fails, it will fall back to cached data, or return None if no cached
        data exists.
        """
        # Check if we already have a fresh enough copy of this system
        cache_hit = self.get_cached_system(id)
        if cache_hit and not cache_hit.expired:
            return cache_hit.system

        # Load the system's info fresh
        try:
            system = await self.load_system(id)
            self._system_cache[id] = CachedSystem(system=system, timestamp=time.time())
            return system
        except (httpx.HTTPError, ValueError):
            # The request failed, return whatever cached data we had
            logger.warning('Failed to load system for %s', id, exc_info=True)
            return cache_hit.system if cache_hit else None

    async def aclose(self) -> None:
        await self._httpx.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc) -> None:
        await self.aclose()
