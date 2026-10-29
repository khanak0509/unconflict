from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "eval"))

from run import MAX_FILE_HUNKS, load_dotenv
from unconflict.budget import Budget
from unconflict.cache import ResponseCache
from unconflict.config import Config
from unconflict.llm import LLMResolver
from unconflict.pipeline import resolve_sides
from unconflict.structured import git_merge, mergiraf_merge

from metrics import has_conflict_markers, ws_normalize

WORK = ROOT / "data" / "testcheck"
SYSTEMS = ["git_default", "mergiraf_only", "llm_only", "hybrid", "ours_only", "theirs_only"]


def outputs(rec: dict, resolver) -> dict[str, str]:
    b, o, t, path = rec["base"], rec["ours"], rec["theirs"], rec["path"]
    m = mergiraf_merge(b, o, t, path)
    llm_cfg = Config(use_structured=False, use_gate=False)
    return {
        "git_default": git_merge(b, o, t).text,
        "mergiraf_only": m.text if m is not None else git_merge(b, o, t).text,
        "llm_only": resolve_sides(b, o, t, path, llm_cfg, resolver).text,
        "hybrid": resolve_sides(b, o, t, path, Config(), resolver).text,
        "ours_only": o,
        "theirs_only": t,
    }


def sh(cmd, cwd=None, timeout=900, env=None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)


