import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)
load_dotenv()

from easy_requests import Connection, SilentConnection, init_cache


if __name__ == "__main__":
    c = Connection()
    c.get("https://google.cum")