import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)
load_dotenv()

from easy_requests import Connection, SilentConnection, init_cache


if __name__ == "__main__":
    c = Connection(        
        request_delay=.3,
        additional_delay_per_try=1.5,
        warning_status_codes={403, },
        max_retries=1000
    )
    c.generate_headers()
    r = c.get("https://www.reddit.com/user/DasPrivate0/submitted.json?sort=new&limit=100&after=&count=0")

    print(r.status_code)