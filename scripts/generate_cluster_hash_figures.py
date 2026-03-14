"""Generate lightweight SVG figures for cluster + hashing analysis (stdlib only)."""

from __future__ import annotations

import csv
import math
import re
from collections import Counter, defaultdict
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
OUT = ROOT / "results" / "figures"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _svg_open(width: int, height: int) -> list[str]:
    return [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
    ]


def _split_authors(value: str) -> list[str]:
    return [p.strip() for p in re.split(r";|,| and ", value or "") if p.strip()]


def _short_authors(value: str) -> str:
    authors = _split_authors(value)
    if not authors:
        return "Unknown"
    if len(authors) == 1:
        return authors[0]
    return f"{authors[0]} +{len(authors) - 1}"


def _short_title(value: str, limit: int = 38) -> str:
    value = (value or "").strip()
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _cluster_label(value: str) -> str:
    return (value or "unknown").replace("_", " ").title()


def cluster_distribution_svg(rows: list[dict[str, str]]) -> str:
    counts = Counter(r.get("cluster", "unknown") for r in rows)
    ordered = counts.most_common()
    width, height = 980, 560
    margin_left, margin_top = 240, 78
    chart_w, chart_h = 700, 430
    max_count = max(counts.values()) if counts else 1

    parts = _svg_open(width, height)
    parts.extend([
        '<text x="24" y="38" font-size="24" font-family="Arial" font-weight="bold" fill="#17202a">Cluster Distribution of Bell Labs Outputs</text>',
        '<text x="24" y="60" font-size="13" font-family="Arial" fill="#566573">Categories are shown with cleaned labels for publication-ready readability.</text>',
    ])

    bar_h = chart_h / max(len(ordered), 1)
    palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#17becf"]

    for i, (name, cnt) in enumerate(ordered):
        y = margin_top + i * bar_h + 8
        w = (cnt / max_count) * (chart_w - 40)
        color = palette[i % len(palette)]
        parts.append(f'<text x="24" y="{y + 14:.1f}" font-size="13" font-family="Arial" fill="#1b2631">{escape(_cluster_label(name))}</text>')
        parts.append(f'<rect x="{margin_left}" y="{y:.1f}" width="{w:.1f}" height="{bar_h - 12:.1f}" fill="{color}" rx="4"/>')
        parts.append(f'<text x="{margin_left + w + 8:.1f}" y="{y + 14:.1f}" font-size="12" font-family="Arial" fill="#1b2631">{cnt}</text>')

    parts.append('</svg>')
    return "\n".join(parts)


def hash_similarity_svg(hash_rows: list[dict[str, str]], sim_rows: list[dict[str, str]], papers: list[dict[str, str]]) -> str:
    """Render top hash-similar pairs as clean link rows (non-overlapping)."""
    top = sorted(sim_rows, key=lambda r: float(r.get("similarity", 0.0)), reverse=True)[:10]
    paper_map = {r.get("paper_id", ""): r for r in papers}
    hash_map = {r.get("paper_id", ""): r.get("fingerprint", "")[:6] for r in hash_rows}

    width, height = 1320, 760
    parts = _svg_open(width, height)
    parts.extend([
        '<text x="24" y="38" font-size="24" font-family="Arial" font-weight="bold" fill="#17202a">Hash Similarity Links (Readable Pair View)</text>',
        '<text x="24" y="60" font-size="13" font-family="Arial" fill="#566573">Each row is one high-similarity pair with author + category labels (no stacked overlaps).</text>',
    ])

    start_y, row_h = 106, 56
    x1, x2 = 210, 830
    for i, edge in enumerate(top):
        y = start_y + i * row_h
        a, b = edge.get("paper_a", ""), edge.get("paper_b", "")
        ra, rb = paper_map.get(a, {}), paper_map.get(b, {})
        sim = float(edge.get("similarity", 0.0))
        stroke = 1.4 + 4 * max(0.0, min(1.0, sim))

        la = f"{_short_authors(ra.get('authors', ''))} · {_cluster_label(ra.get('cluster', 'unknown'))}"
        lb = f"{_short_authors(rb.get('authors', ''))} · {_cluster_label(rb.get('cluster', 'unknown'))}"
        ta = _short_title(ra.get("title", ""), 34)
        tb = _short_title(rb.get("title", ""), 34)

        parts.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="#9ec4de" stroke-width="{stroke:.2f}"/>')
        parts.append(f'<circle cx="{x1}" cy="{y}" r="7" fill="#2e86c1" stroke="#fff" stroke-width="1"/>')
        parts.append(f'<circle cx="{x2}" cy="{y}" r="7" fill="#2e86c1" stroke="#fff" stroke-width="1"/>')

        parts.append(f'<rect x="24" y="{y-18}" width="520" height="34" rx="4" fill="#ffffff" stroke="#d5dbdb"/>')
        parts.append(f'<text x="34" y="{y-5}" font-size="10.8" font-family="Arial" fill="#1b2631">{escape(la)} · hash {escape(hash_map.get(a, "------"))}</text>')
        parts.append(f'<text x="34" y="{y+9}" font-size="10" font-family="Arial" fill="#5d6d7e">{escape(ta)}</text>')

        parts.append(f'<rect x="884" y="{y-18}" width="410" height="34" rx="4" fill="#ffffff" stroke="#d5dbdb"/>')
        parts.append(f'<text x="894" y="{y-5}" font-size="10.8" font-family="Arial" fill="#1b2631">{escape(lb)} · hash {escape(hash_map.get(b, "------"))}</text>')
        parts.append(f'<text x="894" y="{y+9}" font-size="10" font-family="Arial" fill="#5d6d7e">{escape(tb)}</text>')

        parts.append(f'<rect x="614" y="{y-13}" width="92" height="26" rx="12" fill="#eef5fb" stroke="#c6d9ea"/>')
        parts.append(f'<text x="634" y="{y+4}" font-size="11" font-family="Arial" fill="#1b2631">sim: {sim:.3f}</text>')

    uniq_hash = len({r.get("fingerprint", "") for r in hash_rows if r.get("fingerprint")})
    parts.append('<rect x="24" y="676" width="620" height="58" fill="#f8f9f9" stroke="#d5dbdb" rx="4"/>')
    parts.append(f'<text x="36" y="699" font-size="12.5" font-family="Arial" fill="#1b2631">Hash records: {len(hash_rows)} | Unique fingerprints: {uniq_hash} | Pair links shown: {len(top)}</text>')
    parts.append('<text x="36" y="719" font-size="11" font-family="Arial" fill="#5d6d7e">Format: Author · Category + short title for each side of every pair.</text>')

    parts.append('</svg>')
    return "\n".join(parts)


