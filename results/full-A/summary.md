# Run full-A (track A)

model `gpt-6-luna` (reasoning_effort=none), seed 0, 7887 conflicts from 7887 items, 5 excluded. Spent this run: $0.4622.

Cost columns are nominal (what each system's calls cost without the shared cache).

**Overall**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 7882 | 1.0% | 2.2% | 1.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 7882 | 42.6% | 50.7% | 49.3% | 4.2% | 44.4% | 52.8% | 0 | $0.4797 | $0.000061 |
| llm_gate | 7882 | 42.6% | 50.7% | 49.3% | 4.3% | 44.4% | 52.9% | 29 | $0.4813 | $0.000061 |

Stage that handled each conflict:

| system | mergiraf | llm | llm_retry | abstain | unknown |
|---|---:|---:|---:|---:|---:|
| git_default | 0.0% | 0.0% | 0.0% | 100.0% | 0.0% |
| llm_only | 0.0% | 95.8% | 0.0% | 4.2% | 0.0% |
| llm_gate | 0.0% | 95.5% | 0.2% | 4.3% | 0.0% |

**javascript**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 743 | 0.9% | 3.8% | 0.9% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 743 | 44.3% | 55.3% | 50.5% | 3.0% | 45.6% | 57.0% | 0 | $0.0452 | $0.000061 |
| llm_gate | 743 | 44.3% | 55.3% | 50.5% | 3.0% | 45.6% | 57.0% | 1 | $0.0452 | $0.000061 |

**java**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 794 | 0.0% | 1.4% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 794 | 44.8% | 59.2% | 58.1% | 1.6% | 45.6% | 60.2% | 0 | $0.0470 | $0.000059 |
| llm_gate | 794 | 44.7% | 58.9% | 57.8% | 1.9% | 45.6% | 60.1% | 4 | $0.0471 | $0.000059 |

**rust**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 705 | 5.5% | 5.5% | 5.5% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 705 | 40.3% | 45.5% | 42.7% | 5.1% | 42.2% | 47.7% | 0 | $0.0419 | $0.000059 |
| llm_gate | 705 | 40.4% | 45.7% | 42.8% | 5.2% | 42.4% | 47.9% | 5 | $0.0423 | $0.000060 |

**c**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 623 | 0.0% | 0.5% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 623 | 64.7% | 70.1% | 69.0% | 1.6% | 65.7% | 71.3% | 0 | $0.0387 | $0.000062 |
| llm_gate | 623 | 64.7% | 70.1% | 69.0% | 1.6% | 65.7% | 71.3% | 1 | $0.0388 | $0.000062 |

**cpp**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 764 | 0.8% | 1.0% | 0.8% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 764 | 39.7% | 51.6% | 49.7% | 3.9% | 41.3% | 53.7% | 0 | $0.0481 | $0.000063 |
| llm_gate | 764 | 39.7% | 51.6% | 49.7% | 4.1% | 41.3% | 53.8% | 3 | $0.0483 | $0.000063 |

**csharp**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 845 | 0.4% | 0.4% | 0.4% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 845 | 35.1% | 53.1% | 44.1% | 6.0% | 37.3% | 56.4% | 0 | $0.0515 | $0.000061 |
| llm_gate | 845 | 35.1% | 53.1% | 44.1% | 6.2% | 37.3% | 56.5% | 2 | $0.0516 | $0.000061 |

**php**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 559 | 3.2% | 11.1% | 3.2% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 559 | 49.2% | 59.0% | 53.5% | 3.4% | 50.7% | 60.6% | 0 | $0.0327 | $0.000058 |
| llm_gate | 559 | 49.2% | 59.0% | 53.5% | 3.4% | 50.7% | 60.6% | 0 | $0.0327 | $0.000058 |

**python**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 732 | 0.1% | 2.2% | 0.1% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 732 | 51.4% | 54.2% | 57.2% | 3.1% | 52.9% | 55.4% | 0 | $0.0443 | $0.000060 |
| llm_gate | 732 | 51.5% | 54.4% | 57.4% | 3.3% | 53.1% | 55.6% | 4 | $0.0445 | $0.000061 |

**ruby**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 647 | 0.2% | 0.2% | 0.2% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 647 | 35.2% | 37.9% | 42.7% | 3.1% | 36.4% | 39.1% | 0 | $0.0377 | $0.000058 |
| llm_gate | 647 | 35.2% | 37.9% | 42.7% | 3.1% | 36.4% | 39.1% | 1 | $0.0378 | $0.000058 |

**go**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 671 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 671 | 34.9% | 35.8% | 41.1% | 9.7% | 38.6% | 39.6% | 0 | $0.0439 | $0.000065 |
| llm_gate | 671 | 34.9% | 35.8% | 41.1% | 9.7% | 38.6% | 39.6% | 1 | $0.0439 | $0.000065 |

**typescript**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 799 | 0.0% | 0.4% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| llm_only | 799 | 33.7% | 38.2% | 36.9% | 5.5% | 35.6% | 40.4% | 0 | $0.0488 | $0.000061 |
| llm_gate | 799 | 33.7% | 38.2% | 36.9% | 5.8% | 35.7% | 40.5% | 7 | $0.0492 | $0.000062 |
