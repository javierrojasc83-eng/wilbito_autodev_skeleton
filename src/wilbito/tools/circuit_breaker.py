import time
from typing import Callable, Any

class CircuitBreaker:
    """Circuit-breaker básico: abre tras N fallas y espera cooldown."""
    def __init__(self, fail_max: int = 3, reset_timeout: float = 5.0):
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self.fail_count = 0
        self.open_until = 0.0

    def call(self, fn: Callable[..., Any], *args, **kwargs):
        now = time.time()
        if now < self.open_until:
            raise RuntimeError("CircuitBreaker: abierto (cooldown).")
        try:
            res = fn(*args, **kwargs)
            self.fail_count = 0
            return res
        except Exception as e:
            self.fail_count += 1
            if self.fail_count >= self.fail_max:
                self.open_until = now + self.reset_timeout
            raise
