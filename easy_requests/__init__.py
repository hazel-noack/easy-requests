import pathlib
from .connections import Connection, SilentConnection


__name__ = "easy_requests"
__folder__ = str(pathlib.Path(__file__).parent)
__all__ = [
    "Connection", 
    "SilentConnection",
]
