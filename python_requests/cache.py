from codecs import encode
from hashlib import sha1
from pathlib import Path
import requests
import pickle
import sqlite3
from datetime import datetime

from . import CACHE_DIRECTORY


# SQLite database file path
DB_FILE = Path(CACHE_DIRECTORY, "cache_metadata.db")

# Initialize the database
def _init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS url_cache (
            url_hash TEXT PRIMARY KEY,
            last_updated TIMESTAMP
        )
        """)
        conn.commit()

# Initialize the database when module is imported
_init_db()


def get_url_hash(url: str) -> str:
    return sha1(encode(url.strip(), "utf-8")).hexdigest()


def get_url_file(url: str) -> Path:
    return Path(CACHE_DIRECTORY, f"{get_url_hash(url)}.request")


def has_cache(url: str) -> bool:
    cache_exists = get_url_file(url).exists()
    if not cache_exists:
        return False
    
    # Check if the URL hash exists in the database
    url_hash = get_url_hash(url)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM url_cache WHERE url_hash = ?", (url_hash,))
        return cursor.fetchone() is not None


def get_cache(url: str) -> requests.Response:
    with get_url_file(url).open("rb") as cache_file:
        return pickle.load(cache_file)


def write_cache(url: str, resp: requests.Response):
    url_hash = get_url_hash(url)
    current_time = datetime.now().isoformat()
    
    # Write the cache file
    with get_url_file(url).open("wb") as url_file:
        pickle.dump(resp, url_file)
    
    # Update the database
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO url_cache (url_hash, last_updated) VALUES (?, ?)",
            (url_hash, current_time)
        )
        conn.commit()
