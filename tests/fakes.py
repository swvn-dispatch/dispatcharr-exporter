"""Reusable dependency-free fakes for collector regression tests."""

from fnmatch import fnmatch


class FakeRedis:
    """Small Redis subset with selectable byte or decoded-string responses."""

    def __init__(self, values=None, hashes=None, sets=None, decode_responses=False):
        self.values = values or {}
        self.hashes = hashes or {}
        self.sets = sets or {}
        self.decode_responses = decode_responses

    def _value(self, value):
        if self.decode_responses or not isinstance(value, str):
            return value
        return value.encode()

    def get(self, key):
        return self._value(self.values.get(self._key(key)))

    def hget(self, key, field):
        return self.hgetall(key).get(self._value(self._key(field)))

    def hgetall(self, key):
        return {
            self._value(name): self._value(value)
            for name, value in self.hashes.get(self._key(key), {}).items()
        }

    def scan_iter(self, match="*"):
        for key in self._keys():
            if fnmatch(key, match):
                yield self._value(key)

    def scan(self, cursor, match="*", count=None):
        return 0, list(self.scan_iter(match))

    def smembers(self, key):
        return {self._value(value) for value in self.sets.get(self._key(key), set())}

    def scard(self, key):
        return len(self.sets.get(self._key(key), set()))

    def _keys(self):
        return set(self.values) | set(self.hashes) | set(self.sets)

    @staticmethod
    def _key(key):
        return key.decode() if isinstance(key, bytes) else key
