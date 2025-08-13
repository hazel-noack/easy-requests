import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)
load_dotenv()

from easy_requests import Connection, SilentConnection, init_cache


if __name__ == "__main__":
    c = Connection(warning_status_codes={200,}, cache_enabled=False)
    r = c.get("https://google.com")

    print(r.status_code)