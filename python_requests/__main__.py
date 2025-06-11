import argparse
import logging

from . import Connection, clean_cache, clear_cache, set_cache_directory, get_cache_stats, __folder__


def main():
    c = Connection(cache_enable=False, request_delay=1.5, rate_limit_status_codes={200})
    c.generate_headers()

    print(c.get("http://www.does_not_exist.xyz"))


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

    # Cache management subcommands
    subparsers = parser.add_subparsers(dest='cache_command', help='Cache management commands')

    # Show cache stats
    show_parser = subparsers.add_parser('show-cache', help='Show cache statistics')
    show_parser.set_defaults(func=handle_show_cache)

    # Clean cache (expired entries)
    clean_parser = subparsers.add_parser('clean-cache', help='Clean expired cache entries')
    clean_parser.set_defaults(func=handle_clean_cache)

    # Clear cache (all entries)
    clear_parser = subparsers.add_parser('clear-cache', help='Clear ALL cache entries')
    clear_parser.set_defaults(func=handle_clear_cache)


    args = parser.parse_args()

    # Configure logging based on the debug flag
    if args.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.debug("Debug logging enabled")
        set_cache_directory("cache")
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        set_cache_directory()


    if hasattr(args, 'func'):
        args.func(args)
    else:
        main()


def handle_show_cache(args):
    """Handle the show-cache command"""
    try:
        file_count, db_count = get_cache_stats()
        logging.info(f"Cache Statistics:")
        logging.info(f"  - Files in cache: {file_count}")
        logging.info(f"  - Database entries: {db_count}")
    except Exception as e:
        logging.error(f"Failed to get cache statistics: {str(e)}")

def handle_clean_cache(args):
    """Handle the clean-cache command"""
    try:
        files_deleted, entries_deleted = clean_cache()
        logging.info(f"Cleaned cache:")
        logging.info(f"  - Files deleted: {files_deleted}")
        logging.info(f"  - Database entries removed: {entries_deleted}")
    except Exception as e:
        logging.error(f"Failed to clean cache: {str(e)}")

def handle_clear_cache(args):
    """Handle the clear-cache command"""
    try:
        # Confirm before clearing all cache
        confirm = input("Are you sure you want to clear ALL cache? This cannot be undone. [y/N]: ")
        if confirm.lower() == 'y':
            files_deleted, entries_deleted = clear_cache()
            logging.info(f"Cleared ALL cache:")
            logging.info(f"  - Files deleted: {files_deleted}")
            logging.info(f"  - Database entries removed: {entries_deleted}")
        else:
            logging.info("Cache clearing cancelled")
    except Exception as e:
        logging.error(f"Failed to clear cache: {str(e)}")


if __name__ == "__main__":
    cli()
