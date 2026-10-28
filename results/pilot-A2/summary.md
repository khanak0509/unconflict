# Run pilot-A2 (track A)

model `gpt-6-luna` (reasoning_effort=none), seed 0, 275 conflicts from 275 items, 0 excluded. Spent this run: $0.0000.

Cost columns are nominal (what each system's calls cost without the shared cache).

**Overall**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 275 | 0.0% | 0.4% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 275 | 41.8% | 51.3% | 51.3% | 3.6% | 43.4% | 53.2% | 0 | $0.0167 | $0.000061 |
| llm_gate | 275 | 41.8% | 51.3% | 51.3% | 3.6% | 43.4% | 53.2% | 1 | $0.0168 | $0.000061 |

Stage that handled each conflict:

| system | mergiraf | llm | llm_retry | abstain | unknown |
|---|---:|---:|---:|---:|---:|
| git_default | 0.0% | 0.0% | 0.0% | 100.0% | 0.0% |
| llm_only | 0.0% | 96.4% | 0.0% | 3.6% | 0.0% |
| llm_gate | 0.0% | 96.0% | 0.4% | 3.6% | 0.0% |

**javascript**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 25 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 25 | 40.0% | 48.0% | 44.0% | 0.0% | 40.0% | 48.0% | 0 | $0.0015 | $0.000061 |
| llm_gate | 25 | 40.0% | 48.0% | 44.0% | 0.0% | 40.0% | 48.0% | 0 | $0.0015 | $0.000061 |

**java**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 25 | 0.0% | 4.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 25 | 20.0% | 64.0% | 64.0% | 0.0% | 20.0% | 64.0% | 0 | $0.0014 | $0.000058 |
| llm_gate | 25 | 20.0% | 64.0% | 64.0% | 0.0% | 20.0% | 64.0% | 0 | $0.0014 | $0.000058 |

**rust**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 25 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 25 | 36.0% | 40.0% | 40.0% | 4.0% | 37.5% | 41.7% | 0 | $0.0015 | $0.000060 |
| llm_gate | 25 | 36.0% | 40.0% | 40.0% | 4.0% | 37.5% | 41.7% | 0 | $0.0015 | $0.000060 |

**c**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 25 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 25 | 52.0% | 56.0% | 56.0% | 0.0% | 52.0% | 56.0% | 0 | $0.0015 | $0.000061 |
| llm_gate | 25 | 52.0% | 56.0% | 56.0% | 0.0% | 52.0% | 56.0% | 1 | $0.0016 | $0.000064 |

**cpp**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 25 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 25 | 56.0% | 68.0% | 68.0% | 0.0% | 56.0% | 68.0% | 0 | $0.0015 | $0.000060 |
| llm_gate | 25 | 56.0% | 68.0% | 68.0% | 0.0% | 56.0% | 68.0% | 0 | $0.0015 | $0.000060 |

**csharp**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 25 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 25 | 44.0% | 60.0% | 52.0% | 8.0% | 47.8% | 65.2% | 0 | $0.0014 | $0.000057 |
| llm_gate | 25 | 44.0% | 60.0% | 52.0% | 8.0% | 47.8% | 65.2% | 0 | $0.0014 | $0.000057 |

**php**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 25 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 25 | 48.0% | 52.0% | 48.0% | 4.0% | 50.0% | 54.2% | 0 | $0.0015 | $0.000062 |
| llm_gate | 25 | 48.0% | 52.0% | 48.0% | 4.0% | 50.0% | 54.2% | 0 | $0.0015 | $0.000062 |

**python**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 25 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 25 | 64.0% | 64.0% | 64.0% | 4.0% | 66.7% | 66.7% | 0 | $0.0015 | $0.000061 |
| llm_gate | 25 | 64.0% | 64.0% | 64.0% | 4.0% | 66.7% | 66.7% | 0 | $0.0015 | $0.000061 |

**ruby**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 25 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 25 | 24.0% | 28.0% | 36.0% | 4.0% | 25.0% | 29.2% | 0 | $0.0015 | $0.000062 |
| llm_gate | 25 | 24.0% | 28.0% | 36.0% | 4.0% | 25.0% | 29.2% | 0 | $0.0015 | $0.000062 |

**go**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 25 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 25 | 52.0% | 52.0% | 64.0% | 8.0% | 56.5% | 56.5% | 0 | $0.0016 | $0.000065 |
| llm_gate | 25 | 52.0% | 52.0% | 64.0% | 8.0% | 56.5% | 56.5% | 0 | $0.0016 | $0.000065 |

**typescript**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 25 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 25 | 24.0% | 32.0% | 28.0% | 8.0% | 26.1% | 34.8% | 0 | $0.0015 | $0.000061 |
| llm_gate | 25 | 24.0% | 32.0% | 28.0% | 8.0% | 26.1% | 34.8% | 0 | $0.0015 | $0.000061 |
