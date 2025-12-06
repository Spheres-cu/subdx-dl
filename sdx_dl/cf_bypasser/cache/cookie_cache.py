import json
import os
import threading

from sdx_dl.cf_bypasser.utils.misc import logger
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Any


@dataclass
class CachedCookies:
    """Represents cached Cloudflare clearance data."""
    hostname: str
    cookies: dict[str, str]
    user_agent: str
    timestamp: datetime
    expires_at: datetime

    def is_expired(self) -> bool:
        """Check if the cached cookies are expired."""
        return datetime.now() >= self.expires_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'hostname': self.hostname,
            'cookies': self.cookies,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat(),
            'expires_at': self.expires_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'CachedCookies':
        """Create from dictionary for deserialization."""
        return cls(
            hostname=data['hostname'],
            cookies=data['cookies'],
            user_agent=data['user_agent'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            expires_at=datetime.fromisoformat(data['expires_at'])
        )


class CookieCache:
    """Thread-safe cache for Cloudflare clearance cookies."""

    def __init__(self, cache_file: str = "cf_cookie_cache.json"):
        self.cache_file = cache_file
        self.cache: dict[str, CachedCookies] = {}
        self.lock = threading.RLock()
        self._load_cache()

    def _load_cache(self):
        """Load cache from file."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    for hostname, cached_data in data.items():
                        try:
                            self.cache[hostname] = CachedCookies.from_dict(cached_data)
                        except Exception as e:
                            logger.warning(f"Failed to load cached data for {hostname}: {e}")
        except Exception as e:
            logger.warning(f"Failed to load cache file: {e}")

    def _save_cache(self):
        """Save cache to file."""
        try:
            with open(self.cache_file, 'w') as f:
                data = {hostname: cached.to_dict() for hostname, cached in self.cache.items()}
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache file: {e}")

    def get(self, hostname: str) -> CachedCookies | None:
        """Get cached cookies for hostname."""
        with self.lock:
            cached = self.cache.get(hostname)
            if cached and not cached.is_expired():
                logger.info(f"Using cached cookies for {hostname}")
                return cached
            elif cached and cached.is_expired():
                logger.info(f"Cached cookies for {hostname} expired, removing")
                del self.cache[hostname]
                self._save_cache()
            return None

    def set(self, hostname: str, cookies: dict[str, str], user_agent: str, ttl_hours: int = 2):
        """Cache cookies for hostname with TTL."""
        with self.lock:
            expires_at = datetime.now() + timedelta(hours=ttl_hours)
            cached = CachedCookies(
                hostname=hostname,
                cookies=cookies,
                user_agent=user_agent,
                timestamp=datetime.now(),
                expires_at=expires_at
            )
            self.cache[hostname] = cached
            self._save_cache()
            logger.info(f"Cached cookies for {hostname}, expires at {expires_at}")

    def clear_expired(self):
        """Remove all expired entries."""
        with self.lock:
            expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
            for key in expired_keys:
                del self.cache[key]
            if expired_keys:
                self._save_cache()
                logger.info(f"Cleared {len(expired_keys)} expired cache entries")

    def invalidate(self, hostname: str):
        """Invalidate cached cookies for a specific hostname."""
        with self.lock:
            if hostname in self.cache:
                del self.cache[hostname]
                self._save_cache()
                logger.info(f"Invalidated cache for {hostname}")

    def clear_all(self):
        """Clear all cached entries."""
        with self.lock:
            self.cache.clear()
            self._save_cache()
            logger.info("Cleared all cache entries")
