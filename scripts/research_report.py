"""Generate a paper-ready narrative summary from repository artifacts.

This script intentionally uses only the Python standard library so it can run even
in restricted environments where scientific dependencies are unavailable.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
RESULTS = ROOT / "results" / "reports"
TABLES = ROOT / "results" / "tables"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def safe_float(v: str, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def safe_int(v: str, default: int = 0) -> int:
    try:
        return int(float(v))
    except Exception:
        return default


def dataset_summary(papers: list[dict[str, str]]) -> dict:
    years = [safe_int(r.get("year", "0")) for r in papers if r.get("year")]
    clusters = Counter(r.get("cluster", "unknown") for r in papers)

    author_papers: Counter[str] = Counter()
    author_citations: defaultdict[str, float] = defaultdict(float)
    for row in papers:
        authors = [a.strip() for a in row.get("authors", "").split(";") if a.strip()]
        cites = safe_float(row.get("citations", "0"))
        for author in authors:
            author_papers[author] += 1
            author_citations[author] += cites

    top_papers = sorted(
        papers,
        key=lambda r: safe_float(r.get("citations", "0")),
        reverse=True,
    )[:10]

    return {
        "n_papers": len(papers),
        "year_min": min(years) if years else None,
        "year_max": max(years) if years else None,
        "n_domains": len(clusters),
        "domain_counts": dict(clusters.most_common()),
        "top_authors_by_papers": author_papers.most_common(10),
        "top_authors_by_citations": sorted(author_citations.items(), key=lambda x: x[1], reverse=True)[:10],
        "top_papers": [
            {
                "paper_id": r.get("paper_id", ""),
                "title": r.get("title", ""),
                "citations": safe_int(r.get("citations", "0")),
                "cluster": r.get("cluster", ""),
            }
            for r in top_papers
        ],
    }


def similarity_summary(sim_pairs: list[dict[str, str]], hashes: list[dict[str, str]]) -> dict:
    sims = [safe_float(r.get("similarity", "0")) for r in sim_pairs]
    same_cluster = sum(1 for r in sim_pairs if str(r.get("same_cluster", "")).lower() == "true")
    return {
        "n_similar_pairs": len(sim_pairs),
        "mean_similarity": round(sum(sims) / len(sims), 4) if sims else 0.0,
        "max_similarity": max(sims) if sims else 0.0,
        "same_cluster_share": round((same_cluster / len(sim_pairs)), 4) if sim_pairs else 0.0,
        "n_hash_records": len(hashes),
        "unique_fingerprints": len({r.get("fingerprint", "") for r in hashes if r.get("fingerprint")}),
    }


def researcher_summary(researchers: list[dict[str, str]]) -> dict:
    archetypes = Counter(r.get("archetype", "Unknown") for r in researchers)
    hi = [r for r in researchers if safe_int(r.get("is_high_impact", "0")) == 1]
    return {
        "n_researchers": len(researchers),
        "n_high_impact": len(hi),
        "archetype_counts": dict(archetypes.most_common()),
        "top_researchers_by_total_citations": [
            {
                "name": r.get("name", ""),
                "total_citations": safe_int(r.get("total_citations", "0")),
                "archetype": r.get("archetype", ""),
            }
            for r in sorted(researchers, key=lambda x: safe_float(x.get("total_citations", "0")), reverse=True)[:10]
        ],
    }


def load_model_metrics() -> dict:
    path = TABLES / "ml_model_metrics.csv"
    if not path.exists():
        return {
            "status": "missing",
            "note": "Model metrics file not present in repo. Run: python -m src.ml.train",
        }
    rows = read_csv(path)
    if not rows:
        return {"status": "empty", "note": "metrics file exists but has no rows"}

    best = sorted(rows, key=lambda r: safe_float(r.get("auc_mean", "0")), reverse=True)[0]
    return {
        "status": "available",
        "n_models": len(rows),
        "best_model": best,
        "all_models": rows,
    }


def build_paper_guidance(report: dict) -> str:
    ds = report["dataset"]
    sim = report["similarity"]
    rs = report["researchers"]
    ml = report["ml"]

    ml_line = (
        f"- Best model currently recorded: {ml['best_model'].get('model')} with AUC={ml['best_model'].get('auc_mean')}"
        if ml.get("status") == "available"
        else "- ML metrics file is not present yet in this environment; discuss planned model evaluation protocol and link to `src/ml/train.py`."
    )

    return f"""# Bell Labs Analysis Report (Auto-generated)

