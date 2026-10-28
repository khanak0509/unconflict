from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import subprocess
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "eval"))

import merge_bench
from metrics import has_conflict_markers, locate, region_text, score, ws_normalize
from unconflict import conflict
from unconflict.budget import Budget
from unconflict.cache import ResponseCache
from unconflict.config import BENCH_LANG, PRICES, Config
from unconflict.llm import SYSTEM_PROMPT, LLMResolver
from unconflict.pipeline import resolve_sides, resolve_text
from unconflict.structured import find_mergiraf, git_merge, mergiraf_merge

TRACK_SYSTEMS = {
    "A": ["git_default", "llm_only", "llm_gate"],
    "B": ["git_default", "mergiraf_only", "llm_only", "hybrid"],
}
MODEL_CUTOFF = "2026-05-18"


def load_dotenv() -> None:
    env = ROOT / ".env"
    if env.exists() and not os.environ.get("OPENAI_API_KEY"):
        for line in env.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def system_config(system: str, base: Config) -> Config:
    cfg = Config(**{**base.__dict__})
    if system in ("llm_only",):
        cfg.use_structured, cfg.use_gate = False, False
    elif system == "llm_gate":
        cfg.use_structured, cfg.use_gate = False, True
    elif system == "hybrid":
        cfg.use_structured, cfg.use_gate = True, True
    return cfg


def split_dangling(snippet: str) -> tuple[str, str] | None:
    try:
        conflict.parse(snippet)
        return snippet, ""
    except conflict.ConflictParseError as e:
        if "unterminated" not in str(e):
            return None
    lines = snippet.splitlines(keepends=True)
    last = max(i for i, x in enumerate(lines) if x.startswith("<<<<<<<"))
    head, tail = "".join(lines[:last]), "".join(lines[last:])
    try:
        conflict.parse(head)
    except conflict.ConflictParseError:
        return None
    return head, tail


def run_item_a(item: dict, system: str, base_cfg: Config, resolver) -> list[dict]:
    lang = item["language"]
    split = split_dangling(item["snippet"])
    rec = {"id": item["id"], "language": lang, "system": system}
    if split is None:
        return [{**rec, "excluded": "malformed conflict markers"}]
    head, tail = split
    if system == "git_default":
        out, abstained, stage, cost, nominal, rej = item["snippet"], True, "abstain", 0.0, 0.0, 0
    else:
        cfg = system_config(system, base_cfg)
        res = resolve_text(head, f"snippet{BENCH_LANG[lang][1]}", cfg, resolver)
        out, abstained = res.text + tail, not res.resolved
        stages = {h.stage for h in res.hunks}
        stage = "abstain" if "abstain" in stages else "llm_retry" if "llm_retry" in stages else "llm"
        cost, nominal, rej = res.cost_usd, res.nominal_cost_usd, res.gate_rejections
    s = score(out, item["answer"], lang, abstained)
    return [{**rec, **s, "stage": stage, "cost_usd": cost, "nominal_cost_usd": nominal, "gate_rejections": rej,
             "pred": out}]


MAX_FILE_HUNKS = 20


def load_mined(languages: list[str], per_language: int | None, seed: int) -> list[dict]:
    items = []
    for lang in languages:
        f = ROOT / "data" / "mined" / f"{lang}.jsonl"
        if not f.exists():
            print(f"no mined data: {f}")
            continue
        recs = [json.loads(x) for x in f.read_text().splitlines()]
        recs = [r for r in recs if r["git_hunks"] <= MAX_FILE_HUNKS]
        recs.sort(key=lambda r: r["id"])
        random.Random(f"{seed}:{lang}").shuffle(recs)
        if per_language is None:
            items += recs
            continue
        n = 0
        for r in recs:
            if n + len(r["hunks"]) <= per_language:
                items.append(r)
                n += len(r["hunks"])
            if n == per_language:
                break
    return items


def _conflict_starts(text: str) -> list[int]:
    starts, line = [], 0
    for s in conflict.parse(text):
        if isinstance(s, conflict.Hunk):
            starts.append(line)
            line += len(s.render())
        else:
            line += len(s.splitlines())
    return starts


