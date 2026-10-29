# Methodology

How the numbers in the README were produced, and how to reproduce them. Every run writes
`results/<run_id>/config.json` (model, prices, seed, sample, date, spend, exact command),
`per_hunk.jsonl` (one scored row per conflict and system) and `summary.md`/`summary.json`.

## Systems

| system | what it does |
|---|---|
| `git_default` | `git merge-file --diff3`: the conflict is always left for the human. A floor. |
| `mergiraf_only` | `mergiraf merge base ours theirs` (0.20.0). Whatever it leaves conflicted stays conflicted. |
| `llm_only` | Every conflict hunk git leaves goes to the LLM. No structured stage, no gate, no retry. |
| `llm_gate` | Same as `llm_only`, plus the deterministic gate with one retry and abstain (Track A). |
| `hybrid` | mergiraf, then the LLM on what mergiraf leaves, then the gate with one retry and abstain. |

All LLM systems use the same model, prompt, output schema and context cap:

- model `gpt-6-luna`, `reasoning_effort="none"`, via LangChain `ChatOpenAI(...).with_structured_output(Resolution, method="json_schema", strict=True)`
- output schema: `code` (lines replacing the conflict block), `can_resolve` (bool), `note`
- per hunk the prompt holds ours / base / theirs (base marked "not available" for 2-way conflicts),
  the language, the file name, and up to 60 lines of surrounding context (30 before, 30 after),
  stopping at neighbouring conflicts. Prompt text is in `src/unconflict/llm.py`.
- output-token cap per call: about (hunk characters / 3 + 300), clamped to 256–4096
- context is also capped at 4,000 characters per side, dropping the lines farthest from the conflict
- hunks over 300 lines or 12,000 characters (ours + base + theirs) aren't sent; they count as abstentions
- the character caps were added after the Track B pilot: 7 calls on minified/generated files had
  ~70–100k input tokens each and made up 20% of all spend at that point

`llm_only` and the first call of `llm_gate`/`hybrid` on the same hunk send byte-identical requests,
so the on-disk cache serves the second one for free. Cost columns therefore report **nominal**
cost: the token usage of every call a system relied on, priced as if uncached. The actual money
spent is in `config.json` (`spent_this_run_usd`) and in the ledger (`unconflict spend`).

## The gate (stage 3, no LLM)

Applied to the whole candidate file (Track B) or the whole snippet (Track A), with any conflict
still left shown as its `ours` side. Each check is relative to the two input sides, so problems
the merge didn't introduce aren't held against it:

1. **markers:** no conflict-marker line that wasn't already present in ours/theirs
2. **parse:** the candidate parses with tree-sitter (no ERROR/MISSING nodes). This check runs only
   when ours and theirs both parse cleanly; if the inputs are already broken (a snippet cut out of a
   file, or a grammar gap), it's skipped and logged
3. **duplicates:** no import, top-level declaration or class member (keyed by kind + name, plus
   parameter list in languages with overloading) occurs more often than in either side

A failure is attributed to the LLM-resolved hunk whose lines contain it (±2 lines); unattributable
failures are blamed on every LLM hunk in the file. Failing hunks are retried once with the error
message appended to the conversation; if they still fail, they're abstained (the original conflict
is put back). mergiraf's own output is also gated: if it fails, the system falls back to git's
conflicts for that file.

**Change made after the pilot (disclosed):** the first version of the parse check compared error
*counts* ("no more errors than the cleaner side"), so it also ran on inputs that didn't parse. On
the Track A pilot (275 snippets, run `pilot-A`) it fired on 10 snippets. In 5 of them it
rejected an LLM answer that exactly matched the developer's, and abstained; in 1 it withheld a wrong
answer. Merge-Bench snippets are fragments, so tree-sitter already reports errors on both sides,
and any edit shifts the count. The check was changed to the rule above before the full runs. The
full runs include the pilot's items, and `results/pilot-A/` keeps the first version's numbers.

## Scoring

