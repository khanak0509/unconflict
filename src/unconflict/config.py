from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PRICES: dict[str, tuple[float, float, float]] = {
    "gpt-6-luna": (0.10, 0.01, 0.50),
    "gpt-5-nano": (0.05, 0.005, 0.40),
    "gpt-4.1-nano": (0.10, 0.025, 0.40),
    "gpt-5.4-nano": (0.20, 0.02, 1.25),
}

DEFAULT_MODEL = "gpt-6-luna"
DEFAULT_REASONING_EFFORT = "none"
DEFAULT_BUDGET_USD = 2.50


def home() -> Path:
    return Path(os.environ.get("UNCONFLICT_HOME", Path.home() / ".unconflict"))


@dataclass
class Config:
    model: str = field(default_factory=lambda: os.environ.get("UNCONFLICT_MODEL", DEFAULT_MODEL))
    reasoning_effort: str | None = DEFAULT_REASONING_EFFORT
    budget_usd: float = field(
        default_factory=lambda: float(os.environ.get("UNCONFLICT_BUDGET_USD", DEFAULT_BUDGET_USD))
    )
    context_lines: int = 60
    context_chars: int = 4000
    max_hunk_lines: int = 300
    max_hunk_chars: int = 12000
    use_structured: bool = True
    use_llm: bool = True
    use_gate: bool = True
    retries: int = 1
    mergiraf_timeout_s: float = 30.0
    llm_timeout_s: float = 60.0


EXT_TO_LANG = {
    ".py": "python", ".pyi": "python",
    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".mts": "typescript", ".cts": "typescript", ".tsx": "tsx",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".c": "c", ".h": "c",
    ".cc": "cpp", ".cpp": "cpp", ".cxx": "cpp", ".hpp": "cpp", ".hh": "cpp", ".hxx": "cpp",
    ".cs": "csharp",
    ".php": "php",
    ".rb": "ruby",
    ".kt": "kotlin", ".kts": "kotlin",
    ".scala": "scala",
    ".swift": "swift",
}

BENCH_LANG = {
    "python": ("python", ".py"),
    "javascript": ("javascript", ".js"),
    "typescript": ("typescript", ".ts"),
    "java": ("java", ".java"),
    "go": ("go", ".go"),
    "rust": ("rust", ".rs"),
    "c": ("c", ".c"),
    "cpp": ("cpp", ".cpp"),
    "csharp": ("csharp", ".cs"),
    "php": ("php", ".php"),
    "ruby": ("ruby", ".rb"),
}


def language_for_path(path: str | os.PathLike | None) -> str | None:
    if not path:
        return None
    return EXT_TO_LANG.get(Path(path).suffix.lower())
