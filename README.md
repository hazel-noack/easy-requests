# Easy-Requests

![publishing workflow](https://github.com/hazel-noack/easy-requests/actions/workflows/python-publish.yml/badge.svg)

A Python library for simplified HTTP requests, featuring rate limiting, browser-like headers, and automatic retries. Built on the official `requests` library for reliability.

## Features

- Save responses to cache
- Use any session (e.g., bypass Cloudflare using [cloudscraper](https://pypi.org/project/cloudscraper/))
- Configurable wait between requests without thread blocking
- Automatic retries for failed requests

```bash
pip install easy-requests
```

## Usage

### Basic Usage

```python
from easy_requests import Connection, init_cache
 
init_cache(".cache")

connection = Connection()
# to generate headers that mimic the browser
connection.generate_headers()

response = connection.get("https://example.com")
```

### Using with Cloudscraper

```python
from easy_requests import Connection
import cloudscraper

connection = Connection(cloudscraper.create_scraper())
response = connection.get("https://example.com")
```

### Configuring cache

This won't use caching without you configuring it. 

You can configure the default cache either with environment variables or using `init_cache`. The env keys are `EASY_REQUESTS_CACHE_DIR` and `EASY_REQUESTS_CACHE_EXPIRES` (in days).

```py
from easy_requests import init_cache

init_cache(".cache")
```

Alternatively you can pass arguments into `Connection(...)` and the request function:

- `cache_enabled: Optional[bool]`
- `cache_directory: Optional[str]`
- `cache_expires_after: Optional[timedelta]`

```py
from easy_requests import Connection

Connection(
    cache_enabled = True
)
```

If you pass in `cache_enabled=True` it will raise a Value error if no cache directory was found.