Exact and semantic match use **Merge-Bench's own code**, copied into `eval/metrics.py` (MIT):

- **exact:** `pred.strip() == gold.strip()`
- **semantic:** equal after Merge-Bench's `normalize_code`, which removes comments and collapses
  whitespace (except in Python, Go and Ruby, where only leading/trailing whitespace is stripped)
- **whitespace-normalized:** ours; every run of whitespace collapsed to one space, all languages
- **abstain:** the system left the conflict (markers in its output for that conflict)
- **precision:** exact (or semantic) matches ÷ conflicts the system did *not* abstain on
- the order is Merge-Bench's: exact, then semantic, then conflict, then different

Merge-Bench's "invalid markdown" category doesn't apply: our tool returns code, not chat text.

## Track A: official Merge-Bench snippets

- Data: the 11 test splits from the `merges.tar.gz` release, loaded exactly as Merge-Bench's
  `eval.py` maps languages (`eval/merge_bench.py`). 8,050 rows, 7,887 unique.
- Sample: duplicate prompts dropped per language, then a seeded shuffle per language
  (`random.Random(f"{seed}:{language}")`), first N per language. Seed 0 unless stated.
- Unit: one snippet = one row. The system's output snippet is compared with the row's `answer`.
- **Truncated next conflict:** 307 snippets end in a second conflict cut off mid-way (a lone
  `<<<<<<<` line). The gold answers keep that line verbatim (308 of the 312 malformed rows), so the
  eval treats it as context: it is split off before resolving and appended back unchanged. 5 rows
  with nested markers are excluded and counted in `config.json`.
- mergiraf and `hybrid` are **not applicable**: the snippets are 2-way (no base) and aren't full
  files. I confirmed mergiraf refuses diff2-style input.
- **Data quirks** (affect every system equally): a few gold answers contain the conflict markers
  (the developer committed them), so leaving the conflict counts as exact; and when a conflict sits
  inside a block comment, `normalize_code` deletes the comment with the markers, so an unresolved
  conflict can score as semantic. This is why `git_default` isn't exactly 0%.
