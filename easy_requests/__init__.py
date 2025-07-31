import pathlib
from .connections import Connection, SilentConnection
from .cache import clean_cache, clear_cache, set_cache_directory, get_cache_stats


__name__ = "python_requests"
__folder__ = str(pathlib.Path(__file__).parent)
__all__ = [
    "Connection", 
    "SilentConnection",
    "clean_cache",
    "clear_cache",
    "get_cache_stats",
    "set_cache_directory",
]
