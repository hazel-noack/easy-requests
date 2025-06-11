from __future__ import annotations
from typing import Optional
import requests
from urllib.parse import urlparse, urlunsplit, ParseResult

from . import cache

class Connection:
    def __init__(self, session: Optional[requests.Session] = None) -> None:
        self.session = session if session is not None else requests.Session()

    def generate_headers(self, referer: Optional[str] = None):
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
            "Connection": "keep-alive",
            "Accept-Language": "en-US,en;q=0.5",
        }

        if referer is not None:
            headers["Referer"] = referer

        self.session.headers.update(**headers)

    def get(self, url: str):
        if cache.has_cache(url):
            return cache.get_cache(url)

        resp = self.session.get(url)
        cache.write_cache(url, resp)
        return resp
