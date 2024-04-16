import os
import pickle
from pathlib import Path

class DomainCache:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_domain_cache_path(self, domain: str) -> Path:
        return self.cache_dir / f"{domain}.pkl"

    def set(self, domain: str, key: str, value):
        domain_cache_path = self._get_domain_cache_path(domain)
        domain_cache = self._load_domain_cache(domain_cache_path)
        domain_cache[key] = value
        with open(domain_cache_path, 'wb') as cache_file:
            pickle.dump(domain_cache, cache_file)

    def get(self, domain: str, key: str):
        domain_cache_path = self._get_domain_cache_path(domain)
        domain_cache = self._load_domain_cache(domain_cache_path)
        return domain_cache.get(key)

    def _load_domain_cache(self, domain_cache_path: Path) -> dict:
        if domain_cache_path.is_file():
            with open(domain_cache_path, 'rb') as cache_file:
                return pickle.load(cache_file)
        return {}

    def clear(self, domain: str):
        domain_cache_path = self._get_domain_cache_path(domain)
        if domain_cache_path.is_file():
            domain_cache_path.unlink()
# Example usage:
# cache = LocalCache()
# cache.set('test_key', 'test_value')
# print(cache.get('test_key'))  # Output: test_value
# cache.clear()
