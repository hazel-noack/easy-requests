import logging
logging.basicConfig(level=logging.DEBUG)

from dotenv import load_dotenv
load_dotenv()

from easy_requests import cache


print(cache.ROOT_CACHE.is_enabled)

cache.init_cache(".cache_yay")

print(cache.ROOT_CACHE.is_enabled)

