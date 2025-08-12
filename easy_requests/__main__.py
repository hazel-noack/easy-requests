from pathlib import Path
import argparse
import logging


def get_name(url: str) -> str:
    return url.split("/")[-1].split("?")[0]


def cli():
    parser = argparse.ArgumentParser(
        description="A Python library for simplified HTTP requests, featuring rate limiting, browser-like headers, and automatic retries. Built on the official `requests` library for reliability.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument('url', help='url to download')

    parser.add_argument(
        "--out", "-o",
        nargs='?',
        type=str,
        help="tells the program where to download to",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Sets the logging level to debug."
    )

    args = parser.parse_args()

    # Configure logging based on the debug flag
    if args.verbose:
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

    logger = logging.getLogger("easy_requests")

    url = args.url
    out_file = get_name(url) if args.out is None else args.out
    
    logger.info("downloading %s to %s", url, out_file)


    from .connections import Connection
    connection = Connection()
    connection.generate_headers(get_referer_from=url)
    
    res = connection.get(url)
    with Path(out_file).open("wb") as f:
        f.write(res.content)



if __name__ == "__main__":
    cli()
