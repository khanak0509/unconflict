from __future__ import annotations

import argparse
import glob
import random
import re
import sys
import tarfile
import urllib.request
from collections import Counter
from pathlib import Path

URL = "https://github.com/benedikt-schesch/Merge-Bench/releases/download/main/merges.tar.gz"
ROOT = Path(__file__).resolve().parent.parent / "data" / "merge_bench"

LANGUAGE_DATASETS = {
    "javascript": "repos_github_javascript",
    "java": "repos_reaper_java",
    "rust": "repos_github_rust",
    "c": "repos_reaper_c",
    "cpp": "repos_reaper_cpp",
    "csharp": "repos_reaper_csharp",
    "php": "repos_reaper_php",
    "python": "repos_reaper_python",
    "ruby": "repos_reaper_ruby",
    "go": "repos_github_go",
    "typescript": "repos_github_typescript",
}

_CODE_BLOCK = re.compile(r"```[^\n]*\n(.*?)\n```", re.DOTALL)


def download(root: Path = ROOT) -> None:
    root.mkdir(parents=True, exist_ok=True)
    tgz = root / "merges.tar.gz"
    if not tgz.exists():
        print(f"downloading {URL}")
        urllib.request.urlretrieve(URL, tgz)
    with tarfile.open(tgz) as tf:
        tf.extractall(root, filter="data")
    print(f"extracted into {root}")


def load(language: str, root: Path = ROOT) -> list[dict]:
    import pyarrow as pa

    d = root / "merges" / LANGUAGE_DATASETS[language] / "dataset" / "test"
    files = sorted(glob.glob(str(d / "*.arrow")))
    if not files:
        raise FileNotFoundError(f"{d} not found; run `python eval/merge_bench.py --download`")
    rows = []
    for f in files:
        with pa.memory_map(f) as src:
            rows += pa.ipc.open_stream(src).read_all().to_pylist()
    out = []
    for i, r in enumerate(rows):
        m = _CODE_BLOCK.search(r["question"])
        if not m:
            continue
        out.append({
            "id": f"{language}:{i}",
            "language": language,
            "snippet": m.group(1) + "\n",
            "answer": r["answer"],
            "question": r["question"],
        })
    return out


def sample(languages: list[str], per_language: int | None, seed: int, root: Path = ROOT) -> list[dict]:
    picked = []
    for lang in languages:
        seen, rows = set(), []
        for r in load(lang, root):
            if r["question"] not in seen:
                seen.add(r["question"])
                rows.append(r)
        rng = random.Random(f"{seed}:{lang}")
        rng.shuffle(rows)
        picked += rows if per_language is None else rows[:per_language]
    return picked


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--download", action="store_true")
    p.add_argument("--stats", action="store_true")
    a = p.parse_args()
    if a.download:
        download()
    if a.stats:
        total = 0
        for lang in LANGUAGE_DATASETS:
            rows = load(lang)
            uniq = len({r["question"] for r in rows})
            base = sum("\n|||||||" in r["snippet"] for r in rows)
            multi = Counter(r["snippet"].count("\n<<<<<<<") + r["snippet"].startswith("<<<<<<<") > 1 for r in rows)[True]
            total += len(rows)
            print(f"{lang:11s} rows={len(rows):4d} unique={uniq:4d} with_base={base} multi_conflict={multi}")
        print("total", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