def run_item_b(item: dict, system: str, base_cfg: Config, resolver) -> list[dict]:
    lang, b, o, t, path = item["language"], item["base"], item["ours"], item["theirs"], item["path"]
    cost = nominal = 0.0
    rej, res = 0, None
    if system == "git_default":
        out = git_merge(b, o, t).text
    elif system == "mergiraf_only":
        m = mergiraf_merge(b, o, t, path, timeout_s=base_cfg.mergiraf_timeout_s)
        out = m.text if m is not None else git_merge(b, o, t).text
    else:
        cfg = system_config(system, base_cfg)
        res = resolve_sides(b, o, t, path, cfg, resolver)
        out, cost, nominal, rej = res.text, res.cost_usd, res.nominal_cost_usd, res.gate_rejections
    file_has_conflicts = has_conflict_markers(out)
    file_exact = ws_normalize(out) == ws_normalize(item["merged"])
    rows = []
    s1 = res.stage1_text if res is not None else None
    s1_starts = _conflict_starts(s1) if s1 else []
    for j, h in enumerate(item["hunks"]):
        region = locate(out, h["before"], h["after"], h["at_start"], h["at_end"])
        pred = region_text(out, region) if region else None
        abstained = has_conflict_markers(pred) if pred is not None else file_has_conflicts
        sc = score(pred, h["gold"], lang, abstained)
        stage = _stage_of(system, res, s1, s1_starts, h, pred, abstained)
        rows.append({
            "id": f"{item['id']}#{j}", "file_id": item["id"], "language": lang, "system": system,
            "date": item["date"], "post_cutoff": item["date"][:10] > MODEL_CUTOFF, "mb_size": h["mb_size"],
            "conflict_lines": h["conflict_lines"], **sc, "stage": stage, "file_exact": file_exact,
            "cost_usd": cost if j == 0 else 0.0, "nominal_cost_usd": nominal if j == 0 else 0.0,
            "gate_rejections": rej if j == 0 else 0,
            "pred": pred,
        })
    return rows


def _stage_of(system, res, s1, s1_starts, h, pred, abstained) -> str:
    if system == "git_default":
        return "abstain"
    if system == "mergiraf_only":
        return "abstain" if abstained else "mergiraf"
    if res is None or s1 is None:
        return "unknown"
    r1 = locate(s1, h["before"], h["after"], h["at_start"], h["at_end"])
    if r1 is None:
        return "unknown"
    if not has_conflict_markers(region_text(s1, r1)):
        return "mergiraf" if res.stage1 == "mergiraf" else "unknown"
    owned = [k for k, start in enumerate(s1_starts) if r1[0] <= start < r1[1]]
    stages = {res.hunks[k].stage for k in owned if k < len(res.hunks)}
    if not stages:
        return "unknown"
    return "abstain" if "abstain" in stages else "llm_retry" if "llm_retry" in stages else "llm"


def pct(a, b):
    return f"{100 * a / b:.1f}%" if b else "–"


def summarize(rows: list[dict], key=lambda r: True) -> dict:
    rs = [r for r in rows if "excluded" not in r and key(r)]
    n = len(rs)
    att = [r for r in rs if not r["abstained"]]
    stages = defaultdict(int)
    for r in rs:
        stages[r["stage"]] += 1
    nominal = sum(r["nominal_cost_usd"] for r in rs)
    return {
        "n": n,
        "exact": sum(r["exact"] for r in rs), "semantic": sum(r["semantic"] for r in rs), "ws": sum(r["ws"] for r in rs),
        "abstained": len(rs) - len(att),
        "attempted": len(att),
        "attempted_exact": sum(r["exact"] for r in att), "attempted_semantic": sum(r["semantic"] for r in att),
        "unlocatable": sum(r["outcome"] == "unlocatable" for r in rs),
        "stages": dict(stages),
        "gate_rejections": sum(r["gate_rejections"] for r in rs),
        "spent_usd": sum(r["cost_usd"] for r in rs),
        "nominal_cost_usd": nominal,
        "nominal_cost_per_conflict_usd": nominal / n if n else 0.0,
    }


