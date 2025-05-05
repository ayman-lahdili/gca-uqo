from abc import ABCMeta, abstractmethod
import asyncio
from types import TracebackType
from typing import Literal
from typing_extensions import override
from cachetools import TTLCache

class BaseCache(metaclass=ABCMeta):
    """Base class for caches managed by a cache dependency."""

    @abstractmethod
    async def clear(self) -> None:
        """Invalidate the cache.

        Used primarily for testing.
        """


class UserLockManager:
    """Helper class for managing per-user locks.

    This should only be created by `PerUserCache`.  It is returned by the
    `PerUserCache.lock` method and implements the async context manager
    protocol.

    Parameters
    ----------
    general_lock
        Lock protecting the per-user locks.
    user_lock
        Per-user lock for a given user.
    """

    def __init__(
        self, general_lock: asyncio.Lock, user_lock: asyncio.Lock
    ) -> None:
        self._general_lock = general_lock
        self._user_lock = user_lock

    async def __aenter__(self) -> asyncio.Lock:
        async with self._general_lock:
            await self._user_lock.acquire()
            return self._user_lock

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> Literal[False]:
        self._user_lock.release()
        return False


class PerUserCache(BaseCache):
    """Base class for a cache with per-user locking.

    Notes
    -----
    There is a moderately complex locking structure at play here.  When
    there's a cache miss for data for a specific user, the goal is to block
    the expensive lookups or token creation for that user until the first
    requester either looks up the data or creates a new token, either way
    adding it to the cache.  Hopefully then subsequent requests that were
    blocked on the lock can be answered from the cache.

    There is therefore a dictionary of per-user locks, but since we don't know
    the list of users in advance, we have to populate those locks on the fly.
    It shouldn't be necessary to protect the dict of per-user locks with
    another lock because we only need to worry about asyncio concurrency, but
    since FastAPI does use a thread pool, err on the side of caution and use
    the same locking strategy that would be used for multithreaded code.

    Note that the per-user lock must be acquired before the general lock is
    released, so the `lock` method cannot simply return the per-user lock.  To
    see why, imagine that one code path retrieves the per-user lock in
    preparation for acquiring it, and then another code path calls `clear`.
    `clear` acquires the global lock and then deletes the per-user lock, but
    the first caller still has a copy of the per-user lock and thinks it's
    valid.  It may then take that per-user lock, but a third code path could
    also try to lock the same user and get a new per-user lock from the
    post-clearing cache.  Both the first and third code paths will think they
    have a lock and may conflict.  `UserLockManager` is used to handle this.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._user_locks: dict[str, asyncio.Lock] = {}

    @override
    async def clear(self) -> None:
        """Invalidate the cache.

        Used primarily for testing.  Calls the `initialize` method provided by
        derivative classes, with proper locking, to reinitialize the cache.
        """
        async with self._lock:
            for user, lock in list(self._user_locks.items()):
                async with lock:
                    del self._user_locks[user]
            self.initialize()

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the cache.

        This will be called by `clear` and should also be called by the
        derived class's ``__init__`` method.
        """

    async def lock(self, username: str) -> UserLockManager:
        """Return the per-user lock for locking.

        The return value should be used with ``async with`` to hold a lock
        around checking for a cached token and, if one is not found, creating
        and storing a new token.

        Parameters
        ----------
        username
            Per-user lock to hold.

        Returns
        -------
        UserLockManager
            Async context manager that will take the user lock.
        """
        async with self._lock:
            if username not in self._user_locks:
                lock = asyncio.Lock()
                self._user_locks[username] = lock
            return UserLockManager(self._lock, self._user_locks[username])
        
class UQOCache[S](PerUserCache):
    """A cache of LDAP data.

    Parameters
    ----------
    content
        The type of object being stored.
    """

    def __init__(self, content: type[S]) -> None:
        super().__init__()
        self._cache: TTLCache[str, S]
        self.initialize()

    def get(self, key: str) -> S | None:
        """Retrieve data from the cache.

        Parameters
        ----------
        username
            Username for which to retrieve data.

        Returns
        -------
        Any or None
            The cached data or `None` if there is no data in the cache.
        """
        return self._cache.get(key)

    @override
    def initialize(self) -> None:
        """Initialize the cache."""
        self._cache = TTLCache(1024, 10)

    def invalidate(self, key: str) -> None:
        del self._cache[key]

    def store(self, key: str, data: S) -> None:
        """Store data in the cache.

        Should only be called with the lock held.

        Parameters
        ----------
        key
            key for which to store data.
        data
            Data to store.
        """
        self._cache[key] = data

    
