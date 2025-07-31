from typing import Optional, Tuple, Union
from codecs import encode
from hashlib import sha1
from pathlib import Path
import requests
import pickle
import sqlite3
from datetime import datetime, timedelta

from . import __name__

CACHE_DIRECTORY = Path(f"/tmp/{__name__}")
DB_FILE = Path(CACHE_DIRECTORY, "cache_metadata.db")


def _init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS url_cache (
            url_hash TEXT PRIMARY KEY,
            expires_at TIMESTAMP
        )
        """)
        conn.commit()


def set_cache_directory(cache_directory: Optional[Union[str, Path]] = None):
    global CACHE_DIRECTORY, DB_FILE

    if cache_directory is not None:
        CACHE_DIRECTORY = cache_directory
        DB_FILE = Path(CACHE_DIRECTORY, "cache_metadata.db")
    
    print(f"initializing cache at {CACHE_DIRECTORY} and db as {DB_FILE}")
    Path(CACHE_DIRECTORY).mkdir(exist_ok=True, parents=True)
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



def clean_cache() -> Tuple[int, int]:
    """
    Clean up expired cache entries.
    Returns tuple of (files_deleted, db_entries_deleted)
    """
    now = datetime.now()
    files_deleted = 0
    db_entries_deleted = 0
    
    with sqlite3.connect(DB_FILE) as conn:
        # Get all expired entries
        cursor = conn.cursor()
        cursor.execute(
            "SELECT url_hash FROM url_cache WHERE expires_at < ?",
            (now.isoformat(),)
        )
        expired_hashes = [row[0] for row in cursor.fetchall()]
        
        # Delete the files and count deletions
        for url_hash in expired_hashes:
            cache_file = Path(CACHE_DIRECTORY, f"{url_hash}.request")
            try:
                if cache_file.exists():
                    cache_file.unlink()
                    files_deleted += 1
            except OSError:
                continue
        
        # Delete database records and count deletions
        cursor.execute(
            "DELETE FROM url_cache WHERE expires_at < ?",
            (now.isoformat(),)
        )
        db_entries_deleted = cursor.rowcount
        conn.commit()
    
    return (files_deleted, db_entries_deleted)

def clear_cache() -> Tuple[int, int]:
    """
    Clear ALL cache entries regardless of expiration.
    Returns tuple of (files_deleted, db_entries_deleted)
    """
    files_deleted = 0
    db_entries_deleted = 0
    
    # Delete all cache files
    for cache_file in Path(CACHE_DIRECTORY).glob("*.request"):
        try:
            cache_file.unlink()
            files_deleted += 1
        except OSError:
            continue
    
    # Delete all database entries
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM url_cache")
        db_entries_deleted = cursor.rowcount
        conn.commit()
    
    return (files_deleted, db_entries_deleted)

def get_cache_stats() -> Tuple[int, int]:
    """
    Get cache statistics.
    Returns tuple of (total_files, total_db_entries)
    """
    # Count cache files
    total_files = len(list(Path(CACHE_DIRECTORY).glob("*.request")))
    
    # Count database entries
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM url_cache")
        total_db_entries = cursor.fetchone()[0]
    
    return (total_files, total_db_entries)
