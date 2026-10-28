from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from .config import home


def cache_key(model: str, params: dict, messages: list[tuple[str, str]], schema: dict) -> str:
    blob = json.dumps(
        {"model": model, "params": params, "messages": messages, "schema": schema},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class ResponseCache:
    def __init__(self, root: Path | None = None, enabled: bool = True):
        self.root = root or (home() / "cache")
        self.enabled = enabled
        self.hits = 0
        self.misses = 0

    def _path(self, model: str, key: str) -> Path:
        return self.root / model / key[:2] / f"{key}.json"

    def get(self, model: str, key: str) -> dict | None:
        if not self.enabled:
            return None
        p = self._path(model, key)
        if not p.exists():
            self.misses += 1
            return None
        self.hits += 1
        return json.loads(p.read_text(encoding="utf-8"))

    def put(self, model: str, key: str, value: dict) -> None:
        if not self.enabled:
            return
        p = self._path(model, key)
        p.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=p.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(value, fh, ensure_ascii=False)
        os.replace(tmp, p)
