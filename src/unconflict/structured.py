from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MergeOutput:
    text: str
    clean: bool
    tool: str
    note: str = ""


def find_mergiraf() -> str | None:
    explicit = os.environ.get("UNCONFLICT_MERGIRAF")
    if explicit:
        return explicit if Path(explicit).exists() else None
    return shutil.which("mergiraf")


def _write_sides(tmp: Path, base: str, ours: str, theirs: str, suffix: str) -> tuple[Path, Path, Path]:
    paths = []
    for name, content in (("base", base), ("ours", ours), ("theirs", theirs)):
        p = tmp / f"{name}{suffix}"
        p.write_text(content, encoding="utf-8", newline="")
        paths.append(p)
    return paths[0], paths[1], paths[2]


def git_merge(base: str, ours: str, theirs: str, labels=("ours", "base", "theirs")) -> MergeOutput:
    with tempfile.TemporaryDirectory(prefix="unconflict-") as d:
        b, o, t = _write_sides(Path(d), base, ours, theirs, ".txt")
        proc = subprocess.run(
            ["git", "merge-file", "--diff3", "-p", "-L", labels[0], "-L", labels[1], "-L", labels[2],
             str(o), str(b), str(t)],
            capture_output=True,
        )
    if proc.returncode < 0 or proc.returncode > 127:
        raise RuntimeError(f"git merge-file failed: {proc.stderr.decode(errors='replace')}")
    return MergeOutput(proc.stdout.decode("utf-8", errors="surrogateescape"), proc.returncode == 0, "git")


def mergiraf_merge(
    base: str,
    ours: str,
    theirs: str,
    path_name: str,
    labels=("ours", "base", "theirs"),
    timeout_s: float = 30.0,
) -> MergeOutput | None:
    exe = find_mergiraf()
    if exe is None:
        return None
    suffix = Path(path_name).suffix or ".txt"
    with tempfile.TemporaryDirectory(prefix="unconflict-") as d:
        b, o, t = _write_sides(Path(d), base, ours, theirs, suffix)
        out = Path(d) / f"out{suffix}"
        cmd = [
            exe, "merge", str(b), str(o), str(t), "-o", str(out), "-p", path_name,
            "-x", labels[0], "-s", labels[1], "-y", labels[2],
            "-t", str(int(timeout_s * 1000)),
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, timeout=timeout_s + 10)
        except subprocess.TimeoutExpired:
            return None
        if proc.returncode not in (0, 1) or not out.exists():
            return None
        text = out.read_text(encoding="utf-8", errors="surrogateescape")
    note = proc.stderr.decode(errors="replace").strip().splitlines()
    return MergeOutput(text, proc.returncode == 0, "mergiraf", note[-1] if note else "")
