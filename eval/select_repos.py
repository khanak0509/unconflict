from __future__ import annotations

import argparse
import csv
import io
import re
import subprocess
import sys
import urllib.request

LISTS = {
    "python": "repos_reaper_Python_0_1000.csv",
    "java": "repos_reaper_Java_0_1000.csv",
    "javascript": "repos_github_Javascript_0_1000.csv",
    "typescript": "repos_github_Typescript_0_1000.csv",
    "go": "repos_github_Go_0_1000.csv",
    "rust": "repos_github_Rust_0_1000.csv",
}
BASE = "https://raw.githubusercontent.com/benedikt-schesch/Merge-Bench-Builder/main/input_data/"
NOT_CODE = re.compile(r"awesome|list of|interview|roadmap|tutorial|book|cheat|guide|course|learn|"
                      r"algorithms|patterns|examples|prompts|30-seconds|clean-code|handbook|free-programming|"
                      r"beginners|computer-science|readme-stats",
                      re.IGNORECASE)


def head_of(repo: str) -> str | None:
    p = subprocess.run(["git", "ls-remote", f"https://github.com/{repo}.git", "HEAD"],
                       capture_output=True, text=True, timeout=60,
                       env={"GIT_TERMINAL_PROMPT": "0", "PATH": "/usr/bin:/bin:/opt/homebrew/bin"})
    return p.stdout.split()[0] if p.returncode == 0 and p.stdout.strip() else None


def pick(language: str, n: int) -> list[str]:
    rows = list(csv.DictReader(io.StringIO(urllib.request.urlopen(BASE + LISTS[language]).read().decode())))
    out, heads = [], set()
    for r in rows:
        name = r["repository"]
        if r.get("archived") == "True":
            continue
        if "updated_at" in r and int(r.get("size") or 0) > 150_000:
            continue
        if NOT_CODE.search(name) or NOT_CODE.search(r.get("description") or ""):
            continue
        head = head_of(name)
        if head and head not in heads:
            heads.add(head)
            out.append(name)
        if len(out) == n:
            break
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=6)
    p.add_argument("--languages", nargs="*", default=list(LISTS))
    a = p.parse_args()
    for lang in a.languages:
        print(f"{lang}: {' '.join(pick(lang, a.n))}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
