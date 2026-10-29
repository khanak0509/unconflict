from __future__ import annotations

from dataclasses import dataclass, field

from . import conflict, gate
from .budget import BudgetExceeded, cost_usd
from .config import Config, language_for_path
from .llm import HunkRequest, LLMResolver
from .structured import git_merge, mergiraf_merge


@dataclass
class HunkLog:
    index: int
    stage: str
    reason: str = ""
    cost_usd: float = 0.0
    lines: tuple[int, int] | None = None


@dataclass
class ResolveResult:
    text: str
    resolved: bool
    git_hunks: int
    stage1: str
    stage1_remaining: int
    hunks: list[HunkLog] = field(default_factory=list)
    cost_usd: float = 0.0
    nominal_cost_usd: float = 0.0
    llm_calls: int = 0
    gate_rejections: int = 0
    gate_skipped: list[str] = field(default_factory=list)
    language: str | None = None
    stage1_text: str = ""

    def summary(self) -> str:
        n = {s: sum(1 for h in self.hunks if h.stage == s) for s in ("llm", "llm_retry", "abstain")}
        lines = [
            f"language: {self.language or 'unknown'}",
            f"git conflicts: {self.git_hunks}" if self.git_hunks >= 0 else "git conflicts: n/a",
            f"stage 1 (structured): {self.stage1}; {self.stage1_remaining} conflict(s) left",
        ]
        if self.hunks:
            lines.append(
                f"stage 2/3 (LLM + gate): {n['llm']} resolved, {n['llm_retry']} resolved after retry, "
                f"{n['abstain']} left for you; gate rejected {self.gate_rejections} LLM output(s)"
            )
            for h in self.hunks:
                where = ""
                if h.lines:
                    a, b = h.lines
                    where = f" lines {a}-{b}" if b > a else f" line {a}" if b == a else f" deleted at line {a}"
                lines.append(f"  conflict #{h.index + 1}: {h.stage}{where}" + (f" ({h.reason})" if h.reason else ""))
        for s in self.gate_skipped:
            lines.append(f"note: gate check skipped: {s}")
        lines.append("result: fully resolved" if self.resolved else "result: conflicts remain (left for you)")
        return "\n".join(lines)

    @property
    def used_llm(self) -> bool:
        return any(h.stage in ("llm", "llm_retry") for h in self.hunks)


def _count(text: str) -> int:
    try:
        return len(conflict.hunks(conflict.parse(text)))
    except conflict.ConflictParseError:
        return -1


def resolve_sides(
    base: str,
    ours: str,
    theirs: str,
    path: str | None,
    cfg: Config,
    resolver: LLMResolver | None,
    labels: tuple[str, str, str] = ("ours", "base", "theirs"),
) -> ResolveResult:
    lang = language_for_path(path)
    floor = git_merge(base, ours, theirs, labels)
    git_hunks = _count(floor.text)
    if floor.clean:
        return ResolveResult(floor.text, True, 0, "skipped: git merged cleanly", 0, language=lang,
                             stage1_text=floor.text)

    text, stage1 = floor.text, "skipped: disabled"
    if cfg.use_structured:
        m = mergiraf_merge(base, ours, theirs, path or "file.txt", labels, cfg.mergiraf_timeout_s)
        if m is None:
            stage1 = "skipped: mergiraf not installed or failed"
        else:
            check = gate.check(_placeholder(m.text), ours, theirs, lang) if cfg.use_gate else None
            if check is not None and not check.ok:
                stage1 = f"mergiraf-rejected ({check.describe()})"
            else:
                text, stage1 = m.text, "mergiraf"
    res = _stage23(text, ours, theirs, path, lang, cfg, resolver)
    res.git_hunks, res.stage1 = git_hunks, stage1
    return res


def resolve_text(text: str, path: str | None, cfg: Config, resolver: LLMResolver | None) -> ResolveResult:
    lang = language_for_path(path)
    segs = conflict.parse(text)
    hs = conflict.hunks(segs)
    if not hs:
        return ResolveResult(text, True, 0, "skipped: no conflicts", 0, language=lang)
    if conflict.all_have_base(segs):
        h0 = hs[0]
        labels = (h0.ours_label or "ours", h0.base_label or "base", h0.theirs_label or "theirs")
        return resolve_sides(
            conflict.side(segs, "base"), conflict.side(segs, "ours"), conflict.side(segs, "theirs"),
            path, cfg, resolver, labels,
        )
    res = _stage23(text, conflict.side(segs, "ours"), conflict.side(segs, "theirs"), path, lang, cfg, resolver)
    res.git_hunks = len(hs)
    res.stage1 = "skipped: no base in conflict markers (set `git config merge.conflictStyle diff3`)"
    return res


def _placeholder(text: str) -> str:
    segs = conflict.parse(text)
    return "".join("".join(s.ours) if isinstance(s, conflict.Hunk) else s for s in segs)


def _context(segs: list, k: int, n_before: int, n_after: int, max_chars: int) -> tuple[str, str]:
    before = segs[k - 1] if k > 0 and isinstance(segs[k - 1], str) else ""
    after = segs[k + 1] if k + 1 < len(segs) and isinstance(segs[k + 1], str) else ""
    b = before.splitlines(keepends=True)[-n_before:] if n_before else []
    a = after.splitlines(keepends=True)[:n_after] if n_after else []
    while b and sum(map(len, b)) > max_chars:
        b.pop(0)
    while a and sum(map(len, a)) > max_chars:
        a.pop()
    return "".join(b), "".join(a)


