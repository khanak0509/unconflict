import json
import threading

import pytest

from unconflict.budget import Budget, BudgetExceeded, Usage, cost_usd
from unconflict.config import Config
from unconflict.llm import HunkRequest

from conftest import FakeLLM, make_resolver

REQ = HunkRequest("python", "a.py", "x = 1\n", "x = 2\n", "x = 0\n", "", "")


def test_cost_formula():
    u = Usage(input_tokens=1_000_000, cached_input_tokens=200_000, output_tokens=100_000)
    assert cost_usd("gpt-6-luna", u) == pytest.approx(0.08 + 0.002 + 0.05)


def test_unknown_model_refused():
    with pytest.raises(BudgetExceeded):
        Budget(2.5).reserve("some-model-without-a-price", "hi", 100)


def test_ledger_persists_across_instances(isolated_home):
    b = Budget(2.5)
    b.record("gpt-6-luna", Usage(input_tokens=1000, output_tokens=1000))
    again = Budget(2.5)
    assert again.spent() == pytest.approx((1000 * 0.10 + 1000 * 0.50) / 1e6)
    assert json.loads((isolated_home / "spend.json").read_text())["calls"] == 1
    assert len((isolated_home / "spend_log.jsonl").read_text().splitlines()) == 1


def test_refuses_once_cap_would_be_passed():
    b = Budget(0.001)
    b.record("gpt-6-luna", Usage(output_tokens=1900))
    with pytest.raises(BudgetExceeded):
        b.reserve("gpt-6-luna", "x" * 300, max_output_tokens=256)


def test_parallel_reservations_cannot_overshoot():
    b = Budget(0.01)
    ok, refused = [], []

    def go():
        try:
            ok.append(b.reserve("gpt-6-luna", "x" * 3000, 4096))
        except BudgetExceeded:
            refused.append(1)

    ts = [threading.Thread(target=go) for _ in range(20)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert sum(ok) <= 0.01 and refused


def test_resolver_records_spend_and_cache_makes_reruns_free():
    fake = FakeLLM("x = 3\n", input_tokens=500, output_tokens=50)
    r = make_resolver(fake)
    first = r.resolve(REQ)
    assert first.resolution.code == "x = 3\n" and not first.cached
    assert first.cost_usd == pytest.approx((500 * 0.10 + 50 * 0.50) / 1e6)
    second = make_resolver(FakeLLM()).resolve(REQ)
    assert second.cached and second.cost_usd == 0 and second.resolution.code == "x = 3\n"
    assert Budget(2.5).summary()["calls"] == 1


def test_budget_exceeded_propagates_without_calling_model():
    fake = FakeLLM()
    with pytest.raises(BudgetExceeded):
        make_resolver(fake, cap=0.0).resolve(REQ)
    assert fake.calls == []


def test_prompt_contains_three_sides_and_context():
    fake = FakeLLM("x = 3\n")
    make_resolver(fake, Config()).resolve(
        HunkRequest("python", "a.py", "OURS_SIDE\n", "THEIRS_SIDE\n", "BASE_SIDE\n", "BEFORE\n", "AFTER\n")
    )
    (msgs,) = fake.calls
    user = msgs[1][1]
    for s in ("OURS_SIDE", "THEIRS_SIDE", "BASE_SIDE", "BEFORE", "AFTER", "Language: python"):
        assert s in user
