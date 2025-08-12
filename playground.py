import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)
load_dotenv()

from easy_requests import cache
from easy_requests import Connection, SilentConnection


if __name__ == "__main__":
    c = SilentConnection(
        cache_enabled=True
    )
    c.get("https://google.cum")