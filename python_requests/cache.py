from typing import Optional
from codecs import encode
from hashlib import sha1
from pathlib import Path
import requests
import pickle
import sqlite3
from datetime import datetime, timedelta

from . import CACHE_DIRECTORY


# SQLite database file path
DB_FILE = Path(CACHE_DIRECTORY, "cache_metadata.db")

# Initialize the database
def _init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS url_cache (
            url_hash TEXT PRIMARY KEY,
            expires_at TIMESTAMP
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
    url_hash = get_url_hash(url)
    cache_file = get_url_file(url)
    
    if not cache_file.exists():
        return False
    
    # Check if the cache has expired
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT expires_at FROM url_cache WHERE url_hash = ?",
            (url_hash,)
        )
        result = cursor.fetchone()
        
        if result is None:
            return False  # No expiration record exists
        
        expires_at = datetime.fromisoformat(result[0])
        if datetime.now() > expires_at:
            # Cache expired, clean it up
            cache_file.unlink(missing_ok=True)
            cursor.execute(
                "DELETE FROM url_cache WHERE url_hash = ?",
                (url_hash,)
            )
            conn.commit()
            return False
    
    return True



def get_cache(url: str) -> requests.Response:
    with get_url_file(url).open("rb") as cache_file:
        return pickle.load(cache_file)


def write_cache(
    url: str,
    resp: requests.Response,
    expires_after: Optional[timedelta] = None
):
    url_hash = get_url_hash(url)
    
    # Default expiration: 24 hours from now
    if expires_after is None:
        expires_after = timedelta(hours=1)
    
    expires_at = datetime.now() + expires_after
    
    # Write the cache file
    with get_url_file(url).open("wb") as url_file:
        pickle.dump(resp, url_file)
    
    # Update the database
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO url_cache (url_hash, expires_at) VALUES (?, ?)",
            (url_hash, expires_at.isoformat())
        )
        conn.commit()
