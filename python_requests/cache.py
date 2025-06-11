from codecs import encode
from hashlib import sha1
from pathlib import Path
import requests
import pickle

from . import CACHE_DIRECTORY


def get_url_hash(url: str) -> str:
    return sha1(encode(url.strip(), "utf-8")).hexdigest()


def get_url_file(url: str) -> Path:
    return Path(CACHE_DIRECTORY, f"{get_url_hash(url)}.request")


def has_cache(url: str) -> bool:
    return get_url_file(url).exists()


def get_cache(url: str) -> requests.Response:
    with get_url_file(url).open("rb") as cache_file:
        return pickle.load(cache_file)


def write_cache(url: str, resp: requests.Response):
    with get_url_file(url).open("wb") as url_file:
        pickle.dump(resp, url_file)
