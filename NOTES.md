# Exploration notes (2026-10-28)

Things I checked before writing code, and where the original project brief had to change.

## Merge-Bench

- Paper: Schesch & Ernst, *Merge-Bench: Resolve Merge Conflicts with Large Language Models*, ICPR 2026.
  Repos: [Merge-Bench](https://github.com/benedikt-schesch/Merge-Bench) (eval, MIT),
  [Merge-Bench-Builder](https://github.com/benedikt-schesch/Merge-Bench-Builder) (dataset construction, MIT),
  [LLMerge](https://github.com/benedikt-schesch/LLMerge) (training).
- **Download:** a single GitHub release asset, `merges.tar.gz` (5.4 MB), at
  `https://github.com/benedikt-schesch/Merge-Bench/releases/download/main/merges.tar.gz`.
  `eval/merge_bench.py --download` fetches it into `data/merge_bench/`.
- **Format:** HuggingFace `datasets` saved with `save_to_disk` (Arrow stream files). One folder per
  language, each with `train`/`test` splits. Only `test` has rows, except `repos_reaper_java_train`
  (a separate training set). Columns: `question` (their full prompt, including the code snippet),
  `answer` (developer's resolved snippet), `prompt` (same as `question`, in chat-message form).
- **Granularity:** **hunk-level snippets.** Each row is one conflict plus the surrounding lines
  (median 18 lines in the prompt, 11 in the answer). About 3% of rows have more than one conflict block.
- **No base.** I checked all 8,050 test rows: **0 have a `|||||||` base section.** The conflicts are
  2-way (`git merge` default style). The rows also have no repository name, file path or full file;
  the only identifier is the commit SHA in the `>>>>>>>` marker line.
- **Size:** 11 test sets = 8,050 rows, 7,887 unique by prompt text. The paper says 7,938; I didn't
  find what the difference is. We use the 11 test splits exactly as `eval.py` loads them
  (`LANGUAGE_DATASETS`, Java = `repos_reaper_java`).

| language | rows | | language | rows |
|---|---:|---|---|---:|
| C | 630 | | Java | 806 |
| C++ | 787 | | JavaScript | 759 |
| C# | 889 | | PHP | 574 |
| Go | 676 | | Python | 761 |
| Ruby | 653 | | Rust | 716 |
| TypeScript | 799 | | **total** | **8,050** |

- **Official metric** (`src/evaluation_metrics.py`, `src/utils.py`): extract the first fenced code
  block from the model's reply, then:
  - *Correct* (exact): `code_block == answer.strip()` (the extracted block is also stripped)
  - *Semantic*: equal after `normalize_code(lang)`, which removes comments and collapses
    whitespace, except in Python/Go/Ruby where only leading/trailing whitespace is stripped
  - *Conflict*: output still has markers ("raising conflict")
  - *Different*: anything else
- **Published numbers** (all languages, `tables/results_table.md`): Gemini 2.5 Pro 47.1% correct /
  52.6% semantic; Claude Opus 4 40.3 / 44.8; o3 Pro 39.2 / 45.1; R1-0528 32.0 / 36.5; Grok 4 27.7 /
  31.7; Qwen3 235B 25.8 / 30.6. No small/cheap OpenAI model is in the table.
- **Selection filter** (`Merge-Bench-Builder/src/metrics_conflict_blocks.py`): a conflict is kept only if
  its whole snippet (conflict block + context) is **≤ 20 lines** (`--max_line_count 20`), the prompt
  fits a token limit, and the resolution size is "coherent". `-keep_trivial_resolution` is computed
  but not used in the selection. So Merge-Bench is a benchmark of *small* conflicts; Track B records
  hunk size so results can also be reported on a Merge-Bench-sized subset.
- **Rebuilding with diff3 isn't practical.** The builder publishes only repo lists
  (`input_data/repos_*.csv`, 1,000 repos per language), not the merges it found. Recovering the
  base would mean re-cloning and replaying ~11k repos.

### Consequence: two evaluation tracks
- **Track A (official Merge-Bench snippets, 2-way):** mergiraf can't run (it needs a base; I
  confirmed it refuses 2-way input) and the gate can only work at snippet level. So Track A compares
  git-default vs LLM-only vs LLM+gate, with mergiraf marked N/A.
- **Track B (self-mined diff3 conflicts with full files):** all four systems, including the full
  hybrid. Mined by replaying merge commits from repos on the same Merge-Bench-Builder lists, plus a
  few active repos so we can split by the model's training cutoff.

## mergiraf

- Version 0.20.0 (Homebrew formula `mergiraf`, crates.io `mergiraf`). GPL-3.0.
- **Install on this machine:** Codeberg (release binaries) and ghcr.io (Homebrew bottles) don't
  resolve from this network, so `brew install` and binary downloads fail here.
  `cargo install --locked mergiraf` works because crates.io is reachable. The built binary is in
  `~/.local/bin/mergiraf`.
- Languages: 50+ including all 11 Merge-Bench languages (`mergiraf languages`).
- CLI: `mergiraf merge BASE LEFT RIGHT [-o OUT] [-p PATH_FOR_LANG] [-x/-s/-y labels] [-t timeout_ms]`.
  Exit 0 = clean, 1 = conflicts left in the output. `mergiraf solve FILE` resolves a file with
  **diff3** markers in place; on 2-way markers it prints "Cannot solve conflicts in diff2 style" and
  gives up. Git driver: `mergiraf merge --git %O %A %B -s %S -x %X -y %Y -p %P -l %L`.
- Toy tests (also in `tests/fixtures/`):
  - It resolves independent additions (imports, class members in Java/TS) and changes to different
    sub-expressions of the same line (e.g. a parameter added on one side and a literal changed on
    the other), which git can't.
  - It leaves real same-token clashes conflicted, and keeps the `|||||||` base section, which is
    what stage 2 needs.
  - It also leaves conflicted the case where both sides append *different* top-level functions at
    the same spot in a Python file (statement order matters in Python modules).
  - **Formatting artifact:** its sub-expression merges sometimes produce a doubled space
    (`return  "hello " + name + punct`). That's semantically fine but fails exact match, so we report
    whitespace-normalized match next to exact match.
  - Its leftover conflicts don't line up 1:1 with git's hunks (often smaller). Scoring therefore
    finds each git hunk's region by context matching, not by hunk index.

## OpenAI model and price

- Pricing page (https://developers.openai.com/api/docs/pricing), checked 2026-10-28, standard tier,
  USD per 1M tokens (input / cached input / output):
  `gpt-6-luna` 0.10 / 0.01 / 0.50 · `gpt-5-nano` 0.05 / 0.005 / 0.40 · `gpt-4.1-nano` 0.10 / 0.025 / 0.40
  · `gpt-5.4-nano` 0.20 / 0.02 / 1.25. Batch/Flex is 50% off but asynchronous; not used.
- **Pick: `gpt-6-luna`.** Current generation, structured outputs supported, $0.10/$0.50 as the brief
  said. `gpt-5-nano` is cheaper on paper but an older generation and can't turn reasoning fully off.
- `gpt-6-luna` is a **reasoning model**: `reasoning.effort` none/low/medium (default)/high/xhigh/max,
  and reasoning tokens bill as output. We call it with `reasoning_effort="none"`.
- Knowledge cutoff **2026-05-18**, so conflicts merged after that date can't have been memorized.
- The key in `.env` can access `gpt-6-luna`, `gpt-5-nano`, `gpt-4.1-nano` (checked with the free
  `GET /v1/models/{id}`, no tokens used).

## Virginia Tech study

arXiv 2607.27674 (Bowen Shen, July 2026), *Can Large Language Models Resolve Real Java Merge
Conflicts? An Evaluation with a Calibrated LLM-as-Judge*. ConflictBench, Java only. Traditional
tools abstain on 20–90% of conflicts; the calibrated LLM judge accepted 4 of the 5 resolutions that
failed a deterministic structural check. mergiraf wasn't among the tools tested.

## Environment notes

- tree-sitter grammars come from `tree-sitter-language-pack` 1.x, which **downloads each grammar on
  first use** into `~/Library/Caches/tree-sitter-language-pack/`. `unconflict warmup` prefetches
  them. If a grammar can't be loaded (offline), the gate still checks markers and reports that the
  parse/duplicate checks were skipped.
- `gpt-6-luna` + LangChain: `ChatOpenAI(model, reasoning_effort="none", max_tokens=N)
  .with_structured_output(Resolution, method="json_schema", strict=True, include_raw=True)`.
  `include_raw` gives `usage_metadata` for the budget ledger.
