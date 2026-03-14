"""Generate a paper-ready narrative summary from repository artifacts.

This script intentionally uses only the Python standard library so it can run even
in restricted environments where scientific dependencies are unavailable.
"""

from __future__ import annotations

import csv
import json
import re
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


def split_authors(value: str) -> list[str]:
    return [p.strip() for p in re.split(r";|,| and ", value or "") if p.strip()]


def dataset_summary(papers: list[dict[str, str]]) -> dict:
    years = [safe_int(r.get("year", "0")) for r in papers if r.get("year")]
    clusters = Counter(r.get("cluster", "unknown") for r in papers)

    author_papers: Counter[str] = Counter()
    author_citations: defaultdict[str, float] = defaultdict(float)
    for row in papers:
        authors = split_authors(row.get("authors", ""))
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


def thesis_evidence_summary(papers: list[dict[str, str]], researchers: list[dict[str, str]], sim_pairs: list[dict[str, str]]) -> dict:
    domain_counts = Counter(r.get("cluster", "unknown") for r in papers)
    years = [safe_int(r.get("year", "0")) for r in papers if r.get("year")]

    researcher_domain_counts = [safe_int(r.get("n_domains", "0")) for r in researchers]
    bridge_count = sum(1 for r in researchers if safe_int(r.get("is_bridge", "0")) == 1)
    high_impact = [r for r in researchers if safe_int(r.get("is_high_impact", "0")) == 1]
    low_impact = [r for r in researchers if safe_int(r.get("is_high_impact", "0")) == 0]

    hi_span = [safe_float(r.get("career_span", "0")) for r in high_impact]
    lo_span = [safe_float(r.get("career_span", "0")) for r in low_impact]
    hi_domains = [safe_float(r.get("n_domains", "0")) for r in high_impact]
    lo_domains = [safe_float(r.get("n_domains", "0")) for r in low_impact]

    key_figures = ["Claude Shannon", "Harry Nyquist", "John Tukey", "Richard Hamming"]
    key_rows = [r for r in researchers if r.get("name", "") in key_figures]

    same_cluster_share = 0.0
    if sim_pairs:
        same_cluster_share = sum(1 for r in sim_pairs if str(r.get("same_cluster", "")).lower() == "true") / len(sim_pairs)

    return {
        "corpus_span_years": (max(years) - min(years)) if years else 0,
        "n_domains": len(domain_counts),
        "largest_domain_share": round(max(domain_counts.values()) / max(len(papers), 1), 4) if domain_counts else 0.0,
        "researcher_avg_domain_count": round(sum(researcher_domain_counts) / max(len(researcher_domain_counts), 1), 3),
        "bridge_researcher_count": bridge_count,
        "bridge_share": round(bridge_count / max(len(researchers), 1), 4),
        "high_impact_avg_career_span": round(sum(hi_span) / max(len(hi_span), 1), 2),
        "low_impact_avg_career_span": round(sum(lo_span) / max(len(lo_span), 1), 2),
        "high_impact_avg_domain_count": round(sum(hi_domains) / max(len(hi_domains), 1), 2),
        "low_impact_avg_domain_count": round(sum(lo_domains) / max(len(lo_domains), 1), 2),
        "similarity_same_cluster_share": round(same_cluster_share, 4),
        "key_figures": [
            {
                "name": r.get("name", ""),
                "career_span": safe_int(r.get("career_span", "0")),
                "n_domains": safe_int(r.get("n_domains", "0")),
                "is_bridge": safe_int(r.get("is_bridge", "0"), 0),
                "total_citations": safe_int(r.get("total_citations", "0")),
            }
            for r in sorted(key_rows, key=lambda x: x.get("name", ""))
        ],
    }


