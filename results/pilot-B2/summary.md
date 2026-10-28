# Run pilot-B2 (track B)

model `gpt-6-luna` (reasoning_effort=none), seed 0, 240 conflicts from 162 items, 0 excluded. Spent this run: $0.0186.

Cost columns are nominal (what each system's calls cost without the shared cache).

**Overall**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 240 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 240 | 25.8% | 27.1% | 28.8% | 55.4% | 57.9% | 60.7% | 0 | $0.0000 | $0.000000 |
| llm_only | 240 | 47.5% | 50.0% | 48.8% | 4.2% | 49.6% | 52.2% | 0 | $0.0597 | $0.000249 |
| hybrid | 240 | 46.7% | 49.2% | 50.4% | 10.4% | 52.1% | 54.9% | 46 | $0.0577 | $0.000240 |

Stage that handled each conflict:

| system | mergiraf | llm | llm_retry | abstain | unknown |
|---|---:|---:|---:|---:|---:|
| git_default | 0.0% | 0.0% | 0.0% | 100.0% | 0.0% |
| mergiraf_only | 44.6% | 0.0% | 0.0% | 55.4% | 0.0% |
| llm_only | 0.0% | 95.4% | 0.0% | 4.2% | 0.4% |
| hybrid | 40.8% | 40.0% | 1.7% | 7.9% | 9.6% |

**python**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 40 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 40 | 27.5% | 27.5% | 30.0% | 65.0% | 78.6% | 78.6% | 0 | $0.0000 | $0.000000 |
| llm_only | 40 | 65.0% | 65.0% | 65.0% | 2.5% | 66.7% | 66.7% | 0 | $0.0043 | $0.000107 |
| hybrid | 40 | 70.0% | 70.0% | 72.5% | 2.5% | 71.8% | 71.8% | 0 | $0.0028 | $0.000070 |

**javascript**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 40 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 40 | 30.0% | 32.5% | 32.5% | 62.5% | 80.0% | 86.7% | 0 | $0.0000 | $0.000000 |
| llm_only | 40 | 47.5% | 50.0% | 50.0% | 15.0% | 55.9% | 58.8% | 0 | $0.0205 | $0.000513 |
| hybrid | 40 | 57.5% | 60.0% | 60.0% | 17.5% | 69.7% | 72.7% | 5 | $0.0259 | $0.000648 |

**typescript**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 40 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 40 | 27.5% | 27.5% | 27.5% | 47.5% | 52.4% | 52.4% | 0 | $0.0000 | $0.000000 |
| llm_only | 40 | 42.5% | 45.0% | 45.0% | 2.5% | 43.6% | 46.2% | 0 | $0.0091 | $0.000228 |
| hybrid | 40 | 42.5% | 45.0% | 45.0% | 5.0% | 44.7% | 47.4% | 3 | $0.0094 | $0.000235 |

**java**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 40 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 40 | 25.0% | 27.5% | 27.5% | 40.0% | 41.7% | 45.8% | 0 | $0.0000 | $0.000000 |
| llm_only | 40 | 32.5% | 37.5% | 35.0% | 0.0% | 32.5% | 37.5% | 0 | $0.0108 | $0.000269 |
| hybrid | 40 | 30.0% | 32.5% | 32.5% | 15.0% | 35.3% | 38.2% | 14 | $0.0072 | $0.000180 |

**go**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 40 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 40 | 37.5% | 37.5% | 45.0% | 42.5% | 65.2% | 65.2% | 0 | $0.0000 | $0.000000 |
| llm_only | 40 | 47.5% | 52.5% | 47.5% | 2.5% | 48.7% | 53.8% | 0 | $0.0067 | $0.000169 |
| hybrid | 40 | 47.5% | 52.5% | 57.5% | 5.0% | 50.0% | 55.3% | 6 | $0.0033 | $0.000082 |

**rust**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 40 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 40 | 7.5% | 10.0% | 10.0% | 75.0% | 30.0% | 40.0% | 0 | $0.0000 | $0.000000 |
| llm_only | 40 | 50.0% | 50.0% | 50.0% | 2.5% | 51.3% | 51.3% | 0 | $0.0082 | $0.000206 |
| hybrid | 40 | 32.5% | 35.0% | 35.0% | 17.5% | 39.4% | 42.4% | 18 | $0.0091 | $0.000229 |

**post_cutoff**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 72 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 72 | 18.1% | 19.4% | 19.4% | 62.5% | 48.1% | 51.9% | 0 | $0.0000 | $0.000000 |
| llm_only | 72 | 47.2% | 47.2% | 47.2% | 1.4% | 47.9% | 47.9% | 0 | $0.0157 | $0.000218 |
| hybrid | 72 | 38.9% | 40.3% | 40.3% | 5.6% | 41.2% | 42.6% | 10 | $0.0161 | $0.000224 |

**pre_cutoff**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 168 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 168 | 29.2% | 30.4% | 32.7% | 52.4% | 61.2% | 63.8% | 0 | $0.0000 | $0.000000 |
| llm_only | 168 | 47.6% | 51.2% | 49.4% | 5.4% | 50.3% | 54.1% | 0 | $0.0440 | $0.000262 |
| hybrid | 168 | 50.0% | 53.0% | 54.8% | 12.5% | 57.1% | 60.5% | 36 | $0.0416 | $0.000248 |

**merge_bench_sized**

| system | n | exact | semantic | whitespace-norm | abstain | precision (exact) | precision (semantic) | gate rejections | cost | $/conflict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| git_default | 91 | 0.0% | 0.0% | 0.0% | 100.0% | – | – | 0 | $0.0000 | $0.000000 |
| mergiraf_only | 91 | 33.0% | 33.0% | 33.0% | 49.5% | 65.2% | 65.2% | 0 | $0.0000 | $0.000000 |
| llm_only | 91 | 60.4% | 61.5% | 60.4% | 6.6% | 64.7% | 65.9% | 0 | $0.0286 | $0.000315 |
| hybrid | 91 | 60.4% | 61.5% | 61.5% | 8.8% | 66.3% | 67.5% | 8 | $0.0305 | $0.000335 |
