from __future__ import annotations

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
    def __init__(
        self, 
        directory: Optional[str], 
        expires_after: timedelta = timedelta(days=float(os.getenv("EASY_REQUESTS_CACHE_EXPIRES", 1)))
    ):
        logger.info("initializing cache at %s, values expire after %s", directory, expires_after)
        
        self.expires_after = expires_after
        self._directory: Optional[Path] = None if directory is None or directory.strip() == "" else Path(directory)

        # initialize database if exist
        if self.is_enabled:
            self.directory.mkdir(exist_ok=True)
            with sqlite3.connect(self.database_file) as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS url_cache (
                    url_hash TEXT PRIMARY KEY,
                    expires_at TIMESTAMP
                )
                """)
                conn.commit()

    key_cache_enabled = "cache_enabled"
    key_cache_directory = "cache_directory"
    key_cache_expires_after = "cache_expires_after"
    def fork(self, **kwargs) -> Cache:
        directory = kwargs.get(self.key_cache_directory)
        if directory is None:
            directory = self._directory
        
        if kwargs.get(self.key_cache_enabled) is not None:
            if not kwargs[self.key_cache_enabled]:
                directory = None
            elif directory is None:
                raise ValueError("can't enable cache because no cache directory is defined")

        expires_after = kwargs.get(self.key_cache_expires_after)
        if expires_after is None:
            expires_after = self.expires_after

        # if didn't change can just return current cache
        if directory == self._directory and expires_after == self.expires_after:
            return self

        logger.debug("forking cache %s %s", directory, expires_after)
        return Cache(
            directory=None if directory is None else str(directory),
            expires_after=expires_after,
        )

    @property
    def is_enabled(self) -> bool:
        return self._directory is not None

    @property
    def directory(self) -> Path:
        assert self._directory is not None, "directory needs to be set"
        return self._directory

    @property
    def database_file(self) -> Path:
        return self.directory / "cache_metadata.db"

    @staticmethod
    def get_hash(*args: str) -> str:
        return sha1(encode("".join(elem.strip() for elem in args), "utf-8")).hexdigest()

    def get_url_file(self, url_hash: str) -> Path:
        return self.directory / f"{url_hash}.request"

    def has_cache(self, url_hash: str) -> bool:
        if not self.is_enabled:
            return False

        cache_file = self.get_url_file(url_hash)
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

    def get_cache(self, url_hash: str) -> requests.Response:
        logger.info("%s - returning cache", url_hash)
        with self.get_url_file(url_hash).open("rb") as cache_file:
            return pickle.load(cache_file)

    def write_cache(self, url_hash: str, response: requests.Response):
        expires_at = datetime.now() + self.expires_after
        
        # Write the cache file
        with self.get_url_file(url_hash).open("wb") as url_file:
            pickle.dump(response, url_file)
        
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



ROOT_CACHE: Cache = Cache(
    directory=os.getenv("EASY_REQUESTS_CACHE_DIR"),
    expires_after=timedelta(
        days=float(os.getenv("EASY_REQUESTS_CACHE_EXPIRES", 1))
    ),
)

def init_cache(directory: str, expires_after: timedelta = timedelta(days=float(os.getenv("EASY_REQUESTS_CACHE_EXPIRES", 1)))):
    """Configure the default cache storage location and expiration time.

    Args:
        directory: Cache storage directory path.
        expires_after: Cache expiration duration.
    
    Example:
        >>> init_cache('/tmp/cache', timedelta(hours=6))  # 6-hour expiration
        >>> init_cache('/tmp/cache')  # Uses default expiration (1 day)
    """
    global ROOT_CACHE
    cache_directory = directory
    cache_expires_after = expires_after
    ROOT_CACHE = ROOT_CACHE.fork(**locals())

