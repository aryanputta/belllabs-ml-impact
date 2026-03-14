"""Prepare a stable 2-file canonical submission bundle.

Priority coverage:
- ML model results
- Hash/similarity pairs
- Cluster distribution

Outputs:
- results/submission/canonical_evidence_table.csv
- results/submission/canonical_evidence.json
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
TABLES = ROOT / "results" / "tables"
REPORTS = ROOT / "results" / "reports"
OUT = ROOT / "results" / "submission"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fnum(v: str, d: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return d


def build_bundle() -> dict:
    papers = read_csv(DATA / "papers.csv")
    pairs = read_csv(DATA / "similar_paper_pairs.csv")
    hashes = read_csv(DATA / "paper_hash_table.csv")
    ml = read_csv(TABLES / "ml_model_metrics.csv")

    best = sorted(ml, key=lambda r: fnum(r.get("auc_mean", "0")), reverse=True)[0] if ml else {}
    clusters = Counter(r.get("cluster", "unknown") for r in papers)
    sims = [fnum(r.get("similarity", "0")) for r in pairs]
    same_cluster = sum(1 for r in pairs if str(r.get("same_cluster", "")).lower() == "true")

    data_sanity = {}
    sanity_path = REPORTS / "data_sanity_report.json"
    if sanity_path.exists():
        data_sanity = json.loads(sanity_path.read_text(encoding="utf-8"))

    payload = {
        "bundle_version": "v1.0",
        "intent": "Two canonical outputs for paper citation with emphasis on ML + hash/similarity + clustering.",
        "canonical_files": [
            "results/submission/canonical_evidence_table.csv",
            "results/submission/canonical_evidence.json",
        ],
        "ml": {
            "models_reported": len(ml),
            "best_model": best,
        },
        "hash_similarity": {
            "n_hash_records": len(hashes),
            "n_similar_pairs": len(pairs),
            "mean_similarity": round(sum(sims) / len(sims), 4) if sims else 0.0,
            "max_similarity": max(sims) if sims else 0.0,
            "same_cluster_share": round((same_cluster / len(pairs)), 4) if pairs else 0.0,
            "top_pair": pairs[0] if pairs else {},
        },
        "clusters": {
            "n_clusters": len(clusters),
            "cluster_counts": dict(clusters.most_common()),
        },
        "figures_for_paper": [
            "results/figures/fig11_researcher_success.png",
            "results/figures/fig12_similarity_heatmap.png",
            "results/figures/fig13_researcher_archetypes.png",
            "results/figures/fig14_cluster_distribution.svg",
            "results/figures/fig15_hash_similarity_graph.svg",
            "results/figures/fig16_paper_flow_network.svg",
        ],
        "data_sanity": data_sanity,
    }
    return payload


def write_table(bundle: dict) -> None:
    rows = [
        {"analysis": "ml", "metric": "models_reported", "value": str(bundle["ml"]["models_reported"]), "source": "results/tables/ml_model_metrics.csv"},
        {"analysis": "ml", "metric": "best_model", "value": str(bundle["ml"]["best_model"].get("model", "")), "source": "results/tables/ml_model_metrics.csv"},
        {"analysis": "ml", "metric": "best_auc", "value": str(bundle["ml"]["best_model"].get("auc_mean", "")), "source": "results/tables/ml_model_metrics.csv"},
        {"analysis": "hash_similarity", "metric": "n_hash_records", "value": str(bundle["hash_similarity"]["n_hash_records"]), "source": "data/processed/paper_hash_table.csv"},
        {"analysis": "hash_similarity", "metric": "n_similar_pairs", "value": str(bundle["hash_similarity"]["n_similar_pairs"]), "source": "data/processed/similar_paper_pairs.csv"},
        {"analysis": "hash_similarity", "metric": "mean_similarity", "value": str(bundle["hash_similarity"]["mean_similarity"]), "source": "data/processed/similar_paper_pairs.csv"},
        {"analysis": "hash_similarity", "metric": "same_cluster_share", "value": str(bundle["hash_similarity"]["same_cluster_share"]), "source": "data/processed/similar_paper_pairs.csv"},
        {"analysis": "clusters", "metric": "n_clusters", "value": str(bundle["clusters"]["n_clusters"]), "source": "data/processed/papers.csv"},
        {"analysis": "data_sanity", "metric": "status", "value": str(bundle.get("data_sanity", {}).get("status", "unknown")), "source": "results/reports/data_sanity_report.json"},
    ]

    out_csv = OUT / "canonical_evidence_table.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["analysis", "metric", "value", "source"])
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    bundle = build_bundle()

    (OUT / "canonical_evidence.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    write_table(bundle)

    print(f"Saved: {OUT / 'canonical_evidence_table.csv'}")
    print(f"Saved: {OUT / 'canonical_evidence.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
