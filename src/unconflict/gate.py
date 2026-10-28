from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache

from .conflict import marker_lines

_OVERLOADING = {"java", "csharp", "cpp", "typescript", "tsx", "kotlin", "scala", "swift"}

_CONTAINER_TYPES = {
    "class_definition", "class_declaration", "class_specifier", "struct_specifier",
    "interface_declaration", "enum_declaration", "struct_declaration", "record_declaration",
    "impl_item", "trait_item", "module", "class", "object_declaration",
    "namespace_definition", "namespace_declaration", "declaration_list",
}
_IMPORT_HINTS = ("import", "use_declaration", "using_directive", "preproc_include", "require")


@dataclass
class Issue:
    check: str
    message: str
    line: int | None = None


@dataclass
class GateResult:
    ok: bool
    issues: list[Issue] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    def describe(self) -> str:
        return "; ".join(i.message for i in self.issues) or "ok"


@lru_cache(maxsize=None)
def _parser(lang: str):
    try:
        from tree_sitter_language_pack import get_parser

        return get_parser(lang)
    except Exception:
        return None


def parse_tree(text: str, lang: str | None):
    if not lang:
        return None
    p = _parser(lang)
    if p is None:
        return None
    return p.parse(text.encode("utf-8", errors="surrogatepass"))


def error_nodes(tree) -> list:
    out = []
    stack = [tree.root_node]
    while stack:
        n = stack.pop()
        if n.type == "ERROR" or n.is_missing:
            out.append(n)
            continue
        if n.has_error:
            stack.extend(n.children)
    return out


def _name_of(node) -> str | None:
    name = node.child_by_field_name("name")
    if name is not None:
        return name.text.decode("utf-8", "replace")
    named = [c for c in node.named_children if c.type != "comment"]
    if len(named) == 1:
        name = named[0].child_by_field_name("name")
        if name is not None:
            return name.text.decode("utf-8", "replace")
    return None


def _unwrap(node):
    for f in ("declaration", "definition"):
        inner = node.child_by_field_name(f)
        if inner is not None and node.type in ("export_statement", "decorated_definition"):
            return inner
    return node


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def declarations(tree, lang: str) -> Counter:
    keys: Counter = Counter()

    def visit(parent, scope: str, depth: int):
        for raw in parent.named_children:
            if raw.type in ("comment", "ERROR"):
                continue
            node = _unwrap(raw)
            if any(h in node.type for h in _IMPORT_HINTS):
                keys[("import", scope, _norm(node.text.decode("utf-8", "replace")))] += 1
                continue
            name = _name_of(node)
            if name is None:
                if node.type in ("declaration_list", "namespace_body") and depth < 3:
                    visit(node, scope, depth + 1)
                continue
            key_name = name
            if lang in _OVERLOADING:
                params = node.child_by_field_name("parameters")
                if params is not None:
                    key_name += _norm(params.text.decode("utf-8", "replace"))
            keys[(node.type, scope, key_name)] += 1
            if node.type in _CONTAINER_TYPES and depth < 2:
                body = node.child_by_field_name("body")
                if body is not None:
                    visit(body, f"{scope}/{name}", depth + 1)

    visit(tree.root_node, "", 0)
    return keys


def check(candidate: str, ours: str, theirs: str, lang: str | None) -> GateResult:
    issues: list[Issue] = []
    skipped: list[str] = []

    allowed = Counter(marker_lines(ours)) | Counter(marker_lines(theirs))
    extra = Counter(marker_lines(candidate)) - allowed
    if extra:
        for i, line in enumerate(candidate.splitlines()):
            if line in extra or any(line.startswith(m) for m in extra):
                issues.append(Issue("markers", f"leftover conflict marker on line {i + 1}: {line[:20]!r}", i))
                break

    cand_tree = parse_tree(candidate, lang)
    if cand_tree is None:
        skipped.append(f"parse/duplicates (no tree-sitter grammar for {lang or 'unknown language'})")
    else:
        ours_tree, theirs_tree = parse_tree(ours, lang), parse_tree(theirs, lang)
        cand_err = error_nodes(cand_tree)
        side_err = (len(error_nodes(ours_tree)), len(error_nodes(theirs_tree)))
        allowed_err = 0
        if max(side_err) > 0:
            skipped.append(f"parse ({lang} sides already have syntax errors: {side_err[0]}/{side_err[1]})")
        elif len(cand_err) > allowed_err:
            first = cand_err[0]
            line = first.start_point[0]
            snippet = candidate.splitlines()[line].strip()[:60] if line < len(candidate.splitlines()) else ""
            issues.append(
                Issue(
                    "parse",
                    f"does not parse as {lang}: {len(cand_err)} syntax error(s) vs {allowed_err} in the "
                    f"original sides; first near line {line + 1}: {snippet!r}",
                    line,
                )
            )

        cand_decl = declarations(cand_tree, lang)
        side_max = declarations(ours_tree, lang) | declarations(theirs_tree, lang)
        for key, n in cand_decl.items():
            if n > max(side_max.get(key, 0), 1):
                kind, scope, name = key
                where = f" in {scope.lstrip('/')}" if scope else ""
                line = _find_line(candidate, name if kind != "import" else name[:40])
                issues.append(Issue("duplicates", f"duplicate {kind} '{name[:60]}'{where} ({n} copies)", line))

    return GateResult(ok=not issues, issues=issues, skipped=skipped)


def _find_line(text: str, needle: str) -> int | None:
    lines = text.splitlines()
    hits = [i for i, line in enumerate(lines) if needle.split("(")[0] in line]
    return hits[-1] if hits else None
