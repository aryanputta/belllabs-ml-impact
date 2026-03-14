"""Basic data sanity checks for core processed dataset (stdlib only)."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed" / "papers.csv"
OUT = ROOT / "results" / "reports" / "data_sanity_report.json"


def main() -> int:
    with DATA.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    required = ["paper_id", "title", "authors", "year", "abstract", "citations", "cluster"]
    missing_cols = [c for c in required if c not in rows[0]] if rows else required

    bad_year = 0
    bad_citations = 0
    dup_ids = 0
    ids = Counter()
    empty_titles = 0
    for r in rows:
        pid = r.get("paper_id", "")
        ids[pid] += 1
        if not r.get("title", "").strip():
            empty_titles += 1
        try:
            y = int(float(r.get("year", "0")))
            if y < 1900 or y > 2030:
                bad_year += 1
        except Exception:
            bad_year += 1
        try:
            c = float(r.get("citations", "0"))
            if c < 0:
                bad_citations += 1
        except Exception:
            bad_citations += 1

    dup_ids = sum(1 for _, v in ids.items() if v > 1)
    domain_counts = Counter(r.get("cluster", "unknown") for r in rows)

    report = {
        "dataset": str(DATA.relative_to(ROOT)),
        "n_rows": len(rows),
        "required_columns_missing": missing_cols,
        "duplicate_paper_ids": dup_ids,
        "invalid_year_rows": bad_year,
        "invalid_citation_rows": bad_citations,
        "empty_title_rows": empty_titles,
        "domain_counts": dict(domain_counts.most_common()),
        "status": "pass" if not any([missing_cols, dup_ids, bad_year, bad_citations, empty_titles]) else "warn",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved: {OUT}")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
