from .cache import init_cache
from .connections import Connection, SilentConnection


__name__ = "easy_requests"
__all__ = [
    "init_cache",
    "Connection", 
    "SilentConnection",
]
