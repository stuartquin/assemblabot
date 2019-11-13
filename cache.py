from datetime import datetime, timedelta


class Cache():
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