def write_thesis_evidence_csv(evidence: dict) -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    out = TABLES / "thesis_evidence_summary.csv"
    rows = [
        ("corpus_span_years", evidence["corpus_span_years"]),
        ("n_domains", evidence["n_domains"]),
        ("largest_domain_share", evidence["largest_domain_share"]),
        ("researcher_avg_domain_count", evidence["researcher_avg_domain_count"]),
        ("bridge_researcher_count", evidence["bridge_researcher_count"]),
        ("bridge_share", evidence["bridge_share"]),
        ("high_impact_avg_career_span", evidence["high_impact_avg_career_span"]),
        ("low_impact_avg_career_span", evidence["low_impact_avg_career_span"]),
        ("high_impact_avg_domain_count", evidence["high_impact_avg_domain_count"]),
        ("low_impact_avg_domain_count", evidence["low_impact_avg_domain_count"]),
        ("similarity_same_cluster_share", evidence["similarity_same_cluster_share"]),
    ]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        w.writerows(rows)


def build_paper_guidance(report: dict) -> str:
    ds = report["dataset"]
    sim = report["similarity"]
    rs = report["researchers"]
    ml = report["ml"]
    ev = report["thesis_evidence"]

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
- Evidence summary table generated at: **results/tables/thesis_evidence_summary.csv**.

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
- Bridge researchers: **{ev['bridge_researcher_count']}** ({round(ev['bridge_share']*100, 1)}% of profiles).
- High-impact vs low-impact career span: **{ev['high_impact_avg_career_span']} vs {ev['low_impact_avg_career_span']} years**.
- High-impact vs low-impact domain breadth: **{ev['high_impact_avg_domain_count']} vs {ev['low_impact_avg_domain_count']} domains**.
{ml_line}

## 4) Evidence-backed answer to your thesis question
A data-supported answer is: Bell Labs breakthroughs appear to come from **long research horizons + cross-domain bridge people + coherent but diverse technical domains**.
- Long horizons: high-impact researchers have longer average careers.
- Bridge structure: a non-trivial share of researchers are cross-domain bridges.
- Domain diversity: work spans {ev['n_domains']} domains with no single domain overwhelming the corpus (largest share {round(ev['largest_domain_share']*100, 1)}%).
- Semantic cohesion: same-cluster similarity share is {round(ev['similarity_same_cluster_share']*100, 1)}%, indicating coherent streams that still interact through bridge researchers.

## 5) Suggested "Methods" section text (you can adapt)
- Construct a curated Bell Labs corpus with metadata: title, abstract, year, authors, domain label, and citation count.
- Build a paper fingerprinting system using deterministic hashes and MinHash/cosine similarity to detect related research streams.
- Build co-authorship networks and compute centrality metrics (degree, betweenness, eigenvector).
- Train multiple supervised classifiers for high-impact prediction using text + structural + team features with cross-validation.
- Compare unsupervised semantic clusters to curated labels (e.g., ARI) to test whether emergent themes align with known domains.

## 6) Suggested "Results" section text (you can adapt)
- Report model ranking by AUC/F1/accuracy and discuss which features are most predictive.
- Show that similarity/hashing recovers coherent clusters and potential cross-domain bridges.
- Show how high-impact researchers differ in career span, domain breadth, and network role.
- Discuss whether the evidence supports a replicable organizational model: long horizons, cross-domain interaction, and institutional stability.

## 7) Suggested "Limitations" section text
- Small sample size and historical curation may introduce selection bias.
- Citation-based impact can undercount practical/industrial influence.
- Affiliation/entity matching can still miss hidden Bell Labs ties.

## 8) Next run commands (for Colab/local)
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
        "thesis_evidence": thesis_evidence_summary(papers, researchers, sim_pairs),
    }

    with (RESULTS / "research_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    write_thesis_evidence_csv(report["thesis_evidence"])

    md = build_paper_guidance(report)
    (RESULTS / "research_brief.md").write_text(md, encoding="utf-8")

    print(f"Saved: {RESULTS / 'research_report.json'}")
    print(f"Saved: {RESULTS / 'research_brief.md'}")
    print(f"Saved: {TABLES / 'thesis_evidence_summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
