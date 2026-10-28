import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from unconflict.budget import Budget
from unconflict.cache import ResponseCache
from unconflict.config import Config
from unconflict.llm import LLMResolver, Resolution

FIXTURES = Path(__file__).parent / "fixtures"

needs_mergiraf = pytest.mark.skipif(shutil.which("mergiraf") is None, reason="mergiraf not installed")


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    monkeypatch.setenv("UNCONFLICT_HOME", str(tmp_path / "home"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("UNCONFLICT_BUDGET_USD", raising=False)
    monkeypatch.delenv("UNCONFLICT_MODEL", raising=False)
    monkeypatch.delenv("UNCONFLICT_MERGIRAF", raising=False)
    yield tmp_path / "home"


class FakeLLM:
    def __init__(self, *answers, input_tokens=400, output_tokens=60):
        self.answers = list(answers)
        self.calls: list[list] = []
        self.usage = {"input_tokens": input_tokens, "output_tokens": output_tokens,
                      "input_token_details": {"cache_read": 0}, "output_token_details": {"reasoning": 0}}

    def factory(self, cfg, max_tokens):
        outer = self

        class _Chat:
            def invoke(self, messages):
                outer.calls.append(messages)
                if not outer.answers:
                    raise AssertionError("unexpected extra LLM call")
                a = outer.answers.pop(0)
                if isinstance(a, str):
                    a = Resolution(code=a, can_resolve=True, note="")
                return {"raw": SimpleNamespace(usage_metadata=outer.usage), "parsed": a,
                        "parsing_error": None if a is not None else "bad json"}

        return _Chat()


def make_resolver(fake: FakeLLM, cfg: Config | None = None, cap: float = 2.5) -> LLMResolver:
    cfg = cfg or Config()
    return LLMResolver(cfg, Budget(cap), ResponseCache(), chat_factory=fake.factory)


def load_case(lang: str, case: str) -> tuple[str, str, str, str]:
    d = FIXTURES / lang / case
    ext = next(d.iterdir()).suffix
    read = lambda n: (d / f"{n}{ext}").read_text()
    return read("base"), read("ours"), read("theirs"), f"src/example{ext}"
