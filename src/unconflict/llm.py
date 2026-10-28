from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable, Optional

from pydantic import BaseModel, Field

from .budget import Budget, BudgetExceeded, Usage
from .cache import ResponseCache, cache_key
from .config import Config

SYSTEM_PROMPT = (
    "You resolve one git merge conflict. You get OURS and THEIRS (and BASE, their common "
    "ancestor, when available) plus a little surrounding context. Return in `code` the exact "
    "lines that replace the conflict block only, not the context. Keep the intent of both "
    "sides when compatible; keep the original indentation; add no comments, explanations or "
    "conflict markers. If the sides contradict each other and the right merge is unclear, "
    "set can_resolve=false and say why in `note`."
)


class Resolution(BaseModel):
    code: str = Field(description="Lines replacing the conflict block (no markers, no context).")
    can_resolve: bool = Field(description="False if the conflict can't be resolved safely.")
    note: str = Field(description="Empty unless can_resolve is false: a short reason.")


@dataclass
class HunkRequest:
    language: str | None
    path: str | None
    ours: str
    theirs: str
    base: str | None
    before: str
    after: str


@dataclass
class LLMAnswer:
    resolution: Optional[Resolution]
    cost_usd: float = 0.0
    cached: bool = False
    usage: Usage = field(default_factory=Usage)
    error: str | None = None


def _block(title: str, text: str) -> str:
    return f"--- {title} ---\n{text if text.endswith(chr(10)) or not text else text + chr(10)}"


def build_user_prompt(req: HunkRequest) -> str:
    parts = [f"Language: {req.language or 'unknown'}" + (f"\nFile: {req.path}" if req.path else "")]
    if req.before:
        parts.append(_block("context before", req.before))
    parts.append(_block("OURS", req.ours))
    parts.append(_block("BASE", req.base) if req.base is not None else "--- BASE: not available ---\n")
    parts.append(_block("THEIRS", req.theirs))
    if req.after:
        parts.append(_block("context after", req.after))
    return "\n".join(parts)


def output_token_cap(req: HunkRequest) -> int:
    approx = (len(req.ours) + len(req.theirs) + len(req.base or "")) // 3 + 300
    return max(256, min(approx, 4096))


def _default_chat_factory(cfg: Config, max_tokens: int):
    return _chat(cfg.model, cfg.reasoning_effort, max_tokens, cfg.llm_timeout_s)


@lru_cache(maxsize=64)
def _chat(model: str, effort: str | None, max_tokens: int, timeout: float):
    from langchain_openai import ChatOpenAI

    kwargs = dict(model=model, max_tokens=max_tokens, max_retries=2, timeout=timeout)
    if effort is not None:
        kwargs["reasoning_effort"] = effort
    chat = ChatOpenAI(**kwargs)
    return chat.with_structured_output(Resolution, method="json_schema", strict=True, include_raw=True)


def _usage_from(raw) -> Usage:
    um = getattr(raw, "usage_metadata", None) or {}
    return Usage(
        input_tokens=int(um.get("input_tokens", 0) or 0),
        cached_input_tokens=int((um.get("input_token_details") or {}).get("cache_read", 0) or 0),
        output_tokens=int(um.get("output_tokens", 0) or 0),
        reasoning_tokens=int((um.get("output_token_details") or {}).get("reasoning", 0) or 0),
    )


class LLMResolver:
    def __init__(
        self,
        cfg: Config,
        budget: Budget,
        cache: ResponseCache,
        chat_factory: Callable[[Config, int], object] | None = None,
    ):
        self.cfg = cfg
        self.budget = budget
        self.cache = cache
        self.chat_factory = chat_factory or _default_chat_factory
        self.calls = 0

    def resolve(self, req: HunkRequest, feedback: tuple[str, str] | None = None) -> LLMAnswer:
        messages: list[tuple[str, str]] = [("system", SYSTEM_PROMPT), ("human", build_user_prompt(req))]
        if feedback is not None:
            prev, err = feedback
            messages.append(("ai", json.dumps({"code": prev, "can_resolve": True, "note": ""})))
            messages.append(("human", f"That resolution failed a check: {err}\nReturn a corrected resolution."))
        max_tokens = output_token_cap(req)
        params = {"reasoning_effort": self.cfg.reasoning_effort, "max_tokens": max_tokens}
        key = cache_key(self.cfg.model, params, messages, Resolution.model_json_schema())

        hit = self.cache.get(self.cfg.model, key)
        if hit is not None:
            res = Resolution(**hit["parsed"]) if hit.get("parsed") else None
            return LLMAnswer(res, 0.0, True, Usage(**hit.get("usage", {})), hit.get("error"))

        prompt_text = "\n".join(c for _, c in messages)
        reservation = self.budget.reserve(self.cfg.model, prompt_text, max_tokens)
        try:
            chat = self.chat_factory(self.cfg, max_tokens)
            out = chat.invoke(messages)
        except BudgetExceeded:
            self.budget.release(reservation)
            raise
        except Exception as e:
            self.budget.release(reservation)
            return LLMAnswer(None, 0.0, False, Usage(), f"{type(e).__name__}: {e}")
        self.calls += 1
        raw, parsed = out.get("raw"), out.get("parsed")
        usage = _usage_from(raw)
        cost = self.budget.record(self.cfg.model, usage, reservation, {"key": key[:16]})
        error = None
        if parsed is None:
            error = f"unparseable model output: {out.get('parsing_error')}"
        self.cache.put(self.cfg.model, key, {
            "parsed": parsed.model_dump() if parsed is not None else None,
            "usage": usage.__dict__,
            "error": error,
        })
        return LLMAnswer(parsed, cost, False, usage, error)
