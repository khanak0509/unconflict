# normalize_code and the regexes below are from Merge-Bench (https://github.com/benedikt-schesch/Merge-Bench), MIT License, Copyright (c) 2025 Benedikt Schesch

from __future__ import annotations

import re

BLOCK_COMMENT_RE = re.compile(r"/\*[\s\S]*?\*/")
LINE_COMMENT_RE = re.compile(r"//.*")
HASH_COMMENT_RE = re.compile(r"#.*")
WHITESPACE_RE = re.compile(r"\s+")
CONFLICT_MARKERS = ["<<<<<<<", "=======", "|||||||", ">>>>>>>"]


def normalize_code(code: str, language: str = "generic") -> str:
    if language in ["javascript", "java", "c", "cpp", "csharp", "rust", "php", "typescript"]:
        code = BLOCK_COMMENT_RE.sub("", code)
        code = LINE_COMMENT_RE.sub("", code)
    elif language in ["python", "ruby"]:
        code = HASH_COMMENT_RE.sub("", code)
        code = re.sub(r'"""[\s\S]*?"""', "", code)
        code = re.sub(r"'''[\s\S]*?'''", "", code)
    elif language == "go":
        code = BLOCK_COMMENT_RE.sub("", code)
        code = LINE_COMMENT_RE.sub("", code)
    if language not in ["python", "go", "ruby"]:
        code = WHITESPACE_RE.sub(" ", code)
        return code.strip()
    return code.strip()


def has_conflict_markers(code: str) -> bool:
    return any(marker in code for marker in CONFLICT_MARKERS)


def ws_normalize(code: str) -> str:
    return " ".join(code.split())


def score(pred: str | None, gold: str, language: str, abstained: bool | None = None) -> dict:
    if pred is None:
        return {"outcome": "unlocatable", "exact": False, "semantic": False, "ws": False,
                "abstained": bool(abstained)}
    exact = pred.strip() == gold.strip()
    semantic = exact or normalize_code(pred.strip(), language) == normalize_code(gold.strip(), language)
    ws = exact or ws_normalize(pred) == ws_normalize(gold)
    if abstained is None:
        abstained = has_conflict_markers(pred) and not exact
    if exact:
        outcome = "exact"
    elif semantic:
        outcome = "semantic"
    elif abstained:
        outcome = "conflict"
    else:
        outcome = "different"
    return {"outcome": outcome, "exact": exact, "semantic": semantic, "ws": ws, "abstained": bool(abstained)}


def _key(line: str) -> str:
    return line.rstrip()


def locate(text: str, before: list[str], after: list[str], at_start: bool, at_end: bool) -> tuple[int, int] | None:
    lines = [_key(x) for x in text.splitlines()]
    b = [_key(x) for x in before]
    a = [_key(x) for x in after]
    if not b:
        if not at_start:
            return None
        starts = [0]
    else:
        n = len(b)
        starts = [p + n for p in range(len(lines) - n + 1) if lines[p:p + n] == b]
    regions = []
    for s in starts:
        if not a:
            if at_end:
                regions.append((s, len(lines)))
            continue
        m = len(a)
        for q in range(s, len(lines) - m + 1):
            if lines[q:q + m] == a:
                regions.append((s, q))
                break
    return regions[0] if len(regions) == 1 else None


def region_text(text: str, region: tuple[int, int]) -> str:
    lines = text.splitlines(keepends=True)
    return "".join(lines[region[0]:region[1]])
