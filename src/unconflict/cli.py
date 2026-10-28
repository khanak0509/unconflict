from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from .budget import Budget
from .cache import ResponseCache
from .config import Config
from .llm import LLMResolver
from .pipeline import resolve_sides, resolve_text

DRIVER_CMD = "unconflict driver %O %A %B %P -s %S -x %X -y %Y"
DEFAULT_PATTERNS = ["*.py", "*.js", "*.jsx", "*.mjs", "*.ts", "*.tsx", "*.java", "*.go", "*.rs",
                    "*.c", "*.h", "*.cpp", "*.hpp", "*.cc", "*.cs", "*.php", "*.rb"]


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def _make(args) -> tuple[Config, Budget, LLMResolver | None]:
    cfg = Config()
    if getattr(args, "model", None):
        cfg.model = args.model
    if getattr(args, "context", None) is not None:
        cfg.context_lines = args.context
    cfg.use_structured = not getattr(args, "no_structured", False)
    cfg.use_llm = not getattr(args, "no_llm", False)
    if getattr(args, "max_spend", None) is not None:
        cfg.budget_usd = min(cfg.budget_usd, args.max_spend)
    budget = Budget(cfg.budget_usd)
    resolver = None
    if cfg.use_llm:
        if os.environ.get("OPENAI_API_KEY"):
            resolver = LLMResolver(cfg, budget, ResponseCache())
        else:
            _err("unconflict: OPENAI_API_KEY not set, skipping LLM stage")
    return cfg, budget, resolver


def cmd_resolve(args) -> int:
    src = Path(args.file)
    text = src.read_text(encoding="utf-8", errors="surrogateescape")
    cfg, budget, resolver = _make(args)
    res = resolve_text(text, str(src), cfg, resolver)
    if args.stdout:
        sys.stdout.write(res.text)
        dest = "stdout"
    else:
        out = src if args.in_place else Path(args.output) if args.output else src.with_name(src.name + ".resolved")
        out.write_text(res.text, encoding="utf-8", errors="surrogateescape", newline="")
        dest = str(out)
    if not args.quiet:
        _err(res.summary())
        _err(f"wrote: {dest}")
        if resolver is not None:
            _err(budget.report())
    return 0 if res.resolved else 1


def cmd_driver(args) -> int:
    ours_path = Path(args.ours)
    read = lambda p: Path(p).read_text(encoding="utf-8", errors="surrogateescape")
    labels = (args.x or "ours", args.s or "base", args.y or "theirs")
    try:
        base, ours, theirs = read(args.base), read(args.ours), read(args.theirs)
        cfg, budget, resolver = _make(args)
        res = resolve_sides(base, ours, theirs, args.path, cfg, resolver, labels)
        ours_path.write_text(res.text, encoding="utf-8", errors="surrogateescape", newline="")
        _err(f"unconflict: {args.path}\n" + "\n".join("  " + line for line in res.summary().splitlines()))
        if resolver is not None and res.llm_calls:
            _err("  " + budget.report())
        return 0 if res.resolved else 1
    except Exception as e:
        _err(f"unconflict: error: {e}; using git merge-file")
        proc = subprocess.run(["git", "merge-file", "--diff3", "-L", labels[0], "-L", labels[1], "-L", labels[2],
                               args.ours, args.base, args.theirs])
        return 0 if proc.returncode == 0 else 1


def cmd_install(args) -> int:
    scope = ["--global"] if args.global_ else []
    cmds = [
        ["git", "config", *scope, "merge.unconflict.name", "unconflict: mergiraf + LLM + gate"],
        ["git", "config", *scope, "merge.unconflict.driver", DRIVER_CMD],
    ]
    patterns = args.patterns or DEFAULT_PATTERNS
    if args.global_:
        attr = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "git" / "attributes"
    else:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        if top.returncode != 0:
            _err("not a git repository (use --global)")
            return 2
        attr = Path(top.stdout.strip()) / ".gitattributes"
    lines = [f"{p} merge=unconflict" for p in patterns]
    for c in cmds:
        print(" ".join(c[:-1]) + f" '{c[-1]}'")
    for line in lines:
        print(f"{attr}: {line}")
    if args.dry_run:
        return 0
    for c in cmds:
        subprocess.run(c, check=True)
    existing = attr.read_text().splitlines() if attr.exists() else []
    attr.parent.mkdir(parents=True, exist_ok=True)
    with open(attr, "a") as fh:
        for line in lines:
            if line not in existing:
                fh.write(line + "\n")
    return 0


def cmd_spend(args) -> int:
    cfg = Config()
    b = Budget(cfg.budget_usd)
    s = b.summary()
    if args.json:
        print(json.dumps(s, indent=2))
    else:
        print(f"ledger: {b.path}")
        print(f"total: ${s['total_usd']:.4f} of ${cfg.budget_usd:.2f} cap over {s['calls']} paid call(s)")
        print(f"tokens: {s['input_tokens']} in ({s.get('cached_input_tokens', 0)} cached), "
              f"{s['output_tokens']} out ({s.get('reasoning_tokens', 0)} reasoning)")
        for m, v in s.get("by_model", {}).items():
            print(f"  {m}: ${v['usd']:.4f} / {v['calls']} calls")
    return 0


def cmd_warmup(args) -> int:
    from .gate import _parser

    for lang in args.languages or ["python", "javascript", "typescript", "tsx", "java", "go", "rust",
                                   "c", "cpp", "csharp", "php", "ruby"]:
        print(f"{lang}: {'ok' if _parser(lang) is not None else 'unavailable'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="unconflict", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--no-llm", action="store_true", help="structured merge only, no paid calls")
        sp.add_argument("--no-structured", action="store_true", help="skip mergiraf")
        sp.add_argument("--model", help="OpenAI model (default: $UNCONFLICT_MODEL or gpt-6-luna)")
        sp.add_argument("--context", type=int, help="lines of context sent per conflict (default 60)")
        sp.add_argument("--max-spend", type=float, help="lower the USD spending cap for this run")

    r = sub.add_parser("resolve", help="resolve a file that contains conflict markers")
    r.add_argument("file")
    g = r.add_mutually_exclusive_group()
    g.add_argument("-o", "--output", help="write here (default: FILE.resolved)")
    g.add_argument("--in-place", action="store_true", help="overwrite FILE")
    g.add_argument("--stdout", action="store_true", help="print the result")
    r.add_argument("-q", "--quiet", action="store_true")
    common(r)
    r.set_defaults(func=cmd_resolve)

    d = sub.add_parser("driver", help="git merge driver entry point (see `unconflict install`)")
    d.add_argument("base")
    d.add_argument("ours")
    d.add_argument("theirs")
    d.add_argument("path")
    d.add_argument("-s")
    d.add_argument("-x")
    d.add_argument("-y")
    common(d)
    d.set_defaults(func=cmd_driver)

    i = sub.add_parser("install", help="register the merge driver with git")
    i.add_argument("--global", dest="global_", action="store_true", help="for all repos (~/.gitconfig)")
    i.add_argument("--patterns", nargs="*", help="file patterns (default: common source extensions)")
    i.add_argument("--dry-run", action="store_true")
    i.set_defaults(func=cmd_install)

    s = sub.add_parser("spend", help="show total LLM spend")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_spend)

    w = sub.add_parser("warmup", help="download tree-sitter grammars used by the gate")
    w.add_argument("languages", nargs="*")
    w.set_defaults(func=cmd_warmup)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
