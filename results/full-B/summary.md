# Run full-B (track B)

model `gpt-6-luna` (reasoning_effort=none), seed 0, 1131 conflicts from 725 items, 0 excluded. Spent this run: $0.1973.

Cost columns are nominal (what each system's calls cost without the shared cache).

**Overall**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 1131 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 1131 | 23.8% | 25.6% | 25.7% | 57.4% | 55.8% | 60.0% | 0 | $0.0000 | $0.000000 |
| llm_only | 1131 | 40.6% | 43.9% | 42.3% | 4.5% | 42.5% | 46.0% | 0 | $0.2001 | $0.000177 |
| hybrid | 1131 | 43.7% | 47.3% | 46.5% | 9.5% | 48.3% | 52.3% | 199 | $0.1501 | $0.000133 |

Stage that handled each conflict:

| system | mergiraf | llm | llm_retry | abstain | unknown |
|---|---:|---:|---:|---:|---:|
| git_default | 0.0% | 0.0% | 0.0% | 100.0% | 0.0% |
| mergiraf_only | 42.6% | 0.0% | 0.0% | 57.4% | 0.0% |
| llm_only | 0.0% | 95.3% | 0.0% | 4.3% | 0.4% |
| hybrid | 40.6% | 43.2% | 1.3% | 8.1% | 6.7% |

**python**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 210 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 210 | 25.2% | 26.7% | 26.2% | 66.2% | 74.6% | 78.9% | 0 | $0.0000 | $0.000000 |
| llm_only | 210 | 56.7% | 60.0% | 59.0% | 1.9% | 57.8% | 61.2% | 0 | $0.0287 | $0.000137 |
| hybrid | 210 | 65.7% | 68.6% | 67.1% | 1.4% | 66.7% | 69.6% | 3 | $0.0186 | $0.000088 |

**javascript**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 215 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 215 | 26.5% | 28.8% | 27.4% | 58.1% | 63.3% | 68.9% | 0 | $0.0000 | $0.000000 |
| llm_only | 215 | 34.9% | 38.1% | 35.8% | 11.2% | 39.3% | 42.9% | 0 | $0.0316 | $0.000147 |
| hybrid | 215 | 43.3% | 47.0% | 45.1% | 12.1% | 49.2% | 53.4% | 29 | $0.0222 | $0.000103 |

**typescript**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 176 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 176 | 26.1% | 29.0% | 29.0% | 52.3% | 54.8% | 60.7% | 0 | $0.0000 | $0.000000 |
| llm_only | 176 | 37.5% | 40.3% | 40.3% | 2.8% | 38.6% | 41.5% | 0 | $0.0364 | $0.000207 |
| hybrid | 176 | 35.8% | 39.8% | 39.8% | 15.9% | 42.6% | 47.3% | 69 | $0.0315 | $0.000179 |

**java**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 150 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 150 | 28.0% | 30.0% | 30.0% | 43.3% | 49.4% | 52.9% | 0 | $0.0000 | $0.000000 |
| llm_only | 150 | 32.0% | 36.0% | 34.7% | 2.7% | 32.9% | 37.0% | 0 | $0.0265 | $0.000176 |
| hybrid | 150 | 36.0% | 40.0% | 39.3% | 8.0% | 39.1% | 43.5% | 19 | $0.0152 | $0.000101 |

**go**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 116 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 116 | 31.0% | 31.9% | 37.1% | 45.7% | 57.1% | 58.7% | 0 | $0.0000 | $0.000000 |
| llm_only | 116 | 38.8% | 42.2% | 40.5% | 2.6% | 39.8% | 43.4% | 0 | $0.0204 | $0.000176 |
| hybrid | 116 | 41.4% | 44.8% | 49.1% | 5.2% | 43.6% | 47.3% | 14 | $0.0108 | $0.000093 |

**rust**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 264 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 264 | 13.3% | 14.4% | 14.4% | 66.3% | 39.3% | 42.7% | 0 | $0.0000 | $0.000000 |
| llm_only | 264 | 40.2% | 43.6% | 40.5% | 4.2% | 41.9% | 45.5% | 0 | $0.0566 | $0.000214 |
| hybrid | 264 | 37.1% | 40.9% | 38.6% | 12.5% | 42.4% | 46.8% | 65 | $0.0520 | $0.000197 |

**post_cutoff**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 396 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 396 | 19.4% | 19.7% | 19.9% | 64.1% | 54.2% | 54.9% | 0 | $0.0000 | $0.000000 |
| llm_only | 396 | 37.1% | 39.9% | 37.4% | 3.0% | 38.3% | 41.1% | 0 | $0.0884 | $0.000223 |
| hybrid | 396 | 37.6% | 40.2% | 38.9% | 9.3% | 41.5% | 44.3% | 94 | $0.0779 | $0.000197 |

**pre_cutoff**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 735 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 735 | 26.1% | 28.7% | 28.8% | 53.7% | 56.5% | 62.1% | 0 | $0.0000 | $0.000000 |
| llm_only | 735 | 42.4% | 46.1% | 44.9% | 5.3% | 44.8% | 48.7% | 0 | $0.1116 | $0.000152 |
| hybrid | 735 | 46.9% | 51.2% | 50.6% | 9.7% | 52.0% | 56.6% | 105 | $0.0723 | $0.000098 |

**merge_bench_sized**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 477 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 477 | 24.7% | 26.6% | 25.4% | 55.8% | 55.9% | 60.2% | 0 | $0.0000 | $0.000000 |
| llm_only | 477 | 49.7% | 52.0% | 50.3% | 5.5% | 52.5% | 55.0% | 0 | $0.0641 | $0.000134 |
| hybrid | 477 | 49.9% | 52.6% | 50.9% | 8.4% | 54.5% | 57.4% | 59 | $0.0491 | $0.000103 |
