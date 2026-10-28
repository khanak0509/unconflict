from __future__ import annotations

import fcntl
import json
import math
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .config import PRICES, home


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class Usage:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0


def price_for(model: str) -> tuple[float, float, float]:
    if model not in PRICES:
        raise BudgetExceeded(
            f"no price configured for model {model!r}; add it to unconflict.config.PRICES "
            "before making paid calls"
        )
    return PRICES[model]


def cost_usd(model: str, u: Usage) -> float:
    p_in, p_cached, p_out = price_for(model)
    uncached = max(u.input_tokens - u.cached_input_tokens, 0)
    return (uncached * p_in + u.cached_input_tokens * p_cached + u.output_tokens * p_out) / 1e6


def estimate_input_tokens(text: str) -> int:
    return math.ceil(len(text) / 3) + 50


class Budget:
    def __init__(self, cap_usd: float, ledger_path: Path | None = None):
        self.cap_usd = cap_usd
        self.path = ledger_path or (home() / "spend.json")
        self.log_path = self.path.with_name("spend_log.jsonl")
        self._reserved = 0.0
        self._lock = threading.Lock()
        self.run_spent = 0.0
        self.run_calls = 0

    @contextmanager
    def _locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock = self.path.with_suffix(".lock")
        with open(lock, "a") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)

    def _read(self) -> dict:
        if not self.path.exists():
            return {"total_usd": 0.0, "calls": 0, "input_tokens": 0, "cached_input_tokens": 0,
                    "output_tokens": 0, "reasoning_tokens": 0, "by_model": {}}
        return json.loads(self.path.read_text())

    def spent(self) -> float:
        with self._locked():
            return float(self._read()["total_usd"])

    def summary(self) -> dict:
        with self._locked():
            return self._read()

    def reserve(self, model: str, prompt_text: str, max_output_tokens: int) -> float:
        p_in, _, p_out = price_for(model)
        worst = (estimate_input_tokens(prompt_text) * p_in + max_output_tokens * p_out) / 1e6
        with self._lock:
            spent = self.spent()
            if spent + self._reserved + worst > self.cap_usd:
                raise BudgetExceeded(
                    f"refusing LLM call: spent ${spent:.4f} + pending ${self._reserved:.4f} + this call "
                    f"(worst case ${worst:.5f}) would pass the ${self.cap_usd:.2f} cap"
                )
            self._reserved += worst
        return worst

    def release(self, reservation: float) -> None:
        with self._lock:
            self._reserved = max(self._reserved - reservation, 0.0)

    def record(self, model: str, usage: Usage, reservation: float = 0.0, meta: dict | None = None) -> float:
        dollars = cost_usd(model, usage)
        with self._lock:
            with self._locked():
                led = self._read()
                led["total_usd"] = led["total_usd"] + dollars
                led["calls"] += 1
                for k in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens"):
                    led[k] = led.get(k, 0) + getattr(usage, k)
                m = led["by_model"].setdefault(model, {"usd": 0.0, "calls": 0})
                m["usd"] += dollars
                m["calls"] += 1
                tmp = self.path.with_suffix(".tmp")
                tmp.write_text(json.dumps(led, indent=2))
                tmp.replace(self.path)
                with open(self.log_path, "a") as fh:
                    fh.write(json.dumps({"ts": time.time(), "model": model, "usd": dollars,
                                         **usage.__dict__, **(meta or {})}) + "\n")
            self._reserved = max(self._reserved - reservation, 0.0)
            self.run_spent += dollars
            self.run_calls += 1
        return dollars

    def report(self) -> str:
        return (f"spend: this run ${self.run_spent:.5f} over {self.run_calls} paid call(s); "
                f"total ${self.spent():.4f} of ${self.cap_usd:.2f} cap")
