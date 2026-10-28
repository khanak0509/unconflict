# Run smoke-B (track B)

model `gpt-6-luna` (reasoning_effort=none), seed 0, 14 conflicts from 9 items, 0 excluded. Spent this run: $0.0023.

Cost columns are nominal (what each system's calls cost without the shared cache).

**Overall**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 14 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 14 | 78.6% | 85.7% | 85.7% | 0.0% | 78.6% | 85.7% | 0 | $0.0000 | $0.000000 |
| llm_only | 14 | 57.1% | 64.3% | 64.3% | 0.0% | 57.1% | 64.3% | 0 | $0.0023 | $0.000166 |
| hybrid | 14 | 78.6% | 85.7% | 85.7% | 0.0% | 78.6% | 85.7% | 0 | $0.0002 | $0.000016 |

Stage that handled each conflict:

| system | mergiraf | llm | llm_retry | abstain | unknown |
|---|---:|---:|---:|---:|---:|
| git_default | 0.0% | 0.0% | 0.0% | 100.0% | 0.0% |
| mergiraf_only | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| llm_only | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% |
| hybrid | 92.9% | 7.1% | 0.0% | 0.0% | 0.0% |

**python**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 5 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 5 | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% | 100.0% | 0 | $0.0000 | $0.000000 |
| llm_only | 5 | 40.0% | 40.0% | 40.0% | 0.0% | 40.0% | 40.0% | 0 | $0.0005 | $0.000097 |
| hybrid | 5 | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% | 100.0% | 0 | $0.0000 | $0.000000 |

**javascript**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 3 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 3 | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% | 100.0% | 0 | $0.0000 | $0.000000 |
| llm_only | 3 | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% | 100.0% | 0 | $0.0002 | $0.000068 |
| hybrid | 3 | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% | 100.0% | 0 | $0.0000 | $0.000000 |

**typescript**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 2 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 2 | 50.0% | 50.0% | 50.0% | 0.0% | 50.0% | 50.0% | 0 | $0.0000 | $0.000000 |
| llm_only | 2 | 50.0% | 50.0% | 50.0% | 0.0% | 50.0% | 50.0% | 0 | $0.0004 | $0.000183 |
| hybrid | 2 | 50.0% | 50.0% | 50.0% | 0.0% | 50.0% | 50.0% | 0 | $0.0002 | $0.000115 |

**java**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 2 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 0.0% | 50.0% | 0 | $0.0000 | $0.000000 |
| llm_only | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 0.0% | 50.0% | 0 | $0.0006 | $0.000299 |
| hybrid | 2 | 0.0% | 50.0% | 50.0% | 0.0% | 0.0% | 50.0% | 0 | $0.0000 | $0.000000 |

**go**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 2 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 2 | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% | 100.0% | 0 | $0.0000 | $0.000000 |
| llm_only | 2 | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% | 100.0% | 0 | $0.0007 | $0.000334 |
| hybrid | 2 | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% | 100.0% | 0 | $0.0000 | $0.000000 |

**post_cutoff**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 3 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 3 | 66.7% | 66.7% | 66.7% | 0.0% | 66.7% | 66.7% | 0 | $0.0000 | $0.000000 |
| llm_only | 3 | 66.7% | 66.7% | 66.7% | 0.0% | 66.7% | 66.7% | 0 | $0.0006 | $0.000209 |
| hybrid | 3 | 66.7% | 66.7% | 66.7% | 0.0% | 66.7% | 66.7% | 0 | $0.0002 | $0.000077 |

**pre_cutoff**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 11 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 11 | 81.8% | 90.9% | 90.9% | 0.0% | 81.8% | 90.9% | 0 | $0.0000 | $0.000000 |
| llm_only | 11 | 54.5% | 63.6% | 63.6% | 0.0% | 54.5% | 63.6% | 0 | $0.0017 | $0.000154 |
| hybrid | 11 | 81.8% | 90.9% | 90.9% | 0.0% | 81.8% | 90.9% | 0 | $0.0000 | $0.000000 |

**merge_bench_sized**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 7 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 7 | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% | 100.0% | 0 | $0.0000 | $0.000000 |
| llm_only | 7 | 85.7% | 85.7% | 85.7% | 0.0% | 85.7% | 85.7% | 0 | $0.0004 | $0.000062 |
| hybrid | 7 | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% | 100.0% | 0 | $0.0002 | $0.000033 |
