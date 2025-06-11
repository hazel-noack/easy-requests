from __future__ import annotations
from typing import Optional, Set
import requests
from datetime import timedelta
import time
import logging

from . import cache


log = logging.getLogger(__name__)

class Connection:
    def __init__(
        self, 
        session: Optional[requests.Session] = None,
        cache_enable: bool = True,
        cache_expires_after: Optional[timedelta] = None,
        request_delay: float = 0,
        additional_delay_per_try: float = 1,
        error_status_codes: Optional[Set[int]] = None,
        rate_limit_status_codes: Optional[Set[int]] = None,
    ) -> None:
        self.session = session if session is not None else requests.Session()
        
        # cache related config
        self.cache_enable = cache_enable
        self.cache_expires_after = cache_expires_after if cache_expires_after is not None else timedelta(hours=1)

        # waiting between requests
        self.request_delay = request_delay
        self.additional_delay_per_try = additional_delay_per_try
        self.last_request: float = 0

        # response validation config
        self.error_status_codes = error_status_codes if error_status_codes is not None else {
            400,  # Bad Request
            401,  # Unauthorized
            403,  # Forbidden
            404,  # Not Found
            405,  # Method Not Allowed
            406,  # Not Acceptable
            410,  # Gone
            418,  # I'm a teapot
            422,  # Unprocessable Entity
            451,  # Unavailable For Legal Reasons
            500,  # Internal Server Error
            501,  # Not Implemented
            502,  # Bad Gateway
            503,  # Service Unavailable
            504,  # Gateway Timeout
        }
        
        self.rate_limit_status_codes = rate_limit_status_codes if rate_limit_status_codes is not None else {
            429,  # Too Many Requests
            509,  # Bandwidth Limit Exceeded
        }

    def generate_headers(self, referer: Optional[str] = None):
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
            "Connection": "keep-alive",
            "Accept-Language": "en-US,en;q=0.5",
        }

        if referer is not None:
            headers["Referer"] = referer

        self.session.headers.update(**headers)

    def validate_response(self, response: requests.Response) -> bool:
        """
        Validates the HTTP response and raises appropriate exceptions or returns True if successful.
        
        Args:
            response: The response object to validate
            
        Returns:
            bool: True if the response is valid (status code < 400 and not in error/rate limit codes)
            
        Raises:
            requests.HTTPError: For response status codes that indicate client or server errors
            RateLimitExceeded: For response status codes that indicate rate limiting
        """
        if response.status_code in self.error_status_codes:
            raise requests.HTTPError(
                f"Server returned error status code {response.status_code}: {response.reason}",
                response=response
            )
            
        if response.status_code in self.rate_limit_status_codes:
            return False
            
        # For any other 4xx or 5xx status codes not explicitly configured
        if response.status_code >= 400:
            raise requests.HTTPError(
                f"Server returned unexpected status code {response.status_code}: {response.reason}",
                response=response
            )
            
        return True

    def send_request(self, request: requests.Request, attempt: int = 0) -> requests.Response:
        url = request.url 
        if url is None:
            raise ValueError("can't send a request without url")
        if self.cache_enable and cache.has_cache(url):
            return cache.get_cache(url)
        
        current_delay = self.request_delay + (self.additional_delay_per_try * attempt)
        elapsed_time = time.time() - self.last_request
        to_wait = current_delay - elapsed_time

        if to_wait > 0:
            log.info(f"waiting {to_wait} at attempt {attempt}: {url}")
            time.sleep(to_wait)
        
        response = self.session.send(request.prepare())

        self.last_request = time.time()


        # TODO validate response and retrying if necessary 

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
