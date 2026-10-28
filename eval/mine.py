from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from metrics import has_conflict_markers, locate, region_text
from unconflict import conflict
from unconflict.config import EXT_TO_LANG
from unconflict.structured import git_merge

DATA = Path(__file__).resolve().parent.parent / "data"
CONTEXT = 5
MAX_FILE_BYTES = 300_000


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=check)


def clone(name: str) -> Path:
    dest = DATA / "repos" / name.replace("/", "__")
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"  cloning {name} ...", flush=True)
        subprocess.run(["git", "clone", "-q", "--bare", f"https://github.com/{name}.git", str(dest)], check=True)
    return dest


def blob(repo: Path, commit: str, path: str) -> str | None:
    p = git(repo, "cat-file", "-p", f"{commit}:{path}", check=False)
    if p.returncode != 0 or len(p.stdout) > MAX_FILE_BYTES or b"\0" in p.stdout[:8000]:
        return None
    try:
        return p.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None


def hunk_specs(conflicted: str, merged: str) -> list[dict]:
    segs = conflict.parse(conflicted)
    specs = []
    for k, s in enumerate(segs):
        if not isinstance(s, conflict.Hunk):
            continue
        prev = segs[k - 1] if k > 0 else None
        nxt = segs[k + 1] if k + 1 < len(segs) else None
        if isinstance(prev, conflict.Hunk) or isinstance(nxt, conflict.Hunk):
            continue
        before = prev.splitlines()[-CONTEXT:] if prev else []
        after = nxt.splitlines()[:CONTEXT] if nxt else []
        at_start, at_end = prev is None, nxt is None
        region = locate(merged, before, after, at_start, at_end)
        if region is None:
            continue
        gold = region_text(merged, region)
        if has_conflict_markers(gold):
            continue
        n_lines = len(s.render())
        specs.append({
            "k": k, "before": before, "after": after, "at_start": at_start, "at_end": at_end,
            "gold": gold, "conflict_lines": n_lines,
            "mb_size": n_lines + len(before) + len(after) <= 20,
        })
    return specs


def mine_repo(name: str, language: str, max_merges: int, max_files: int, since: str | None,
              keep_clone: bool = False) -> list[dict]:
    repo = clone(name)
    try:
        return _mine(repo, name, language, max_merges, max_files, since)
    finally:
        if not keep_clone:
            shutil.rmtree(repo, ignore_errors=True)


def _mine(repo: Path, name: str, language: str, max_merges: int, max_files: int, since: str | None) -> list[dict]:
    args = ["log", "--merges", "--format=%H %P %cI", f"-n{max_merges}", "--all"]
    if since:
        args.append(f"--since={since}")
    lines = git(repo, *args).stdout.decode().splitlines()
    out: list[dict] = []
    seen_files: set[tuple] = set()
    for line in lines:
        parts = line.split()
        if len(parts) != 4:
            continue
        merge, p1, p2, date = parts
        bases = git(repo, "merge-base", "--all", p1, p2, check=False).stdout.decode().split()
        if len(bases) != 1:
            continue
        base = bases[0]
        mt = git(repo, "merge-tree", "--write-tree", "--name-only", "--no-messages", p1, p2, check=False)
        if mt.returncode != 1:
            continue
        paths = mt.stdout.decode(errors="replace").splitlines()[1:]
        for path in dict.fromkeys(p for p in paths if p):
            if EXT_TO_LANG.get(Path(path).suffix.lower()) != language:
                continue
            versions = [blob(repo, c, path) for c in (base, p1, p2, merge)]
            if any(v is None for v in versions):
                continue
            b, o, t, m = versions
            key = (path, b, o, t)
            if key in seen_files:
                continue
            floor = git_merge(b, o, t)
            if floor.clean:
                continue
            specs = hunk_specs(floor.text, m)
            if not specs:
                continue
            seen_files.add(key)
            out.append({
                "id": f"{name}@{merge[:10]}:{path}", "repo": name, "merge": merge, "parents": [p1, p2],
                "base_commit": base, "path": path, "language": language, "date": date,
                "base": b, "ours": o, "theirs": t, "merged": m,
                "git_hunks": len(conflict.hunks(conflict.parse(floor.text))), "hunks": specs,
            })
            if len(out) >= max_files:
                return out
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--language", required=True)
    p.add_argument("--repos", nargs="+", required=True)
    p.add_argument("--max-merges", type=int, default=3000, help="newest merge commits examined per repo")
    p.add_argument("--max-files", type=int, default=40, help="conflicted files kept per repo")
    p.add_argument("--since", help="only merges committed after this date")
    p.add_argument("--out", help="JSONL output (default data/mined/<language>.jsonl)")
    p.add_argument("--keep-clone", action="store_true", help="don't delete the clone after mining")
    a = p.parse_args()
    out = Path(a.out) if a.out else DATA / "mined" / f"{a.language}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    existing = {json.loads(x)["id"] for x in out.read_text().splitlines()} if out.exists() else set()
    with open(out, "a") as fh:
        for name in a.repos:
            print(f"{name}:", flush=True)
            try:
                recs = mine_repo(name, a.language, a.max_merges, a.max_files, a.since, a.keep_clone)
            except subprocess.CalledProcessError as e:
                print(f"  failed: {e.stderr.decode(errors='replace')[:200] if e.stderr else e}")
                continue
            new = [r for r in recs if r["id"] not in existing]
            for r in new:
                fh.write(json.dumps(r) + "\n")
            n_h = sum(len(r["hunks"]) for r in new)
            print(f"  kept {len(new)} files / {n_h} scorable hunks", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
