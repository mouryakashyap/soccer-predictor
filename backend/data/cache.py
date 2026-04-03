"""
Simple in-process TTL cache. No external dependencies.
Wrap any function with @ttl_cache(seconds=N) to cache its return value.
Thread-safe: concurrent callers with the same key wait for the first
execution to complete rather than all triggering redundant work.
"""
import threading
import time
from functools import wraps
from typing import Any, Dict, Tuple

_store: Dict[Tuple, Dict[str, Any]] = {}
_locks: Dict[Tuple, threading.Lock] = {}
_meta_lock = threading.Lock()


def _get_lock(key: Tuple) -> threading.Lock:
    with _meta_lock:
        if key not in _locks:
            _locks[key] = threading.Lock()
        return _locks[key]


def ttl_cache(seconds: int):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = (fn.__qualname__, args, tuple(sorted(kwargs.items())))
            entry = _store.get(key)
            if entry and (time.monotonic() - entry["ts"]) < seconds:
                return entry["val"]
            lock = _get_lock(key)
            acquired = lock.acquire(blocking=True, timeout=2)
            if not acquired:
                # Another thread is populating the cache (e.g. warm-up thread).
                # Run the function directly rather than waiting indefinitely —
                # the result will not be stored so the warmer's result wins.
                return fn(*args, **kwargs)
            try:
                # Re-check after acquiring the lock — another thread may have
                # populated the cache while we were waiting.
                entry = _store.get(key)
                if entry and (time.monotonic() - entry["ts"]) < seconds:
                    return entry["val"]
                val = fn(*args, **kwargs)
                _store[key] = {"val": val, "ts": time.monotonic()}
                return val
            finally:
                lock.release()
        return wrapper
    return decorator


def invalidate_all():
    """Clear every cached entry (useful for testing)."""
    _store.clear()