## 1) What data is in this repo
- Papers dataset size: **{ds['n_papers']}** publications spanning **{ds['year_min']}–{ds['year_max']}**.
- Distinct research domains (clusters): **{ds['n_domains']}**.
- Researcher profiles available: **{rs['n_researchers']}**.

## 2) How this helps answer your Bell Labs question
Your question is essentially: *what conditions enabled repeated innovation at Bell Labs?*
This repo addresses that via four measurable lenses:
1. **Impact prediction (ML)** — estimate which paper characteristics track high impact.
2. **Similarity + hashing** — connect related outputs even when labels differ.
3. **Network structure** — quantify which researchers were central or bridging.
4. **Archetypes/outcomes** — compare high-impact vs lower-impact researcher traits.

## 3) Key quantitative observations from current artifacts
- Similar pair records: **{sim['n_similar_pairs']}** with mean similarity **{sim['mean_similarity']}**.
- Hash coverage: **{sim['n_hash_records']}** records and **{sim['unique_fingerprints']}** unique fingerprints.
- High-impact researchers in profiles: **{rs['n_high_impact']}**.
{ml_line}

## 4) Suggested "Methods" section text (you can adapt)
- Construct a curated Bell Labs corpus with metadata: title, abstract, year, authors, domain label, and citation count.
- Build a paper fingerprinting system using deterministic hashes and MinHash/cosine similarity to detect related research streams.
- Build co-authorship networks and compute centrality metrics (degree, betweenness, eigenvector).
- Train multiple supervised classifiers for high-impact prediction using text + structural + team features with cross-validation.
- Compare unsupervised semantic clusters to curated labels (e.g., ARI) to test whether emergent themes align with known domains.

## 5) Suggested "Results" section text (you can adapt)
- Report model ranking by AUC/F1/accuracy and discuss which features are most predictive.
- Show that similarity/hashing recovers coherent clusters and potential cross-domain bridges.
- Show how high-impact researchers differ in career span, domain breadth, and network role.
- Discuss whether the evidence supports a replicable organizational model: long horizons, cross-domain interaction, and institutional stability.

## 6) Suggested "Limitations" section text
- Small sample size and historical curation may introduce selection bias.
- Citation-based impact can undercount practical/industrial influence.
- Affiliation/entity matching can still miss hidden Bell Labs ties.

## 7) Next run commands (for Colab/local)
```bash
python scripts/verify_environment.py
python -m src.ml.train
python -m src.similarity.paper_similarity
python -m src.network.author_network
python -m src.clustering.research_clustering
python -m src.researcher.researcher_analysis
```
"""


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    papers = read_csv(DATA / "papers.csv")
    hashes = read_csv(DATA / "paper_hash_table.csv") if (DATA / "paper_hash_table.csv").exists() else []
    sim_pairs = read_csv(DATA / "similar_paper_pairs.csv") if (DATA / "similar_paper_pairs.csv").exists() else []
    researchers = read_csv(DATA / "researcher_profiles.csv") if (DATA / "researcher_profiles.csv").exists() else []

    report = {
        "dataset": dataset_summary(papers),
        "similarity": similarity_summary(sim_pairs, hashes),
        "researchers": researcher_summary(researchers),
        "ml": load_model_metrics(),
    }

    with (RESULTS / "research_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    md = build_paper_guidance(report)
    (RESULTS / "research_brief.md").write_text(md, encoding="utf-8")

    print(f"Saved: {RESULTS / 'research_report.json'}")
    print(f"Saved: {RESULTS / 'research_brief.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
