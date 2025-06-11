import argparse
import logging

from .connections import Connection


def cli():
    parser = argparse.ArgumentParser(
        description="A Python library for simplified HTTP requests, featuring rate limiting, browser-like headers, and automatic retries. Built on the official `requests` library for reliability.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Sets the logging level to debug."
    )

    args = parser.parse_args()

    # Configure logging based on the debug flag
    if args.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.debug("Debug logging enabled")
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )


    c = Connection()
    c.generate_headers()
    print(c.session.headers)

    


if __name__ == "__main__":
    cli()
