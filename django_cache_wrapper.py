import logging
import time
import traceback
from functools import wraps
from typing import Callable, Optional, List, Any

from django.conf import settings
from django.core.cache import caches

logger = logging.getLogger(__name__)

def cache_result(
    cache_key: Optional[str] = None,
    cache_kwarg_keys: Optional[List[str]] = None,
    seconds: int = 900,
    cache_filter: Callable[[Any], bool] = lambda x: True,
    cache_setup: str = "default",
):
    """
    A decorator for caching function results using Django's caching framework.
    :param cache_key: A fixed key for caching the result (if provided, ignores `cache_kwarg_keys`).
    :param cache_kwarg_keys: A list of argument keys to generate a dynamic cache key.
    :param seconds: Cache expiration time in seconds (default: 900 seconds / 15 minutes).
    :param cache_filter: A function to determine if a result should be cached.
    :param cache_setup: Cache configuration alias from Django's settings.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not getattr(settings, "USE_CACHE", False):
                return func(*args, **kwargs)

            try:
                cache_conn = caches[cache_setup]
            except Exception as e:
                logger.warning("Cache setup failed: %s", str(e))
                return func(*args, **kwargs)

            final_cache_key = generate_cache_key_for_method(func, kwargs, args, cache_kwarg_keys, cache_key)

            try:
                result = cache_conn.get(final_cache_key)
                if result is not None:
                    if not cache_filter(result):
                        logger.debug("Cache hit, but result failed filter check: %s", final_cache_key)
                        return func(*args, **kwargs)
                    return result
            except Exception as e:
                logger.exception("Cache retrieval failed: %s", traceback.format_exc())

            # Compute and store result if not cached
            result = func(*args, **kwargs)
            if cache_filter(result):
                try:
                    cache_conn.set(final_cache_key, result, seconds)
                except Exception as e:
                    logger.exception("Cache storage failed: %s", traceback.format_exc())

            return result
        return wrapper
    return decorator

def generate_cache_key_for_method(
    method: Callable, 
    method_kwargs: dict, 
    method_args: tuple, 
    cache_kwarg_keys: Optional[List[str]] = None, 
    cache_key: Optional[str] = None
) -> str:
    """Generates a unique cache key based on method name and arguments."""
    import pickle

    if cache_key:
        return f"{method.__module__}::{method.__name__}::{cache_key}"

    if cache_kwarg_keys:
        if method_args:
            raise ValueError("cache_kwarg_keys mode requires keyword arguments only; args should be empty")
        cache_values = [method_kwargs.get(key) for key in cache_kwarg_keys]
        return f"{method.__module__}::{method.__name__}::{hash(pickle.dumps(cache_values))}"

    key_parts = [method.__module__, method.__name__]
    if method_args:
        key_parts.append(str(hash(pickle.dumps(method_args))))
    if method_kwargs:
        key_parts.append(str(hash(pickle.dumps(method_kwargs))))

    return "::".join(key_parts)