def paper_flow_network_svg(papers: list[dict[str, str]], sim_rows: list[dict[str, str]]) -> str:
    """Timeline network with top arc region + separate annotation region to avoid overlap."""
    by_id = {r.get("paper_id", ""): r for r in papers}
    top = sorted(sim_rows, key=lambda r: float(r.get("similarity", 0.0)), reverse=True)[:8]

    nodes = []
    seen = set()
    for e in top:
        for pid in (e.get("paper_a", ""), e.get("paper_b", "")):
            if pid and pid in by_id and pid not in seen:
                seen.add(pid)
                nodes.append(pid)

    nodes = sorted(nodes, key=lambda p: int(by_id[p].get("year", 0)))
    years = sorted({int(by_id[n].get("year", 0)) for n in nodes})
    min_y, max_y = (min(years), max(years)) if years else (0, 1)

    width, height = 1360, 840
    x0, x1 = 120, 1240
    timeline_y = 270

    pos = {}
    for n in nodes:
        year = int(by_id[n].get("year", 0))
        frac = (year - min_y) / max((max_y - min_y), 1)
        pos[n] = (x0 + frac * (x1 - x0), timeline_y)

    parts = _svg_open(width, height)
    parts.extend([
        '<defs><marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L10,4 L0,8 z" fill="#7f8c8d"/></marker></defs>',
        '<text x="24" y="38" font-size="24" font-family="Arial" font-weight="bold" fill="#17202a">Directed Paper Flow Network (Cleaner Timeline View)</text>',
        '<text x="24" y="60" font-size="13" font-family="Arial" fill="#566573">Arrows stay above timeline, while labels are placed below in rows to prevent overlap.</text>',
        f'<line x1="{x0}" y1="{timeline_y}" x2="{x1}" y2="{timeline_y}" stroke="#cfd8dc" stroke-width="1.5"/>',
    ])

    for year in years:
        frac = (year - min_y) / max((max_y - min_y), 1)
        x = x0 + frac * (x1 - x0)
        parts.append(f'<line x1="{x:.1f}" y1="95" x2="{x:.1f}" y2="644" stroke="#ecf0f1"/>')
        parts.append(f'<text x="{x-12:.1f}" y="88" font-size="10.5" font-family="Arial" fill="#7b8a8b">{year}</text>')

    for e in top:
        a, b = e.get("paper_a", ""), e.get("paper_b", "")
        if a not in pos or b not in pos:
            continue
        ya = int(by_id[a].get("year", 0))
        yb = int(by_id[b].get("year", 0))
        src, dst = (a, b) if ya <= yb else (b, a)
        x1p, y1p = pos[src]
        x2p, y2p = pos[dst]
        sim = float(e.get("similarity", 0.0))
        stroke = 1.2 + 3.2 * max(0.0, min(1.0, sim))
        mx = (x1p + x2p) / 2
        curve = 130 + (abs(x2p - x1p) * 0.04)
        parts.append(
            f'<path d="M{x1p:.1f},{y1p:.1f} Q{mx:.1f},{curve:.1f} {x2p:.1f},{y2p:.1f}" stroke="#7f8c8d" '
            f'fill="none" stroke-width="{stroke:.2f}" opacity="0.68" marker-end="url(#arrow)"/>'
        )

    palette = {
        "information_theory": "#1f77b4",
        "network_theory": "#17becf",
        "computing_systems": "#2ca02c",
        "semiconductor_physics": "#d62728",
        "radio_astronomy": "#9467bd",
        "photonics_laser": "#ff7f0e",
        "mathematics_statistics": "#8c564b",
        "satellite_communications": "#e377c2",
    }

    # node dots on timeline
    for n in nodes:
        x, y = pos[n]
        color = palette.get(by_id[n].get("cluster", "unknown"), "#566573")
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{color}" stroke="#ffffff" stroke-width="1"/>')

    # clean label rows below timeline
    label_y_start, label_row_h = 350, 52
    for idx, n in enumerate(nodes):
        x, _ = pos[n]
        row = by_id[n]
        y = label_y_start + idx * label_row_h
        author = _short_authors(row.get("authors", ""))
        category = _cluster_label(row.get("cluster", "unknown"))
        title = _short_title(row.get("title", ""), 42)

        parts.append(f'<line x1="{x:.1f}" y1="278" x2="{x:.1f}" y2="{y-12:.1f}" stroke="#d6dbdf" stroke-width="1"/>')
        parts.append(f'<rect x="{x+8:.1f}" y="{y-20:.1f}" width="330" height="36" rx="4" fill="#ffffff" stroke="#d5dbdb"/>')
        parts.append(f'<text x="{x+16:.1f}" y="{y-6:.1f}" font-size="10.8" font-family="Arial" fill="#1b2631">{escape(author)} · {escape(category)}</text>')
        parts.append(f'<text x="{x+16:.1f}" y="{y+8:.1f}" font-size="10" font-family="Arial" fill="#5d6d7e">{escape(title)}</text>')

    parts.append('<rect x="24" y="772" width="600" height="52" fill="#f8f9f9" stroke="#d5dbdb" rx="4"/>')
    parts.append(f'<text x="36" y="794" font-size="12.5" font-family="Arial" fill="#1b2631">Papers shown: {len(nodes)} | Similarity arrows: {len(top)}</text>')
    parts.append('<text x="36" y="813" font-size="11" font-family="Arial" fill="#5d6d7e">No stacked labels: all annotation cards are separated into clean rows below the timeline.</text>')

    parts.append('</svg>')
    return "\n".join(parts)


