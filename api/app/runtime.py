import time
from collections import OrderedDict, deque
from threading import Lock
from typing import Protocol


class RateLimiter(Protocol):
    def allow(self, key: str = "global") -> bool: ...


class MemoryRateLimiter:
    def __init__(self, limit=30, window=60, clock=time.monotonic, max_keys=1024):
        self.limit = limit
        self.window = window
        self.clock = clock
        self.max_keys = max_keys
        self.events = OrderedDict()
        self.lock = Lock()

    def allow(self, key="global"):
        with self.lock:
            now = self.clock()
            for old_key in list(self.events):
                if not self.events[old_key] or self.events[old_key][-1] <= now - self.window:
                    del self.events[old_key]
            if key not in self.events:
                if len(self.events) >= self.max_keys:
                    return False
                self.events[key] = deque()
            events = self.events[key]
            while events and events[0] <= now - self.window:
                events.popleft()
            if len(events) >= self.limit:
                return False
            events.append(now)
            return True


class TTLCache:
    def __init__(self, capacity=256, ttl=30, clock=time.monotonic):
        self.capacity = capacity
        self.ttl = ttl
        self.clock = clock
        self.values = OrderedDict()
        self.lock = Lock()

    def get(self, key):
        with self.lock:
            entry = self.values.get(key)
            if entry is None:
                return None
            if entry[0] <= self.clock():
                del self.values[key]
                return None
            self.values.move_to_end(key)
            return entry[1]

    def put(self, key, value):
        with self.lock:
            self.values[key] = (self.clock() + self.ttl, value)
            self.values.move_to_end(key)
            while len(self.values) > self.capacity:
                self.values.popitem(last=False)

    def clear(self):
        with self.lock:
            self.values.clear()


class Metrics:
    def __init__(self):
        self.lock = Lock()
        self.requests = 0
        self.errors = 0
        self.elapsed = 0.0
        self.started = time.monotonic()

    def observe(self, status, elapsed):
        with self.lock:
            self.requests += 1
            self.errors += int(status >= 500)
            self.elapsed += elapsed

    def snapshot(self):
        with self.lock:
            return {"scope": "current_process", "requests": self.requests,
                    "server_errors": self.errors, "request_seconds_total": self.elapsed,
                    "uptime_seconds": time.monotonic() - self.started}
