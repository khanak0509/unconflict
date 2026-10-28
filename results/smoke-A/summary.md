# Run smoke-A (track A)

model `gpt-6-luna` (reasoning_effort=none), seed 0, 10 conflicts from 10 items, 0 excluded. Spent this run: $0.0006.

Cost columns are nominal (what each system's calls cost without the shared cache).

**Overall**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 10 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 10 | 30.0% | 40.0% | 30.0% | 0.0% | 30.0% | 40.0% | 0 | $0.0006 | $0.000063 |
| llm_gate | 10 | 30.0% | 40.0% | 30.0% | 0.0% | 30.0% | 40.0% | 0 | $0.0006 | $0.000063 |

Stage that handled each conflict:

| system | mergiraf | llm | llm_retry | abstain | unknown |
|---|---:|---:|---:|---:|---:|
| git_default | 0.0% | 0.0% | 0.0% | 100.0% | 0.0% |
| llm_only | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% |
| llm_gate | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% |

**python**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 2 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 2 | 50.0% | 50.0% | 50.0% | 0.0% | 50.0% | 50.0% | 0 | $0.0001 | $0.000062 |
| llm_gate | 2 | 50.0% | 50.0% | 50.0% | 0.0% | 50.0% | 50.0% | 0 | $0.0001 | $0.000062 |

**javascript**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 2 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 2 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0 | $0.0001 | $0.000061 |
| llm_gate | 2 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0 | $0.0001 | $0.000061 |

**typescript**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 2 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 2 | 0.0% | 50.0% | 0.0% | 0.0% | 0.0% | 50.0% | 0 | $0.0001 | $0.000070 |
| llm_gate | 2 | 0.0% | 50.0% | 0.0% | 0.0% | 0.0% | 50.0% | 0 | $0.0001 | $0.000070 |

**java**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 2 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 2 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0 | $0.0001 | $0.000057 |
| llm_gate | 2 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0 | $0.0001 | $0.000057 |

**go**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 2 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 2 | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% | 100.0% | 0 | $0.0001 | $0.000063 |
| llm_gate | 2 | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% | 100.0% | 0 | $0.0001 | $0.000063 |
