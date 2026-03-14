"""Map project objectives to concrete repo implementation status.

This script is dependency-light (stdlib only) so it can run in restricted environments.
It emits both JSON + Markdown status artifacts under results/reports/.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "results" / "reports"


@dataclass
class CheckItem:
    objective: str
    implementation: str
    status: str
    evidence_files: list[str]
    notes: str


def exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def run() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)

    checks = [
        CheckItem(
            objective="Define and operationalize Bell Labs innovation question",
            implementation="README research framing + auto-generated research brief",
            status="done" if exists("README.md") and exists("results/reports/research_brief.md") else "missing",
            evidence_files=["README.md", "results/reports/research_brief.md"],
            notes="Framing + narrative answer path is in place.",
        ),
        CheckItem(
            objective="Collect papers/publications and structure core dataset",
            implementation="Processed paper corpus",
            status="done" if exists("data/processed/papers.csv") else "missing",
            evidence_files=["data/processed/papers.csv"],
            notes="Paper-level table exists and powers all downstream analyses.",
        ),
        CheckItem(
            objective="Hash/matching system for connecting related outputs",
            implementation="SHA fingerprint + MinHash similarity",
            status="done" if exists("src/similarity/paper_similarity.py") and exists("data/processed/paper_hash_table.csv") else "partial",
            evidence_files=["src/similarity/paper_similarity.py", "data/processed/paper_hash_table.csv", "data/processed/similar_paper_pairs.csv"],
            notes="Implemented for papers. Extend same pattern to patents/presentations when added.",
        ),
        CheckItem(
            objective="Network analysis of researchers/coauthors",
            implementation="Co-authorship network module + researcher profiles",
            status="done" if exists("src/network/author_network.py") and exists("data/processed/researcher_profiles.csv") else "partial",
            evidence_files=["src/network/author_network.py", "src/researcher/researcher_analysis.py", "data/processed/researcher_profiles.csv"],
            notes="Centrality + archetypes support institutional-structure claims.",
        ),
        CheckItem(
            objective="Cluster work by topic/domain/time",
            implementation="Similarity clustering + semantic KMeans",
            status="done" if exists("src/clustering/research_clustering.py") and exists("data/processed/papers_with_kmeans_clusters.csv") else "partial",
            evidence_files=["src/clustering/research_clustering.py", "src/similarity/paper_similarity.py"],
            notes="Clustering code exists; precomputed kmeans artifact may need fresh run.",
        ),
        CheckItem(
            objective="Machine learning model to predict impact",
            implementation="Paper-level ML pipeline with CV",
            status="done" if exists("src/ml/train.py") and exists("results/tables/ml_model_metrics.csv") else "partial",
            evidence_files=["src/ml/train.py", "src/ml/features.py", "results/tables/ml_model_metrics.csv"],
            notes="Model pipeline exists; environment dependencies required for full rerun.",
        ),
        CheckItem(
            objective="Reproducible local/Colab execution",
            implementation="Requirements + env check + colab helper + CI",
            status="done" if all(exists(p) for p in [
                "requirements.txt",
                "scripts/verify_environment.py",
                "scripts/colab_setup.py",
                ".github/workflows/python-ci.yml",
            ]) else "partial",
            evidence_files=["requirements.txt", "scripts/verify_environment.py", "scripts/colab_setup.py", ".github/workflows/python-ci.yml"],
            notes="Colab is the recommended runtime when local env is constrained.",
        ),
        CheckItem(
            objective="Security/secrets protection",
            implementation=".gitignore + SECURITY.md + branch protection guidance",
            status="done" if exists(".gitignore") and exists("SECURITY.md") else "missing",
            evidence_files=[".gitignore", "SECURITY.md"],
            notes="Protects against accidental key leakage and unsafe push practices.",
        ),
        CheckItem(
            objective="Bell Labs identity resolution beyond explicit labels",
            implementation="Affiliation/name matching rules",
            status="partial",
            evidence_files=["data/processed/papers.csv"],
            notes="Dataset includes affiliation fields, but a dedicated resolver module + confidence scoring should be added.",
        ),
        CheckItem(
            objective="Include patents/presentations alongside papers",
            implementation="Unified multi-output ingestion pipeline",
            status="pending",
            evidence_files=[],
            notes="Not yet implemented in current repo artifacts; high-priority next extension.",
        ),
    ]

    status_counts: dict[str, int] = {}
    for c in checks:
        status_counts[c.status] = status_counts.get(c.status, 0) + 1

    payload = {
        "summary": {
            "total_objectives": len(checks),
            "done": status_counts.get("done", 0),
            "partial": status_counts.get("partial", 0),
            "pending": status_counts.get("pending", 0),
            "missing": status_counts.get("missing", 0),
        },
        "checks": [asdict(c) for c in checks],
    }

    (REPORTS / "project_checklist_status.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Bell Labs Project Checklist Status",
        "",
        f"- Total objectives: **{payload['summary']['total_objectives']}**",
        f"- Done: **{payload['summary']['done']}**",
        f"- Partial: **{payload['summary']['partial']}**",
        f"- Pending: **{payload['summary']['pending']}**",
        f"- Missing: **{payload['summary']['missing']}**",
        "",
        "## Objective Mapping",
        "",
    ]

    icon = {"done": "✅", "partial": "🟡", "pending": "⚪", "missing": "❌"}
    for c in checks:
        lines.append(f"- {icon.get(c.status, '•')} **{c.objective}** — `{c.status}`")
        lines.append(f"  - Implementation: {c.implementation}")
        if c.evidence_files:
            lines.append(f"  - Evidence: {', '.join(c.evidence_files)}")
        lines.append(f"  - Notes: {c.notes}")

    (REPORTS / "project_checklist_status.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Saved: {REPORTS / 'project_checklist_status.json'}")
    print(f"Saved: {REPORTS / 'project_checklist_status.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