def failing_tests(wt: Path, py: Path, junit: Path, timeout: int) -> tuple[str, set[str]]:
    junit.unlink(missing_ok=True)
    try:
        p = sh([str(py), "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={junit}", "tests"],
               cwd=wt, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "timeout", set()
    if p.returncode in (2, 3, 4, 5) or not junit.exists():
        return f"error(exit {p.returncode})", set()
    failed = set()
    for case in ET.parse(junit).getroot().iter("testcase"):
        if case.find("failure") is not None or case.find("error") is not None:
            failed.add(f"{case.get('classname')}::{case.get('name')}")
    return "ok", failed


def setup_env(wt: Path, env: Path, python: str, date: str) -> str | None:
    shutil.rmtree(env, ignore_errors=True)
    if sh(["uv", "venv", "-q", "--python", python, str(env)]).returncode != 0:
        return "uv venv failed"
    cutoff = (dt.datetime.fromisoformat(date) + dt.timedelta(days=1)).astimezone(dt.timezone.utc)
    stamp = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
    extra = ["-r", "requirements/tests.txt"] if (wt / "requirements" / "tests.txt").exists() else ["pytest"]
    p = sh(["uv", "pip", "install", "-q", "--python", str(env / "bin" / "python"), "--exclude-newer", stamp,
            "-e", ".", *extra], cwd=wt)
    if p.returncode != 0 and extra[0] == "-r":
        p = sh(["uv", "pip", "install", "-q", "--python", str(env / "bin" / "python"), "--exclude-newer", stamp,
                "-e", ".", "pytest"], cwd=wt)
    return None if p.returncode == 0 else "install failed: " + p.stderr.strip().splitlines()[-1][:200]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="mitsuhiko/flask")
    ap.add_argument("--clone", default=str(WORK / "flask"))
    ap.add_argument("--python", default="3.11")
    ap.add_argument("--max-spend", type=float, default=0.01)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--dry-run", action="store_true", help="build outputs and show the plan; run nothing external")
    ap.add_argument("--run-id", default="testcheck-flask")
    a = ap.parse_args()

    load_dotenv()
    recs = [json.loads(x) for x in (ROOT / "data" / "mined" / "python.jsonl").read_text().splitlines()]
    recs = [r for r in recs if r["repo"] == a.repo and r["git_hunks"] <= MAX_FILE_HUNKS]
    before = Budget(Config().budget_usd).spent()
    budget = Budget(min(Config().budget_usd, before + a.max_spend))
    cache = ResponseCache()
    resolver = LLMResolver(Config(), budget, cache)

    plan = []
    for r in recs:
        outs = outputs(r, resolver)
        variants = {}
        for s, text in outs.items():
            if has_conflict_markers(text):
                variants[s] = "abstained"
            elif text == r["merged"]:
                variants[s] = "identical"
            else:
                variants[s] = text
        plan.append((r, variants))
    print(f"{len(plan)} files from {len({r['merge'] for r, _ in plan})} merges; "
          f"LLM cache hits {cache.hits}, misses {cache.misses}, new spend ${budget.run_spent:.5f}")
    to_run = Counter(s for _, v in plan for s, x in v.items() if x not in ("abstained", "identical"))
    print("test runs needed per system:", dict(to_run))
    if a.dry_run:
        return 0

    clone, wt, env = Path(a.clone), WORK / "wt-check", WORK / "env-check"
    out_dir = ROOT / "results" / a.run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    by_merge = defaultdict(list)
    for r, v in plan:
        by_merge[r["merge"]].append((r, v))
    t0 = time.time()
    for k, (merge, items) in enumerate(sorted(by_merge.items(), key=lambda x: x[1][0][0]["date"])):
        date = items[0][0]["date"]
        sh(["git", "-C", str(clone), "worktree", "remove", "--force", str(wt)])
        shutil.rmtree(wt, ignore_errors=True)
        if sh(["git", "-C", str(clone), "worktree", "add", "-q", "--detach", str(wt), merge]).returncode != 0:
            for r, v in items:
                rows.append({"file_id": r["id"], "merge": merge, "status": "checkout failed"})
            continue
        problem = setup_env(wt, env, a.python, date)
        py = env / "bin" / "python"
        base_status, base_fail = ("skipped", set()) if problem else failing_tests(wt, py, WORK / "junit.xml", a.timeout)
        print(f"[{k + 1}/{len(by_merge)}] {merge[:10]} {date[:10]}: env {problem or 'ok'}, "
              f"developer version tests {base_status} ({len(base_fail)} failing)", flush=True)
        for r, v in items:
            row = {"file_id": r["id"], "merge": merge, "date": date, "path": r["path"],
                   "baseline": base_status, "baseline_failures": len(base_fail), "systems": {}}
            if problem or base_status != "ok":
                row["status"] = problem or f"baseline {base_status}"
                rows.append(row)
                continue
            target = wt / r["path"]
            original = target.read_text()
            for s, x in v.items():
                if x in ("abstained", "identical"):
                    row["systems"][s] = {"result": x}
                    continue
                target.write_text(x)
                status, fail = failing_tests(wt, py, WORK / "junit.xml", a.timeout)
                new = sorted(fail - base_fail)
                ok = status == "ok" and not new
                row["systems"][s] = {"result": "passes" if ok else "fails", "status": status,
                                     "new_failures": len(new), "ws_equal": ws_normalize(x) == ws_normalize(r["merged"])}
                target.write_text(original)
            row["status"] = "tested"
            rows.append(row)
        (out_dir / "files.jsonl").write_text("\n".join(json.dumps(x) for x in rows) + "\n")
    shutil.rmtree(env, ignore_errors=True)
    sh(["git", "-C", str(clone), "worktree", "remove", "--force", str(wt)])

    tested = [x for x in rows if x.get("status") == "tested"]
    summary = {}
    for s in SYSTEMS:
        c = Counter(x["systems"][s]["result"] for x in tested)
        n = len(tested)
        summary[s] = {"n_files": n, **c, "tests_pass": c["identical"] + c["passes"]}
    config = {"run_id": a.run_id, "date": dt.datetime.now().isoformat(timespec="seconds"), "repo": a.repo,
              "python": a.python, "files": len(rows), "tested_files": len(tested),
              "skipped": dict(Counter(x["status"] for x in rows if x.get("status") != "tested")),
              "rule": "a variant passes if pytest collects and no test fails that didn't fail on the developer's version",
              "deps": "uv pip install --exclude-newer <merge date + 1 day> -e . (+ requirements/tests.txt)",
              "wall_seconds": round(time.time() - t0), "new_llm_spend_usd": budget.run_spent}
    (out_dir / "config.json").write_text(json.dumps(config, indent=2))
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    lines = ["| system | files | identical to developer | different but tests pass | tests fail | abstained | tests pass (total) |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for s, v in summary.items():
        n = v["n_files"] or 1
        lines.append(f"| {s} | {v['n_files']} | {v.get('identical', 0)} | {v.get('passes', 0)} | {v.get('fails', 0)} "
                     f"| {v.get('abstained', 0)} | {v['tests_pass']} ({100 * v['tests_pass'] / n:.0f}%) |")
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(config, indent=2))
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