- **Comparability with published Merge-Bench numbers:** same data and same metric code, but a
  different prompt and output format (we return only the replacement for the conflict and splice it
  back; the paper's models rewrite the whole snippet as markdown), and a sample rather than the full
  set. Our numbers sit next to theirs as context, not as a head-to-head result.

## Track B: mined conflicts with full files and a base

- Repos: `eval/select_repos.py` walks the Merge-Bench-Builder repo lists (`input_data/*.csv`) for
  Python, Java, JavaScript, TypeScript, Go and Rust in published order. It skips archived repos,
  repos over 150 MB (disk space on the machine used), non-code repos (awesome-lists, books,
  tutorials, roadmaps) and renamed duplicates, and takes the first 5 per language.
- Mining (`eval/mine.py`, free): newest 3,000 merge commits per repo (all branches). It skips
  octopus merges and criss-cross merges (more than one merge base), replays each merge with
  `git merge-tree`, and keeps conflicted files in the target language where base, ours, theirs and
  the merge commit's version all exist (no add/delete/rename conflicts), each under 300 KB. It
  keeps at most 40 files per repo and drops duplicate (path, base, ours, theirs) files.
- Ground truth per git conflict hunk: the 5 lines before and after the hunk (from git's own diff3
  output) must occur exactly once in the developer's committed file; the lines between them are the
  developer's resolution. It drops hunks whose context isn't unique, hunks directly adjacent to
  another hunk, and hunks where the developer committed conflict markers.
- Scoring: each system produces a whole file, and each hunk's region in it is found with the same
  context. If the context can't be found (e.g. a system rewrote the neighbouring lines), the hunk is
  scored `unlocatable`: wrong, or abstained if that file still has conflicts.
- **Stage attribution** (hybrid): a hunk counts as handled by mergiraf if its region is
  conflict-free after stage 1; otherwise by the stage of the leftover conflict(s) inside it (LLM,
  LLM after retry, or abstain).
- **Merge-Bench-sized subset:** hunks whose conflict block plus context is ≤ 20 lines, the filter
  Merge-Bench used to build its dataset.
- **Contamination split:** merges committed after the model's knowledge cutoff (2026-05-18) versus
  before. A post-cutoff merge date makes memorization unlikely, but not impossible: the same
  resolution could have been public earlier on another branch.
- **Excluded: files with more than 20 git conflict hunks** (3 files: two generated API files in
  dify with 337 and 39 hunks, and one uv file with 24). This was decided after the first Track B
  pilot drew the 337-hunk generated file, which would have contributed more scored hunks than all
  other TypeScript files combined. That pilot run was stopped and isn't reported.
- Sample (pilot only): files shuffled with a seeded RNG per language, then added while they fit
  the language's hunk quota. Full runs use every remaining file.

## Budget

`src/unconflict/budget.py`: before every paid call it reserves the worst case (prompt characters ÷ 3
as tokens at the input price, plus the full output cap at the output price) and refuses the call if
ledger + pending reservations + this reservation would pass the cap. After the call it records the
real `usage_metadata` (input, cached input, output including reasoning tokens) at the prices in
`src/unconflict/config.py`. The ledger is `~/.unconflict/spend.json` with a per-call log in
`spend_log.jsonl`. Each eval run also takes `--max-spend`, a cap on new spend for that run. Cache:
`~/.unconflict/cache/`, keyed by SHA-256 of (model, reasoning effort, max tokens, messages, schema).

## Limitations and caveats

- **One model, one sample per conflict.** I didn't test other models or repeated runs. Re-running reproduces my numbers exactly (the cache serves the stored answers), but a new uncached call can give a different answer.
- **Exact match to what the developer committed is a strict, imperfect target.** Some developers made unrelated edits in the merge, kept conflict markers, or picked one side for reasons the code doesn't show. A different but correct merge counts as wrong. Nothing here builds the code or runs tests.
- **The mined set is modest:** 28 repos (30 queried; 2 had no usable conflicts), at most 40 files each, repos under 150 MB. A few repos dominate some languages, e.g. dify in TypeScript and uv/sway/tauri in Rust.
- **Some conflicts can't be fully scored.** When mergiraf reformats the lines around a conflict, scoring can't line up 0.7% of hunks in files it fully resolved, and these count as wrong. It also leaves 6.7% of the hybrid's hunks without a stage label. mergiraf's sub-expression merges sometimes leave a doubled space, which costs exact (not semantic) matches.
- **The gate catches broken code, not wrong code.** A merge that parses but picks the wrong value passes. That's why the merge driver stops for review after LLM resolutions by default.
- **Two design changes were made after the pilot.** The parse check now runs only when the inputs parse, and context is capped by characters. Both are documented in [METHODOLOGY.md](METHODOLOGY.md); the full runs include the pilot's conflicts.
- **Your code is sent to OpenAI** for stage 2 (only the conflicting hunk and up to 60 lines around it). Use `--no-llm` or unset the key when that's not acceptable.
- tree-sitter grammars are downloaded on first use (`unconflict warmup` prefetches them). Offline, the gate still checks markers but skips parsing.

## Reproduce

```bash
uv sync
cargo install --locked mergiraf          # or: brew install mergiraf
python eval/merge_bench.py --download
python eval/select_repos.py --n 5        # prints the repo list per language (the list used is eval/trackB_repos.txt)
python eval/mine.py --language python --repos <repos...> --max-files 40 --max-merges 3000   # per language
python eval/run.py --track A --per-language <N> --seed 0 --max-spend <USD>
python eval/run.py --track B --per-language <N> --seed 0 --max-spend <USD>
```

Mined data changes as the upstream repos gain new merges, so a re-mine later will not give
byte-identical data. The JSONL files used for the reported runs are listed with their sizes and
SHA-256 in the run's `config.json`.
