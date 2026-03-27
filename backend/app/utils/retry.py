"""API call retry mechanism with exponential backoff"""

import time
import random
import functools
from typing import Callable, Any, Optional, Type, Tuple
from .logger import get_logger

logger = get_logger('foresight.retry')


def retry_with_backoff(
    max_retries=3,
    initial_delay=1.0,
    max_delay=30.0,
    backoff_factor=2.0,
    jitter=True,
    exceptions=(Exception,),
    on_retry=None
):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(f"{func.__name__} failed after {max_retries} retries: {e}")
                        raise

                    current_delay = min(delay, max_delay)
                    if jitter:
                        current_delay *= (0.5 + random.random())

                    logger.warning(f"{func.__name__} attempt {attempt + 1} failed: {e}, retrying in {current_delay:.1f}s")

                    if on_retry:
                        on_retry(e, attempt + 1)

                    time.sleep(current_delay)
                    delay *= backoff_factor

            raise last_exception
        return wrapper
    return decorator
