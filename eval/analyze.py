from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path


def load(run: Path) -> dict[str, dict[str, dict]]:
    by_sys: dict[str, dict[str, dict]] = defaultdict(dict)
    for line in (run / "per_hunk.jsonl").read_text().splitlines():
        r = json.loads(line)
        if "excluded" not in r:
            by_sys[r["system"]][r["id"]] = r
    return by_sys


def paired(a: dict, b: dict, metric: str, cluster_key: str, n_boot: int = 2000, seed: int = 0, keep=None) -> dict:
    ids = [i for i in a if i in b and (keep is None or keep(a[i]))]
    clusters: dict[str, list[str]] = defaultdict(list)
    for i in ids:
        clusters[a[i].get(cluster_key, i)].append(i)
    keys = sorted(clusters)
    diff = lambda sel: sum(b[i][metric] - a[i][metric] for i in sel) / max(len(sel), 1)
    point = diff(ids)
    rng = random.Random(seed)
    boots = []
    for _ in range(n_boot):
        sel = [i for k in rng.choices(keys, k=len(keys)) for i in clusters[k]]
        boots.append(diff(sel))
    boots.sort()
    b_only = sum(1 for i in ids if b[i][metric] and not a[i][metric])
    a_only = sum(1 for i in ids if a[i][metric] and not b[i][metric])
    return {"n": len(ids), "clusters": len(keys), "diff_pts": round(100 * point, 2),
            "ci95_pts": [round(100 * boots[int(0.025 * n_boot)], 2), round(100 * boots[int(0.975 * n_boot)], 2)],
            "b_right_a_wrong": b_only, "a_right_b_wrong": a_only}


def main() -> int:
    run = Path(sys.argv[1])
    S = load(run)
    out: dict = {}
    ck = "file_id" if "hybrid" in S else "id"
    if "hybrid" in S:
        L, H, M = S["llm_only"], S["hybrid"], S["mergiraf_only"]
        out["hybrid_vs_llm_only"] = {m: paired(L, H, m, ck) for m in ("exact", "semantic")}
        out["hybrid_vs_llm_only_precision_note"] = "precision differences come with different abstain rates"
        out["hybrid_vs_mergiraf_only"] = {m: paired(M, H, m, ck) for m in ("exact", "semantic")}
        for split, keep in (("post_cutoff", lambda r: r["post_cutoff"]), ("pre_cutoff", lambda r: not r["post_cutoff"]),
                            ("merge_bench_sized", lambda r: r["mb_size"])):
            out[f"hybrid_vs_llm_only_{split}"] = paired(L, H, "exact", ck, keep=keep)
        ab = [i for i in H if H[i]["abstained"]]
        out["hybrid_abstained"] = {"n": len(ab), "llm_only_was_exact": sum(L[i]["exact"] for i in ab),
                                   "llm_only_was_semantic": sum(L[i]["semantic"] for i in ab),
                                   "llm_only_was_wrong": sum(not L[i]["semantic"] and not L[i]["abstained"] for i in ab)}
        out["by_hybrid_stage"] = {}
        for st in ("mergiraf", "llm", "llm_retry", "abstain", "unknown"):
            ids = [i for i in H if H[i]["stage"] == st]
            out["by_hybrid_stage"][st] = {"n": len(ids), "hybrid_exact": sum(H[i]["exact"] for i in ids),
                                          "llm_only_exact": sum(L[i]["exact"] for i in ids),
                                          "mergiraf_only_exact": sum(M[i]["exact"] for i in ids)}
        out["gate_rejections_total"] = sum(r["gate_rejections"] for r in H.values())
        out["files_with_gate_rejections"] = sum(1 for r in H.values() if r["gate_rejections"])
        out["unlocatable"] = {s: sum(r["outcome"] == "unlocatable" for r in S[s].values()) for s in S}
    else:
        L, G = S["llm_only"], S["llm_gate"]
        out["llm_gate_vs_llm_only"] = {m: paired(L, G, m, ck) for m in ("exact", "semantic")}
        out["gate_rejections_total"] = sum(r["gate_rejections"] for r in G.values())
        out["outcomes"] = {s: dict(Counter(r["outcome"] for r in S[s].values())) for s in S}
    (run / "analysis.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