def innovation_map_svg(papers: list[dict[str, str]], researchers: list[dict[str, str]]) -> str:
    """Clean, non-overlapping bipartite innovation map."""
    highlight = ["Claude Shannon", "Harry Nyquist", "John Tukey", "Richard Hamming"]

    author_domains: dict[str, set[str]] = defaultdict(set)
    author_papers: Counter[str] = Counter()
    for row in papers:
        cluster = row.get("cluster", "unknown")
        for a in _split_authors(row.get("authors", "")):
            author_domains[a].add(cluster)
            author_papers[a] += 1

    domain_counts = Counter(r.get("cluster", "unknown") for r in papers)
    domains = [d for d, _ in domain_counts.most_common(8)]

    selected = set(highlight)
    for name, _ in sorted(author_papers.items(), key=lambda kv: kv[1], reverse=True):
        if len(selected) >= 14:
            break
        if author_papers[name] >= 2 or len(author_domains.get(name, set())) >= 2:
            selected.add(name)

    # order by primary domain index to reduce edge crossings
    domain_order = {d: i for i, d in enumerate(domains)}

    def primary_domain(name: str) -> int:
        doms = sorted(author_domains.get(name, set()), key=lambda d: (-domain_counts.get(d, 0), d))
        if not doms:
            return 10_000
        return domain_order.get(doms[0], 10_000)

    researchers_ordered = sorted(selected, key=lambda n: (primary_domain(n), n))

    width, height = 1400, 980
    parts = _svg_open(width, height)
    parts.extend([
        '<text x="24" y="38" font-size="28" font-family="Arial" font-weight="bold" fill="#17202a">Bell Labs Innovation Map</text>',
        '<text x="24" y="60" font-size="14" font-family="Arial" fill="#566573">Researchers (left) linked to categories (right). Ordered to reduce crossings and keep labels readable.</text>',
    ])

    cluster_colors = {
        "information_theory": "#1f77b4",
        "network_theory": "#17becf",
        "computing_systems": "#2ca02c",
        "semiconductor_physics": "#d62728",
        "radio_astronomy": "#9467bd",
        "photonics_laser": "#ff7f0e",
        "mathematics_statistics": "#8c564b",
        "satellite_communications": "#e377c2",
    }

    left_x, right_x = 210, 1060
    y_start = 108
    r_step = 58
    d_step = 98

    r_pos = {name: (left_x, y_start + i * r_step) for i, name in enumerate(researchers_ordered)}
    d_pos = {d: (right_x, 150 + i * d_step) for i, d in enumerate(domains)}

    # edges
    for name in researchers_ordered:
        doms = sorted(author_domains.get(name, set()), key=lambda d: domain_order.get(d, 9999))
        for d in doms:
            if d not in d_pos:
                continue
            x1, y1 = r_pos[name]
            x2, y2 = d_pos[d]
            bridge = len(doms) >= 2
            stroke_w = 2.2 if bridge else 1.1
            opacity = 0.52 if bridge else 0.23
            cx = x1 + (x2 - x1) * 0.55
            cy = y1 + (y2 - y1) * 0.25
            parts.append(
                f'<path d="M{x1:.1f},{y1:.1f} Q{cx:.1f},{cy:.1f} {x2:.1f},{y2:.1f}" stroke="#aeb6bf" '
                f'fill="none" stroke-width="{stroke_w:.1f}" opacity="{opacity:.2f}"/>'
            )

    # researcher side
    for name in researchers_ordered:
        x, y = r_pos[name]
        papers_n = author_papers.get(name, 0)
        dom_n = len(author_domains.get(name, set()))
        is_hi = name in highlight
        fill = "#fef9e7" if is_hi else "#f8f9f9"
        stroke = "#1b2631" if is_hi else "#d5dbdb"
        radius = 10 if is_hi else 7
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        if dom_n >= 2:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius + 4}" fill="none" stroke="#5dade2" stroke-width="1.3" stroke-dasharray="3 2"/>')
        parts.append(f'<text x="{x+16:.1f}" y="{y+4:.1f}" font-size="11.5" font-family="Arial" fill="#1b2631">{escape(name)} ({papers_n} papers, {dom_n} domains)</text>')

    # domain side
    for d in domains:
        x, y = d_pos[d]
        color = cluster_colors.get(d, "#7f8c8d")
        label = _cluster_label(d)
        count = domain_counts.get(d, 0)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="16" fill="{color}" stroke="#ffffff" stroke-width="1"/>')
        parts.append(f'<rect x="{x+22:.1f}" y="{y-16:.1f}" width="300" height="30" rx="4" fill="#ffffff" stroke="#d5dbdb"/>')
        parts.append(f'<text x="{x+32:.1f}" y="{y+3:.1f}" font-size="12" font-family="Arial" fill="#1b2631">{escape(label)} ({count} papers)</text>')

    bridge_count = sum(1 for n in researchers_ordered if len(author_domains.get(n, set())) >= 2)
    parts.append('<rect x="24" y="914" width="900" height="52" rx="4" fill="#f8f9f9" stroke="#d5dbdb"/>')
    parts.append(f'<text x="38" y="936" font-size="12.5" font-family="Arial" fill="#1b2631">Researchers shown: {len(researchers_ordered)} | Categories shown: {len(domains)} | Cross-domain bridges: {bridge_count}</text>')
    parts.append('<text x="38" y="955" font-size="11" font-family="Arial" fill="#5d6d7e">Dashed ring = bridge researcher. Highlighted: Shannon, Nyquist, Tukey, Hamming.</text>')

    parts.append('</svg>')
    return "\n".join(parts)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    papers = read_csv(DATA / "papers.csv")
    hashes = read_csv(DATA / "paper_hash_table.csv")
    sim = read_csv(DATA / "similar_paper_pairs.csv")
    researchers = read_csv(DATA / "researcher_profiles.csv")

    save(OUT / "fig14_cluster_distribution.svg", cluster_distribution_svg(papers))
    save(OUT / "fig15_hash_similarity_graph.svg", hash_similarity_svg(hashes, sim, papers))
    save(OUT / "fig16_paper_flow_network.svg", paper_flow_network_svg(papers, sim))
    save(OUT / "fig17_bell_labs_innovation_map.svg", innovation_map_svg(papers, researchers))

    print(f"Saved: {OUT / 'fig14_cluster_distribution.svg'}")
    print(f"Saved: {OUT / 'fig15_hash_similarity_graph.svg'}")
    print(f"Saved: {OUT / 'fig16_paper_flow_network.svg'}")
    print(f"Saved: {OUT / 'fig17_bell_labs_innovation_map.svg'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
