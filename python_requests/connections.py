from __future__ import annotations
from typing import Optional
import requests
from datetime import timedelta
from urllib.parse import urlparse, urlunsplit, ParseResult

from . import cache

class Connection:
    def __init__(
        self, 
        session: Optional[requests.Session] = None,
        cache_enable: bool = True,
        cache_expires_after: Optional[timedelta] = None
    ) -> None:
        self.session = session if session is not None else requests.Session()

        self.cache_enable = cache_enable
        self.cache_expires_after = cache_expires_after if cache_expires_after is not None else timedelta(hours=1)

    def generate_headers(self, referer: Optional[str] = None):
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
            "Connection": "keep-alive",
            "Accept-Language": "en-US,en;q=0.5",
        }

        if referer is not None:
            headers["Referer"] = referer

        self.session.headers.update(**headers)

    def send_request(self, request: requests.Request) -> requests.Response:
        url = request.url 
        if url is None:
            raise ValueError("can't send a request without url")
        if self.cache_enable and cache.has_cache(url):
            return cache.get_cache(url)
        
        response = self.session.send(request.prepare())
        if self.cache_enable:
            cache.write_cache(url, response)
        return response


    def get(self, url: str, headers: Optional[dict] = None, **kwargs) -> requests.Response:
        return self.send_request(requests.Request(
            'GET',
            url=url,
            headers=headers,
            **kwargs
        ))
    
    def post(self, url: str, headers: Optional[dict] = None, json: Optional[dict] = None, **kwargs) -> requests.Response:
        return self.send_request(requests.Request(
            'POST',
            url=url,
            headers=headers,
            json=json,
            **kwargs,
        ))