def table(summ: dict[str, dict], title: str) -> str:
    head = ("| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) "
            "| gate rejections | cost | $/conflict |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    lines = [f"**{title}**", "", head]
    for sysname, s in summ.items():
        lines.append(
            f"| {sysname} | {s['n']} | {pct(s['exact'], s['n'])} | {pct(s['semantic'], s['n'])} | {pct(s['ws'], s['n'])} "
            f"| {pct(s['abstained'], s['n'])} | {pct(s['attempted_exact'], s['attempted'])} "
            f"| {pct(s['attempted_semantic'], s['attempted'])} | {s['gate_rejections']} "
            f"| ${s['nominal_cost_usd']:.4f} | ${s['nominal_cost_per_conflict_usd']:.6f} |"
        )
    return "\n".join(lines)


def stage_table(summ: dict[str, dict]) -> str:
    names = ["mergiraf", "llm", "llm_retry", "abstain", "unknown"]
    lines = ["| system | " + " | ".join(names) + " |", "|---|" + "---:|" * len(names)]
    for sysname, s in summ.items():
        lines.append(f"| {sysname} | " + " | ".join(pct(s["stages"].get(k, 0), s["n"]) for k in names) + " |")
    return "\n".join(lines)


def _data_files(track: str, langs: list[str]) -> dict:
    import hashlib

    if track == "A":
        files = [merge_bench.ROOT / "merges" / merge_bench.LANGUAGE_DATASETS[x] / "dataset" / "test" for x in langs]
        files = [f for d in files for f in sorted(d.glob("*.arrow"))]
    else:
        files = [ROOT / "data" / "mined" / f"{x}.jsonl" for x in langs]
    return {str(f.relative_to(ROOT)): {"bytes": f.stat().st_size,
                                       "sha256": hashlib.sha256(f.read_bytes()).hexdigest()}
            for f in files if f.exists()}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--track", choices=["A", "B"], required=True)
    p.add_argument("--systems", nargs="*")
    p.add_argument("--languages", nargs="*")
    p.add_argument("--per-language", type=int, help="items (A) or hunks (B) per language; default all")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--max-spend", type=float, required=True, help="hard cap on NEW spend for this run (USD)")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--no-llm", action="store_true")
    p.add_argument("--run-id")
    p.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    a = p.parse_args()

    load_dotenv()
    langs = a.languages or (list(merge_bench.LANGUAGE_DATASETS) if a.track == "A"
                            else ["python", "javascript", "typescript", "java", "go", "rust"])
    systems = a.systems or TRACK_SYSTEMS[a.track]
    base_cfg = Config()
    if a.no_llm:
        base_cfg.use_llm = False

    items = merge_bench.sample(langs, a.per_language, a.seed) if a.track == "A" else load_mined(langs, a.per_language, a.seed)
    if not items:
        print("no items")
        return 1

    ledger = Budget(base_cfg.budget_usd)
    before = ledger.spent()
    cap = min(base_cfg.budget_usd, before + a.max_spend)
    budget = Budget(cap)
    llm_systems = [s for s in systems if s != "git_default" and s != "mergiraf_only"]
    p_in, _, p_out = PRICES[base_cfg.model]
    if a.track == "A":
        chars = sum(len(SYSTEM_PROMPT) + len(i["snippet"]) + 200 for i in items)
    else:
        chars = sum((len(SYSTEM_PROMPT) + 3 * 400 + base_cfg.context_lines * 40) * i["git_hunks"] for i in items)
    est_in = chars / 4
    n_units = len(items) if a.track == "A" else sum(len(i["hunks"]) for i in items)
    n_calls = len(items) if a.track == "A" else sum(i["git_hunks"] for i in items)
    est_out = 120 * n_calls
    est = (est_in * p_in + est_out * p_out) / 1e6 * (1.15 if "llm_gate" in systems else 1.0) \
        * (1.9 if "hybrid" in systems else 1.0)
    print(f"track {a.track}: {len(items)} items, {n_units} conflicts, systems={systems}, model={base_cfg.model}")
    print(f"spent so far ${before:.4f}, run cap +${a.max_spend:.2f}")
    if llm_systems and not a.no_llm:
        print(f"estimated cost ${est:.3f}")
        if not os.environ.get("OPENAI_API_KEY"):
            print("OPENAI_API_KEY not set")
            return 1
        if not a.yes and input("proceed? [y/N] ").strip().lower() != "y":
            return 1

    resolver = None if a.no_llm else LLMResolver(base_cfg, budget, ResponseCache())
    run_id = a.run_id or dt.datetime.now().strftime(f"%Y%m%d-%H%M%S-track{a.track}")
    out_dir = ROOT / "results" / run_id
    (out_dir / "raw").mkdir(parents=True, exist_ok=True)

    fn = run_item_a if a.track == "A" else run_item_b
    rows: list[dict] = []
    t0 = time.time()
    for system in systems:
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            for res in ex.map(lambda it: fn(it, system, base_cfg, resolver), items):
                rows.extend(res)
        print(f"{system}: {time.time() - t0:.0f}s, ${budget.run_spent:.4f}", flush=True)

    with open(out_dir / "raw" / "predictions.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps({k: r.get(k) for k in ("id", "system", "pred")}) + "\n")
    with open(out_dir / "per_hunk.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps({k: v for k, v in r.items() if k != "pred"}) + "\n")

    spent = Budget(base_cfg.budget_usd).spent() - before
    by_sys = {s: summarize(rows, lambda r, s=s: r["system"] == s) for s in systems}
    by_lang = {lang: {s: summarize(rows, lambda r, s=s, lang=lang: r["system"] == s and r["language"] == lang)
                      for s in systems} for lang in langs}
    extra = {}
    if a.track == "B":
        extra["post_cutoff"] = {s: summarize(rows, lambda r, s=s: r["system"] == s and r["post_cutoff"]) for s in systems}
        extra["pre_cutoff"] = {s: summarize(rows, lambda r, s=s: r["system"] == s and not r["post_cutoff"]) for s in systems}
        extra["merge_bench_sized"] = {s: summarize(rows, lambda r, s=s: r["system"] == s and r["mb_size"]) for s in systems}
    excluded = sum(1 for r in rows if "excluded" in r and r["system"] == systems[0])

    mergiraf_v = subprocess.run([find_mergiraf(), "--version"], capture_output=True, text=True).stdout.strip() \
        if find_mergiraf() else None
    config = {
        "run_id": run_id, "date": dt.datetime.now().isoformat(timespec="seconds"), "track": a.track,
        "systems": systems, "languages": langs, "per_language": a.per_language, "seed": a.seed,
        "n_items": len(items), "n_conflicts": n_units, "excluded": excluded,
        "max_file_hunks": MAX_FILE_HUNKS if a.track == "B" else None,
        "model": None if a.no_llm else base_cfg.model, "reasoning_effort": base_cfg.reasoning_effort,
        "prices_per_1M": dict(zip(("input", "cached_input", "output"), PRICES[base_cfg.model])),
        "context_lines": base_cfg.context_lines, "context_chars_per_side": base_cfg.context_chars,
        "max_hunk_lines": base_cfg.max_hunk_lines, "max_hunk_chars": base_cfg.max_hunk_chars,
        "retries": base_cfg.retries, "mergiraf": mergiraf_v, "model_cutoff": MODEL_CUTOFF,
        "spent_this_run_usd": spent, "ledger_total_usd": before + spent,
        "llm_calls_this_run": budget.run_calls,
        "cache": {"hits": resolver.cache.hits if resolver else 0, "misses": resolver.cache.misses if resolver else 0},
        "wall_seconds": round(time.time() - t0, 1),
        "command": " ".join(sys.argv),
        "data_files": _data_files(a.track, langs),
    }
    (out_dir / "config.json").write_text(json.dumps(config, indent=2))
    (out_dir / "summary.json").write_text(json.dumps({"overall": by_sys, "by_language": by_lang, **extra}, indent=2))

    md = [f"# Run {run_id} (track {a.track})", "",
          f"model `{config['model']}` (reasoning_effort={base_cfg.reasoning_effort}), seed {a.seed}, "
          f"{n_units} conflicts from {len(items)} items, {excluded} excluded. Spent this run: ${spent:.4f}.", "",
          "Cost columns are nominal (what each system's calls cost without the shared cache).", "",
          table(by_sys, "Overall"), "", "Stage that handled each conflict:", "", stage_table(by_sys), ""]
    for lang in langs:
        md += [table(by_lang[lang], lang), ""]
    for k, v in extra.items():
        md += [table(v, k), ""]
    (out_dir / "summary.md").write_text("\n".join(md))
    print("\n".join(md[:12]))
    print(f"\nwrote {out_dir}")
    print(f"spend: this run ${spent:.4f}; ledger total ${before + spent:.4f} of ${base_cfg.budget_usd:.2f} cap")
    return 0


if __name__ == "__main__":
    sys.exit(main())
