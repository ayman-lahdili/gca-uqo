from abc import ABC, abstractmethod
import asyncio
from datetime import timedelta
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
        self._cache: Dict[str, tuple[T, float]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()
        self._ttl = ttl_seconds
        self._max_size = max_size
        # For tracking LRU
        self._access_times: Dict[str, float] = {}

    async def get_or_create(self, key: str, creator_func) -> T:
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
        # Fast path: Check if the item is in the cache without acquiring the lock
        value = self._get(key)
        if value is not None:
            return value

        # Get or create the lock for this key
        key_lock = await self._get_or_create_lock(key)

        # Acquire the lock for this specific key
        async with key_lock:
            # Check again in case another task added the item while we were waiting
            value = self._get(key)
            if value is not None:
                return value

            # Create the value
            result = await creator_func()

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
        import time

        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                # Update access time for LRU tracking
                self._access_times[key] = time.time()
                return value

            # Expired item, remove it
            del self._cache[key]
            if key in self._access_times:
                del self._access_times[key]

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
        import time

        async with self._global_lock:
            # Check if we need to evict items
            if len(self._cache) >= self._max_size:
                self._evict_lru()

            expiry = time.time() + self._ttl
            self._cache[key] = (value, expiry)
            self._access_times[key] = time.time()

            # Clean up the lock if it exists and isn't being used
            # This helps prevent unbounded growth of the locks dictionary
            if key in self._locks and not self._locks[key].locked():
                # Keep the lock if the key is in the cache to avoid recreation for active keys
                pass

    def _evict_lru(self) -> None:
        """Evict the least recently used items from the cache."""
        if not self._access_times:
            return

        # Find oldest accessed key
        oldest_key = min(self._access_times.items(), key=lambda x: x[1])[0]

        # Remove from cache and access times
        if oldest_key in self._cache:
            del self._cache[oldest_key]
        if oldest_key in self._access_times:
            del self._access_times[oldest_key]

        # Clean up the lock if it exists and isn't being used
        if oldest_key in self._locks and not self._locks[oldest_key].locked():
            del self._locks[oldest_key]

    async def invalidate(self, key: str) -> None:
        """Invalidate a specific cache entry.

        Parameters
        ----------
        key : str
            The cache key to invalidate.
        """
        async with self._global_lock:
            if key in self._cache:
                del self._cache[key]
            if key in self._access_times:
                del self._access_times[key]

    async def clear(self) -> None:
        """Clear the entire cache."""
        async with self._global_lock:
            self._cache.clear()
            self._access_times.clear()

            # Only clear locks that aren't currently held
            for key in list(self._locks.keys()):
                if not self._locks[key].locked():
                    del self._locks[key]
