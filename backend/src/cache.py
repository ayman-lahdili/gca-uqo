import asyncio
import time
from cachetools import TTLCache
from collections.abc import Callable, Awaitable
from typing import Dict, Generic, TypeVar, Optional, Any

T = TypeVar("T")


class AsyncCache(Generic[T]):
    """A simple, concurrent-safe cache implementation.

    This cache is designed to be used in async environments where multiple
    concurrent requests may be made for the same resource. It prevents
    multiple simultaneous requests from performing expensive operations for
    the same key (dog-pile effect) by using per-key locks.
    """

    def __init__(self, ttl_seconds: int = 300, max_size: int = 1000):
        """Initialize the cache.

        Parameters
        ----------
        ttl_seconds : int
            Time-to-live for cache entries in seconds.
        max_size : int
            Maximum number of entries in the cache.
        """
        self._cache: TTLCache[str, T] = TTLCache(maxsize=max_size, ttl=ttl_seconds)
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    async def get_or_create(self, key: str, creator_func: Callable[..., Awaitable]) -> T:
        """Get a value from the cache or create it if it doesn't exist.

        This method ensures that only one creator_func runs at a time for any given key,
        preventing redundant expensive operations.

        Parameters
        ----------
        key : str
            The cache key.
        creator_func : Callable
            An async function that creates the value if it's not in the cache.

        Returns
        -------
        T
            The cached or newly created value.
        """
        # Get or create the lock for this key
        key_lock = await self._get_or_create_lock(key)

        # Acquire the lock for this specific key
        async with key_lock:
            # Return if value exists
            value = self._get(key)
            if value is not None:
                return value

            # Create the value
            try:
                result = await creator_func()
            except:
                await self._cleanup_lock_if_unused(key)
                raise

            # Store in cache
            await self._store(key, result)
            return result

    def _get(self, key: str) -> Optional[T]:
        """Get a value from the cache if it exists and is not expired.

        Parameters
        ----------
        key : str
            The cache key.

        Returns
        -------
        Optional[T]
            The cached value or None if not found or expired.
        """
        try:
            return self._cache[key]
        except KeyError:
            return None

    async def _get_or_create_lock(self, key: str) -> asyncio.Lock:
        """Get or create a lock for the given key.

        Parameters
        ----------
        key : str
            The cache key.

        Returns
        -------
        asyncio.Lock
            The lock for the given key.
        """
        async with self._global_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            return self._locks[key]

    async def _store(self, key: str, value: T) -> None:
        """Store a value in the cache.

        Parameters
        ----------
        key : str
            The cache key.
        value : T
            The value to store.
        """
        async with self._global_lock:
            self._cache[key] = value

            # Clean up the lock if it exists and isn't being used
            # This helps prevent unbounded growth of the locks dictionary
            if key in self._locks and not self._locks[key].locked():
                # Keep the lock if the key is in the cache to avoid recreation for active keys
                pass
    
    async def _cleanup_lock_if_unused(self, key: str) -> None:
        async with self._global_lock:
            if key in self._locks and not self._locks[key].locked():
                if key not in self._cache:
                    del self._locks[key]

    async def invalidate(self, key: str) -> None:
        async with self._global_lock:
            self._cache.pop(key, None)

    async def clear(self) -> None:
        async with self._global_lock:
            self._cache.clear()
            for key in list(self._locks.keys()):
                if not self._locks[key].locked():
                    del self._locks[key]