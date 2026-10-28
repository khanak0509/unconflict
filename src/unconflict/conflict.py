from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Union

_START = re.compile(r"^(<{7,})(?: ([^\r\n]*))?\r?\n?$")
_BASE = re.compile(r"^(\|{7,})(?: ([^\r\n]*))?\r?\n?$")
_SEP = re.compile(r"^(={7,})\r?\n?$")
_END = re.compile(r"^(>{7,})(?: ([^\r\n]*))?\r?\n?$")

MARKER_RE = re.compile(r"^(<{7,}|\|{7,}|={7,}|>{7,})(?: .*)?$", re.MULTILINE)


class ConflictParseError(ValueError):
    pass


@dataclass
class Hunk:
    ours: list[str]
    theirs: list[str]
    base: Optional[list[str]] = None
    ours_label: str = ""
    base_label: str = ""
    theirs_label: str = ""
    marker_size: int = 7

    @property
    def has_base(self) -> bool:
        return self.base is not None

    def render(self) -> list[str]:
        n = self.marker_size
        nl = _newline_of(self.ours + self.theirs + (self.base or []))
        out = [_marker("<" * n, self.ours_label, nl)]
        out += _ensure_trailing_newline(self.ours, nl)
        if self.base is not None:
            out.append(_marker("|" * n, self.base_label, nl))
            out += _ensure_trailing_newline(self.base, nl)
        out.append("=" * n + nl)
        out += _ensure_trailing_newline(self.theirs, nl)
        out.append(_marker(">" * n, self.theirs_label, nl))
        return out


Segment = Union[str, Hunk]


def _marker(chars: str, label: str, nl: str) -> str:
    return f"{chars} {label}{nl}" if label else f"{chars}{nl}"


def _newline_of(lines: list[str]) -> str:
    for line in lines:
        if line.endswith("\r\n"):
            return "\r\n"
        if line.endswith("\n"):
            return "\n"
    return "\n"


def _ensure_trailing_newline(lines: list[str], nl: str) -> list[str]:
    if lines and not lines[-1].endswith("\n"):
        return lines[:-1] + [lines[-1] + nl]
    return lines


def parse(text: str) -> list[Segment]:
    lines = text.splitlines(keepends=True)
    segments: list[Segment] = []
    plain: list[str] = []
    i = 0
    while i < len(lines):
        m = _START.match(lines[i])
        if not m:
            plain.append(lines[i])
            i += 1
            continue
        size = len(m.group(1))
        hunk = Hunk(ours=[], theirs=[], ours_label=m.group(2) or "", marker_size=size)
        section = "ours"
        i += 1
        closed = False
        while i < len(lines):
            line = lines[i]
            if (b := _BASE.match(line)) and len(b.group(1)) == size and section == "ours":
                section = "base"
                hunk.base = []
                hunk.base_label = b.group(2) or ""
            elif (s := _SEP.match(line)) and len(s.group(1)) == size and section in ("ours", "base"):
                section = "theirs"
            elif (e := _END.match(line)) and len(e.group(1)) == size and section == "theirs":
                hunk.theirs_label = e.group(2) or ""
                closed = True
                i += 1
                break
            elif _START.match(line) and len(_START.match(line).group(1)) == size:
                raise ConflictParseError(f"nested conflict start at line {i + 1}")
            else:
                getattr(hunk, section).append(line)
            i += 1
        if not closed:
            raise ConflictParseError("unterminated conflict (missing >>>>>>> marker)")
        if plain:
            segments.append("".join(plain))
            plain = []
        segments.append(hunk)
    if plain:
        segments.append("".join(plain))
    return segments


def render(segments: list[Segment]) -> str:
    out: list[str] = []
    for seg in segments:
        if isinstance(seg, Hunk):
            out.extend(seg.render())
        else:
            out.append(seg)
    return "".join(out)


def hunks(segments: list[Segment]) -> list[Hunk]:
    return [s for s in segments if isinstance(s, Hunk)]


def has_conflicts(text: str) -> bool:
    return any(isinstance(s, Hunk) for s in parse(text))


def side(segments: list[Segment], which: str) -> str:
    out: list[str] = []
    for seg in segments:
        if isinstance(seg, Hunk):
            part = getattr(seg, which)
            if part is None:
                raise ValueError("2-way conflict has no base section")
            out.extend(part)
        else:
            out.append(seg)
    return "".join(out)


def all_have_base(segments: list[Segment]) -> bool:
    hs = hunks(segments)
    return bool(hs) and all(h.has_base for h in hs)


def marker_lines(text: str) -> list[str]:
    return MARKER_RE.findall(text)