def _as_lines(code: str, nl: str) -> list[str]:
    if code and not code.endswith("\n"):
        code += nl
    return code.splitlines(keepends=True)


def _stage23(
    text: str, ours_full: str, theirs_full: str, path: str | None, lang: str | None,
    cfg: Config, resolver: LLMResolver | None,
) -> ResolveResult:
    segs = conflict.parse(text)
    idx = [k for k, s in enumerate(segs) if isinstance(s, conflict.Hunk)]
    res = ResolveResult(text, not idx, -1, "", len(idx), language=lang, stage1_text=text)
    if not idx:
        return res
    nl = "\r\n" if "\r\n" in text else "\n"
    n_before = cfg.context_lines // 2
    n_after = cfg.context_lines - n_before

    requests: dict[int, HunkRequest] = {}
    resolved: dict[int, list[str]] = {}
    logs: dict[int, HunkLog] = {}
    budget_out = False

    def ask(i: int, feedback=None) -> list[str] | None:
        nonlocal budget_out
        if budget_out:
            logs[i] = HunkLog(i, "abstain", "LLM budget cap reached")
            return None
        try:
            ans = resolver.resolve(requests[i], feedback)
        except BudgetExceeded as e:
            budget_out = True
            logs[i] = HunkLog(i, "abstain", str(e))
            return None
        res.cost_usd += ans.cost_usd
        if ans.usage.input_tokens or ans.usage.output_tokens:
            res.nominal_cost_usd += cost_usd(resolver.cfg.model, ans.usage)
        res.llm_calls += 0 if ans.cached else 1
        prev_cost = logs[i].cost_usd if i in logs else 0.0
        if ans.resolution is None:
            logs[i] = HunkLog(i, "abstain", ans.error or "no answer", prev_cost + ans.cost_usd)
            return None
        if not ans.resolution.can_resolve:
            logs[i] = HunkLog(i, "abstain", f"model declined: {ans.resolution.note}"[:200], prev_cost + ans.cost_usd)
            return None
        logs[i] = HunkLog(i, "llm" if feedback is None else "llm_retry", "", prev_cost + ans.cost_usd)
        return _as_lines(ans.resolution.code, nl)

    for i, k in enumerate(idx):
        h: conflict.Hunk = segs[k]
        size = len(h.ours) + len(h.theirs) + len(h.base or [])
        if not cfg.use_llm or resolver is None:
            logs[i] = HunkLog(i, "abstain", "LLM stage disabled")
            continue
        chars = sum(map(len, h.ours + h.theirs + (h.base or [])))
        if size > cfg.max_hunk_lines or chars > cfg.max_hunk_chars:
            logs[i] = HunkLog(i, "abstain", f"conflict too large for the LLM stage ({size} lines, {chars} chars)")
            continue
        before, after = _context(segs, k, n_before, n_after, cfg.context_chars)
        requests[i] = HunkRequest(
            lang, path, "".join(h.ours), "".join(h.theirs),
            "".join(h.base) if h.base is not None else None, before, after,
        )
        lines = ask(i)
        if lines is not None:
            resolved[i] = lines

    if cfg.use_gate and resolved:
        for attempt in range(cfg.retries + 1):
            cand, ranges = _assemble(segs, idx, resolved)
            g = gate.check(cand, ours_full, theirs_full, lang)
            res.gate_skipped = g.skipped
            if g.ok:
                break
            failing: dict[int, str] = {}
            for issue in g.issues:
                owners = [i for i, (a, b) in ranges.items() if issue.line is not None and a - 2 <= issue.line <= b + 1]
                for i in owners or list(ranges):
                    failing.setdefault(i, issue.message)
            res.gate_rejections += len(failing)
            for i, msg in failing.items():
                prev = "".join(resolved.pop(i))
                if attempt < cfg.retries:
                    lines = ask(i, (prev, msg))
                    if lines is not None:
                        resolved[i] = lines
                else:
                    logs[i] = HunkLog(i, "abstain", f"gate: {msg}"[:200], logs[i].cost_usd)
            if not resolved:
                break
        cand, ranges = _assemble(segs, idx, resolved)
        if resolved and not gate.check(cand, ours_full, theirs_full, lang).ok:
            for i in list(resolved):
                resolved.pop(i)
                logs[i] = HunkLog(i, "abstain", "gate: combined resolutions failed checks", logs[i].cost_usd)

    out: list[str] = []
    line = 0
    for i_seg, s in enumerate(segs):
        if isinstance(s, conflict.Hunk):
            i = idx.index(i_seg)
            chunk = resolved[i] if i in resolved else s.render()
            if i in resolved:
                logs[i].lines = (line + 1, line + len(chunk))
            out.append("".join(chunk))
            line += len(chunk)
        else:
            out.append(s)
            line += len(s.splitlines())
    res.text = "".join(out)
    res.hunks = [logs[i] for i in sorted(logs)]
    res.resolved = len(resolved) == len(idx)
    return res


def _assemble(segs, idx, resolved) -> tuple[str, dict[int, tuple[int, int]]]:
    out: list[str] = []
    ranges: dict[int, tuple[int, int]] = {}
    line = 0
    for i_seg, s in enumerate(segs):
        if isinstance(s, conflict.Hunk):
            i = idx.index(i_seg)
            lines = resolved.get(i, s.ours)
            if i in resolved:
                ranges[i] = (line, line + max(len(lines) - 1, 0))
            out.extend(lines)
            line += len(lines)
        else:
            out.append(s)
            line += len(s.splitlines())
    return "".join(out), ranges
