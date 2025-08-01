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
from python_requests import Connection, set_cache_directory

set_cache_directory("/tmp/your-project")
connection = Connection()

response = connection.get("https://example.com")
```

### Using with Cloudscraper

```python
from python_requests import Connection, set_cache_directory
import cloudscraper

set_cache_directory("/tmp/your-project")
connection = Connection(cloudscraper.create_scraper())

response = connection.get("https://example.com")
```

## License

This project is licensed under the [**🏳️‍🌈 Opinionated Queer License v1.2**](https://oql.avris.it/license). So use is strictly prohibited for cops, military and everyone who actively works against human rights.