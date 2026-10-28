# unconflict

Resolves git merge conflicts in three stages. A syntax-aware merge ([mergiraf](https://mergiraf.org)) goes first. A small LLM handles only what mergiraf leaves, and a deterministic check rejects broken output. When unsure, it leaves the conflict for you instead of guessing.

**Result.** I tested 1,131 real conflicts mined from 28 open-source repos in 6 languages. The full pipeline matched the developer's actual resolution exactly **43.7%** of the time. The same LLM on its own scored **40.6%**: a gain of +3.1 points (95% CI +0.2 to +5.9), at **25% lower cost** ($0.00013 vs $0.00018 per conflict). The pipeline abstained on 9.5% of conflicts. mergiraf alone resolved 42.6% of them and was exactly right on 23.8%. On the official [Merge-Bench](https://github.com/benedikt-schesch/Merge-Bench) test set (7,882 conflicts, 11 languages), the LLM I used (`gpt-6-luna`) scored 42.6% exact / 50.7% semantic. That full run cost $0.48. All numbers come from runs saved in `results/`. The whole project cost $0.82 in API calls.

## How it works

```
 conflicted file (base, ours, theirs)
        │
        ▼
 ┌──────────────────────┐  resolved hunks are done, $0
 │ 1. mergiraf          │───────────────────────────────┐
 │    structured merge  │                               │
 └──────────┬───────────┘                               │
            │ hunks it can't solve                      │
            ▼                                           ▼
 ┌──────────────────────┐        ┌──────────────────────────────────┐
 │ 2. LLM, one hunk at  │───────▶│ 3. gate (plain code, no LLM)     │──▶ resolved file
 │    a time: base/ours/│◀───────│    no leftover markers           │
 │    theirs + context  │ retry  │    still parses (tree-sitter)    │
 └──────────────────────┘ once   │    no duplicated declarations    │
                                 └───────────────┬──────────────────┘
                                                 │ fails twice
                                                 ▼
                                 conflict left for you, as git would
```

- **Stage 1.** `mergiraf merge` on the three versions. It merges at the syntax-tree level, so changes that git sees as overlapping lines (two imports added at the same spot, two different class members, edits to different parts of one expression) merge cleanly.
- **Stage 2.** Each conflict that's left goes to the LLM through LangChain (`ChatOpenAI` with structured output). The prompt holds the three sides, up to 60 lines of context and the language. The model returns the replacement code and a flag for "can't resolve safely". The default model is `gpt-6-luna` with reasoning off, at about $0.0001 per conflict.
- **Stage 3.** The gate checks the whole file: no conflict markers, still parses (when the inputs parsed), and no import, function or class member duplicated. On failure the LLM gets one retry with the error message. If that fails too, the hunk goes back to you as a normal conflict. mergiraf's own output goes through the same gate.

## Install

```bash
# 1. mergiraf (stage 1). Optional: without it, every conflict goes to the LLM
brew install mergiraf            # or: cargo install --locked mergiraf

# 2. unconflict
git clone <this repo> && cd unconflict
uv tool install .                # or: pip install .

# 3. OpenAI key for stage 2 (without it, stage 2 is skipped and conflicts are left for you)
export OPENAI_API_KEY=sk-...
```

### Use as a git merge driver

```bash
cd your-repo
unconflict install               # sets merge.unconflict.driver and adds lines to .gitattributes
# or for every repo: unconflict install --global
```

That is equivalent to:

```bash
git config merge.unconflict.name "unconflict: mergiraf + LLM + gate"
git config merge.unconflict.driver "unconflict driver %O %A %B %P -s %S -x %X -y %Y"
echo "*.py merge=unconflict" >> .gitattributes     # one line per file type
```

After that, `git merge` and `git rebase` call it automatically. Each file it touches gets a short log on stderr: which stage handled each conflict, and the spend. **A file the driver fully resolves counts as merged, so git will commit it.** To review LLM resolutions before they're committed, merge with `git merge --no-commit` and look at `git diff --cached`.

### Use on a file that already has conflict markers

```bash
unconflict resolve src/app.py               # writes src/app.py.resolved, never touches the original
unconflict resolve src/app.py --stdout
unconflict resolve src/app.py --in-place
unconflict resolve src/app.py --no-llm      # mergiraf only, free
```

Stage 1 needs the base version, so set `git config merge.conflictStyle diff3`. With 2-way markers it skips straight to the LLM.

### Spending cap

Every paid call goes through a hard budget guard. It reserves the worst-case cost before the call and refuses if the total would pass the cap (default $2.50; set `UNCONFLICT_BUDGET_USD`, or `--max-spend` per run). Spend is kept in `~/.unconflict/spend.json`. Responses are cached on disk, so re-running the same conflict is free. Check with `unconflict spend`.

## Results

Two test sets, because the official benchmark can't exercise the full pipeline (see [NOTES.md](NOTES.md)):

- **Track A: Merge-Bench.** The official test set: 11 languages, ~18-line snippets. The snippets have **no base version and no full file**, so mergiraf can't run and the parse check has nothing to check. This tests the LLM stage only.
- **Track B: mined conflicts.** 1,131 conflict hunks in 725 files. I replayed merge commits from 28 repos, taken from Merge-Bench's own repo lists, with full files and the base version. Ground truth is the file the developer committed. This tests all four systems.

"Exact" and "semantic" use Merge-Bench's own scoring code. Semantic ignores comments and, outside Python/Go/Ruby, whitespace. Precision is the accuracy on the conflicts a system didn't abstain on.

### Track B: full pipeline, 1,131 conflicts (`results/full-B`)

| system | exact | semantic | abstains | precision (exact) | cost per conflict |
|---|---:|---:|---:|---:|---:|
| git (default) | 0% | 0% | 100% | – | $0 |
| mergiraf only | 23.8% | 25.6% | 57.4% | 55.8% | $0 |
| LLM only | 40.6% | 43.9% | 4.5% | 42.5% | $0.00018 |
| **hybrid** (mergiraf → LLM → gate) | **43.7%** | **47.3%** | 9.5% | **48.3%** | **$0.00013** |

Who handled each conflict in the hybrid: mergiraf 40.6%, LLM 43.2%, LLM after a gate retry 1.3%, left for the human 8.1%. For the other 6.7%, mergiraf rewrote the surrounding lines, so the stage couldn't be attributed.

By language (exact match):

| | Python | JavaScript | TypeScript | Java | Go | Rust |
|---|---:|---:|---:|---:|---:|---:|
| conflicts | 210 | 215 | 176 | 150 | 116 | 264 |
| mergiraf only | 25.2% | 26.5% | 26.1% | 28.0% | 31.0% | 13.3% |
| LLM only | 56.7% | 34.9% | 37.5% | 32.0% | 38.8% | 40.2% |
| hybrid | 65.7% | 43.3% | 35.8% | 36.0% | 41.4% | 37.1% |

What the numbers say, and what they don't:

- **The gain comes from stage 1.** On the 459 conflicts the hybrid left to mergiraf, mergiraf was exactly right 261 times; the LLM, given the same conflicts, 191. Where the hybrid did use the LLM, it scored the same as LLM-only (219 vs 223).
- **mergiraf is precise but answers rarely.** When it answers it's right 56–60% of the time, the best precision of the three. But it leaves 57% of conflicts alone. This matches the Virginia Tech study's finding for structured tools on Java.
- **Abstaining mostly withholds bad merges.** The hybrid left 108 conflicts to the human. On those, LLM-only was wrong (not abstaining) 49 times and exactly right 23 times.
- **The gate worked on full files.** It rejected 199 LLM outputs in 41 files. It also rejected mergiraf's own output in 17 of the 725 files (9 for parse errors, 8 for duplicated declarations). In those files the fallback (git's conflicts plus the LLM) matched 9 hunks exactly; mergiraf's rejected output matched 7.
- **The gain isn't universal.** It's within noise on conflicts small enough for Merge-Bench (≤ 20 lines with context: +0.2 points, CI −4.1 to +4.4) and on merges after the model's training cutoff (+0.5, CI −4.2 to +5.4). The hybrid was behind LLM-only in TypeScript and Rust.

### Track A: official Merge-Bench, 7,882 conflicts (`results/full-A`)

| system | exact | semantic | abstains | precision (semantic) | total cost |
|---|---:|---:|---:|---:|---:|
| git (default) | 1.0% | 2.2% | 100% | – | $0 |
| `gpt-6-luna`, LLM only | 42.6% | 50.7% | 4.2% | 52.8% | $0.48 |
| `gpt-6-luna` + gate | 42.6% | 50.7% | 4.3% | 52.9% | $0.48 |

By language, exact / semantic: C 64.7 / 70.1 · Python 51.4 / 54.2 · PHP 49.2 / 59.0 · Java 44.8 / 59.2 · JavaScript 44.3 / 55.3 · Rust 40.3 / 45.5 · C++ 39.7 / 51.6 · Ruby 35.2 / 37.9 · C# 35.1 / 53.1 · Go 34.9 / 35.8 · TypeScript 33.7 / 38.2.

The gate does nothing here: these snippets are fragments, so there's no whole file to parse. git's 1.0% "exact" is a data quirk: some developers committed the conflict markers.

**Compared with the published Merge-Bench table** (Gemini 2.5 Pro 47.1% / 52.6%, Claude Opus 4 40.3% / 44.8%, o3 Pro 39.2% / 45.1%), the numbers are **not directly comparable**. The data (deduplicated: 7,882 of 8,050 rows) and the scoring code are the same, but the prompt and output format differ. My tool returns only the replacement for the conflict; the paper's setup has the model rewrite the whole snippet in markdown. So the comparison shows a cheap model in the same range, not a ranking.

### Memorization check

All Merge-Bench conflicts and most mined ones are public, so the model may have seen the resolutions. 396 of the mined conflicts were merged after `gpt-6-luna`'s training cutoff (2026-05-18). There, LLM-only scored 37.1% vs 42.4% before. But within single languages the difference goes both ways (JavaScript −7 points, TypeScript −12, Rust +6). The post-cutoff conflicts also come from different repos. I don't see consistent evidence of memorization, and the data can't rule it out.

### Cost

Total OpenAI spend for the whole project, including development, smoke test, pilot and both full runs: **$0.82** (10,071 calls, `gpt-6-luna` at $0.10 / $0.50 per million input/output tokens). The median call is 364 input and 45 output tokens.

## Limitations

- **One model, one sample per conflict.** I didn't test other models or repeated runs. Re-running reproduces my numbers exactly (the cache serves the stored answers), but a new uncached call can give a different answer.
- **Exact match to what the developer committed is a strict, imperfect target.** Some developers made unrelated edits in the merge, kept conflict markers, or picked one side for reasons the code doesn't show. A different but correct merge counts as wrong. Nothing here builds the code or runs tests.
- **The mined set is modest:** 28 repos (30 queried; 2 had no usable conflicts), at most 40 files each, repos under 150 MB. A few repos dominate some languages, e.g. dify in TypeScript and uv/sway/tauri in Rust.
- **Some conflicts can't be fully scored.** When mergiraf reformats the lines around a conflict, scoring can't line up 0.7% of hunks in files it fully resolved, and these count as wrong. It also leaves 6.7% of the hybrid's hunks without a stage label. mergiraf's sub-expression merges sometimes leave a doubled space, which costs exact (not semantic) matches.
- **The gate catches broken code, not wrong code.** A merge that parses but picks the wrong value passes.
- **Two design changes were made after the pilot.** The parse check now runs only when the inputs parse, and context is capped by characters. Both are documented in [METHODOLOGY.md](METHODOLOGY.md); the full runs include the pilot's conflicts.
- **Your code is sent to OpenAI** for stage 2 (only the conflicting hunk and up to 60 lines around it). Use `--no-llm` or unset the key when that's not acceptable.
- tree-sitter grammars are downloaded on first use (`unconflict warmup` prefetches them). Offline, the gate still checks markers but skips parsing.

## Reproduce

See [METHODOLOGY.md](METHODOLOGY.md). In short:

```bash
uv sync && uv run pytest                     # 65 tests, LLM mocked, no network
python eval/merge_bench.py --download
python eval/select_repos.py --n 5 && python eval/mine.py --language <lang> --repos <...>
python eval/run.py --track A --max-spend 0.70
python eval/run.py --track B --max-spend 0.60
python eval/analyze.py results/<run>
demo/demo.sh                                 # tiny repo, a conflict, the driver resolving it
```

## Credits

- **Merge-Bench** (Benedikt Schesch and Michael D. Ernst, ICPR 2026): the benchmark, its repo lists, and the scoring code reused in `eval/metrics.py` (MIT).
- **mergiraf** (https://mergiraf.org, GPL-3.0): the structured merge in stage 1, called as a separate program.
- **The Virginia Tech study** (Bowen Shen, *Can Large Language Models Resolve Real Java Merge Conflicts? An Evaluation with a Calibrated LLM-as-Judge*, arXiv 2607.27674). It proposed structured tool first, LLM where it abstains, and deterministic checks as the gate. This project tests that pipeline end to end across languages.
- tree-sitter and tree-sitter-language-pack (parsing), LangChain and `langchain-openai` (LLM client).
