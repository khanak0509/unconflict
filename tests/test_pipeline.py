import pytest

from unconflict import conflict
from unconflict.config import Config
from unconflict.llm import Resolution
from unconflict.pipeline import resolve_sides, resolve_text
from unconflict.structured import git_merge

from conftest import FakeLLM, load_case, make_resolver, needs_mergiraf

LANGS = ["python", "javascript", "typescript", "java"]

GOOD = {
    "python": '    return "hello " + name\n',
    "javascript": "  retries: 7,\n",
    "typescript": "  return u.name.trim().toUpperCase();\n",
    "java": "        return Math.round(cents * 1.20f);\n",
}
BROKEN = {
    "python": '    return "hello " + (name\n',
    "javascript": "  retries: (7,\n",
    "typescript": "  return u.name.trim().toUpperCase(;\n",
    "java": "        return Math.round(cents * 1.20f;\n",
}


@needs_mergiraf
@pytest.mark.parametrize("lang", LANGS)
def test_structured_clean_needs_no_llm(lang):
    base, ours, theirs, path = load_case(lang, "structured_clean")
    assert not git_merge(base, ours, theirs).clean
    fake = FakeLLM()
    res = resolve_sides(base, ours, theirs, path, Config(), make_resolver(fake))
    assert res.resolved and res.stage1 == "mergiraf"
    assert res.git_hunks >= 1 and res.stage1_remaining == 0
    assert fake.calls == [] and res.cost_usd == 0
    assert not conflict.has_conflicts(res.text)


@needs_mergiraf
@pytest.mark.parametrize("lang", ["python", "javascript"])
def test_structured_subexpression_merge(lang):
    base, ours, theirs, path = load_case(lang, "structured_subexpr")
    res = resolve_sides(base, ours, theirs, path, Config(), make_resolver(FakeLLM()))
    assert res.resolved and res.stage1 == "mergiraf"


@needs_mergiraf
@pytest.mark.parametrize("lang", LANGS)
def test_llm_needed(lang):
    base, ours, theirs, path = load_case(lang, "llm_needed")
    fake = FakeLLM(GOOD[lang])
    res = resolve_sides(base, ours, theirs, path, Config(), make_resolver(fake))
    assert res.resolved, res.summary()
    assert [h.stage for h in res.hunks] == ["llm"]
    assert GOOD[lang] in res.text and res.gate_rejections == 0
    user = fake.calls[0][1][1]
    assert "--- OURS ---" in user and "--- BASE ---" in user and "--- THEIRS ---" in user


@needs_mergiraf
@pytest.mark.parametrize("lang", LANGS)
def test_gate_rejects_then_retry_succeeds(lang):
    base, ours, theirs, path = load_case(lang, "llm_needed")
    fake = FakeLLM(BROKEN[lang], GOOD[lang])
    res = resolve_sides(base, ours, theirs, path, Config(), make_resolver(fake))
    assert res.resolved, res.summary()
    assert [h.stage for h in res.hunks] == ["llm_retry"]
    assert res.gate_rejections == 1 and len(fake.calls) == 2
    retry_msg = fake.calls[1][-1][1]
    assert "failed a check" in retry_msg and "parse" in retry_msg


@needs_mergiraf
@pytest.mark.parametrize("lang", LANGS)
def test_abstains_when_retry_also_fails(lang):
    base, ours, theirs, path = load_case(lang, "llm_needed")
    fake = FakeLLM(BROKEN[lang], BROKEN[lang])
    res = resolve_sides(base, ours, theirs, path, Config(), make_resolver(fake))
    assert not res.resolved
    assert res.hunks[0].stage == "abstain" and res.hunks[0].reason.startswith("gate:")
    assert res.gate_rejections == 2
    assert conflict.has_conflicts(res.text)
    assert BROKEN[lang] not in res.text


@needs_mergiraf
def test_duplicate_declaration_caught():
    base, ours, theirs, path = load_case("java", "llm_needed")
    dup = "        return cents * 120 / 100;\n    }\n\n    public static int withTax(int cents) {\n        return 0;\n"
    fake = FakeLLM(dup, dup)
    res = resolve_sides(base, ours, theirs, path, Config(), make_resolver(fake))
    assert not res.resolved and "duplicate" in res.hunks[0].reason


@needs_mergiraf
def test_model_declines_means_abstain():
    base, ours, theirs, path = load_case("python", "llm_needed")
    fake = FakeLLM(Resolution(code="", can_resolve=False, note="contradictory greetings"))
    res = resolve_sides(base, ours, theirs, path, Config(), make_resolver(fake))
    assert not res.resolved and "declined" in res.hunks[0].reason
    assert res.gate_rejections == 0


@needs_mergiraf
def test_unparseable_model_output_means_abstain():
    base, ours, theirs, path = load_case("python", "llm_needed")
    res = resolve_sides(base, ours, theirs, path, Config(), make_resolver(FakeLLM(None)))
    assert not res.resolved and res.hunks[0].stage == "abstain"


@needs_mergiraf
def test_budget_cap_means_abstain_not_crash():
    base, ours, theirs, path = load_case("python", "llm_needed")
    fake = FakeLLM()
    res = resolve_sides(base, ours, theirs, path, Config(), make_resolver(fake, cap=0.0))
    assert not res.resolved and "cap" in res.hunks[0].reason and fake.calls == []


def test_without_mergiraf_llm_handles_git_hunks(monkeypatch):
    monkeypatch.setenv("UNCONFLICT_MERGIRAF", "/nonexistent/mergiraf")
    base, ours, theirs, path = load_case("python", "structured_clean")
    fake = FakeLLM("import sys\nimport json\n")
    res = resolve_sides(base, ours, theirs, path, Config(), make_resolver(fake))
    assert "not installed" in res.stage1
    assert res.resolved and len(fake.calls) == 1


def test_llm_only_mode_skips_gate():
    base, ours, theirs, path = load_case("python", "llm_needed")
    cfg = Config(use_structured=False, use_gate=False)
    res = resolve_sides(base, ours, theirs, path, cfg, make_resolver(FakeLLM(BROKEN["python"]), cfg))
    assert res.resolved and BROKEN["python"] in res.text


def test_two_way_text_skips_structured_stage():
    text = 'def greet(name):\n<<<<<<< HEAD\n    return "hello " + name\n=======\n    return "hey " + name\n>>>>>>> b\n'
    res = resolve_text(text, "x.py", Config(), make_resolver(FakeLLM('    return "hey " + name\n')))
    assert res.resolved and "no base" in res.stage1


def test_no_llm_leaves_conflicts():
    base, ours, theirs, path = load_case("java", "llm_needed")
    res = resolve_sides(base, ours, theirs, path, Config(use_llm=False), None)
    assert not res.resolved and res.hunks[0].reason == "LLM stage disabled"


def test_long_lines_are_capped_and_huge_hunks_abstained():
    long = "x = '" + "a" * 9000 + "'\n"
    base = long + "y = 0\n" + long
    ours, theirs = base.replace("y = 0", "y = 1"), base.replace("y = 0", "y = 2")
    fake = FakeLLM("y = 2\n")
    res = resolve_sides(base, ours, theirs, "a.py", Config(use_structured=False), make_resolver(fake))
    assert res.resolved and len(fake.calls[0][1][1]) < 2000
    big = "z = '" + "b" * 13000 + "'\n"
    res = resolve_sides("q\n", big, "r\n", "a.py", Config(use_structured=False), make_resolver(FakeLLM()))
    assert not res.resolved and "too large" in res.hunks[0].reason
