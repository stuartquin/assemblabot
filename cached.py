import requests
import logging
from datetime import datetime, timedelta


class Cache:
    cache = {}
    expires = {}

    def get(self, key):
        if key in self.expires and self.expires[key] < datetime.now():
            del self.expires[key]
            del self.cache[key]

        return self.cache.get(key)

    def set(self, key, value, timeout=60):
        self.expires[key] = datetime.now() + timedelta(seconds=timeout)
        self.cache[key] = value


cache = Cache()


def fetch_cached(url, headers, timeout=60):
    cached = cache.get(url)
    if cached:
        return cached

    response = requests.get(url, headers=headers)
    logging.info("Cache Miss: {}".format(url))

    if response.ok:
        data = response.json()
        cache.set(url, data, timeout)
        return data
    else:
        response.raise_for_status()
