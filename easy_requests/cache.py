import logging
from typing import Optional, Tuple, Union
from codecs import encode
from hashlib import sha1
from pathlib import Path
import requests
import pickle
import sqlite3
from datetime import datetime, timedelta
import os
from datetime import timedelta


logger = logging.getLogger("easy_requests")


class Cache:
    def __init__(self, directory: str, expires_after: timedelta = timedelta(days=float(os.getenv("EASY_REQUESTS_CACHE_EXPIRES", 1)))):
        logger.info("initializing cache at %s", directory)
        
        self.directory = Path(directory)
        self.database_file = self.directory / "cache_metadata.db"

        self.expires_after = expires_after

        # initialization code
        self.directory.mkdir(exist_ok=True)
        with sqlite3.connect(self.database_file) as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS url_cache (
                url_hash TEXT PRIMARY KEY,
                expires_at TIMESTAMP
            )
            """)
            conn.commit()

    @staticmethod
    def get_url_hash(url: str) -> str:
        return sha1(encode(url.strip(), "utf-8")).hexdigest()


    def get_url_file(self, url: str) -> Path:
        return Path(self.directory, f"{self.get_url_hash(url)}.request")


    def has_cache(self, url: str) -> bool:
        url_hash = self.get_url_hash(url)
        cache_file = self.get_url_file(url)
        
        if not cache_file.exists():
            return False
        
        # Check if the cache has expired
        with sqlite3.connect(self.database_file) as conn:
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


    def get_cache(self, url: str) -> requests.Response:
        with self.get_url_file(url).open("rb") as cache_file:
            return pickle.load(cache_file)


    def write_cache(
        self,
        url: str,
        resp: requests.Response,
    ):
        url_hash = self.get_url_hash(url)
        
        expires_at = datetime.now() + self.expires_after
        
        # Write the cache file
        with self.get_url_file(url).open("wb") as url_file:
            pickle.dump(resp, url_file)
        
        # Update the database
        with sqlite3.connect(self.database_file) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO url_cache (url_hash, expires_at) VALUES (?, ?)",
                (url_hash, expires_at.isoformat())
            )
            conn.commit()

    def clean_cache(self) -> Tuple[int, int]:
        """
        Clean up expired cache entries.
        Returns tuple of (files_deleted, db_entries_deleted)
        """
        now = datetime.now()
        files_deleted = 0
        db_entries_deleted = 0

        with sqlite3.connect(self.database_file) as conn:
            # Get all expired entries
            cursor = conn.cursor()
            cursor.execute(
                "SELECT url_hash FROM url_cache WHERE expires_at < ?",
                (now.isoformat(),)
            )
            expired_hashes = [row[0] for row in cursor.fetchall()]
            
            # Delete the files and count deletions
            for url_hash in expired_hashes:
                cache_file = Path(self.directory, f"{url_hash}.request")
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

    def clear_cache(self) -> Tuple[int, int]:
        """
        Clear ALL cache entries regardless of expiration.
        Returns tuple of (files_deleted, db_entries_deleted)
        """
        files_deleted = 0
        db_entries_deleted = 0

        # Delete all cache files
        for cache_file in Path(self.directory).glob("*.request"):
            try:
                cache_file.unlink()
                files_deleted += 1
            except OSError:
                continue
        
        # Delete all database entries
        with sqlite3.connect(self.database_file) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM url_cache")
            db_entries_deleted = cursor.rowcount
            conn.commit()
        
        return (files_deleted, db_entries_deleted)

    def get_cache_stats(self) -> Tuple[int, int]:
        """
        Get cache statistics.
        Returns tuple of (total_files, total_db_entries)
        """

        # Count cache files
        total_files = len(list(self.directory.glob("*.request")))
        
        # Count database entries
        with sqlite3.connect(self.database_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM url_cache")
            total_db_entries = cursor.fetchone()[0]
        
        return (total_files, total_db_entries)



DEFAULT_CACHE: Optional[Cache] = None
if os.getenv("EASY_REQUESTS_CACHE_DIR"):
    logger.info("environment variable EASY_REQUESTS_CACHE_DIR was set, initializing default cache dir")
    DEFAULT_CACHE = Cache(directory=os.getenv("EASY_REQUESTS_CACHE_DIR", ""))


def init_cache(directory: str, expires_after: timedelta = timedelta(days=float(os.getenv("EASY_REQUESTS_CACHE_EXPIRES", 1)))):
    global DEFAULT_CACHE
    DEFAULT_CACHE = Cache(
        directory=directory,
        expires_after=expires_after
    )

