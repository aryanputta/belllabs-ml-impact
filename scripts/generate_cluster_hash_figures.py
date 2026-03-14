"""Generate lightweight SVG figures for cluster + hashing analysis (stdlib only)."""

from __future__ import annotations

import csv
import math
from collections import Counter
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


def cluster_distribution_svg(rows: list[dict[str, str]]) -> str:
    counts = Counter(r.get("cluster", "unknown") for r in rows)
    ordered = counts.most_common()
    width, height = 980, 540
    margin_left, margin_top = 220, 40
    chart_w, chart_h = 700, 430
    max_count = max(counts.values()) if counts else 1

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="20" y="28" font-size="22" font-family="Arial" font-weight="bold">Cluster Distribution of Bell Labs Outputs</text>',
        '<text x="20" y="50" font-size="13" font-family="Arial" fill="#555">Source: data/processed/papers.csv</text>',
    ]

    bar_h = chart_h / max(len(ordered), 1)
    palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#17becf"]

    for i, (name, cnt) in enumerate(ordered):
        y = margin_top + i * bar_h + 8
        w = (cnt / max_count) * (chart_w - 40)
        color = palette[i % len(palette)]
        parts.append(f'<text x="20" y="{y + 14:.1f}" font-size="13" font-family="Arial">{name}</text>')
        parts.append(f'<rect x="{margin_left}" y="{y:.1f}" width="{w:.1f}" height="{bar_h - 12:.1f}" fill="{color}" rx="4"/>')
        parts.append(f'<text x="{margin_left + w + 8:.1f}" y="{y + 14:.1f}" font-size="12" font-family="Arial">{cnt}</text>')

    parts.append('</svg>')
    return "\n".join(parts)


def hash_similarity_svg(hash_rows: list[dict[str, str]], sim_rows: list[dict[str, str]]) -> str:
    top = sorted(sim_rows, key=lambda r: float(r.get("similarity", 0)), reverse=True)[:20]
    nodes = []
    seen = set()
    for r in top:
        for k in ("paper_a", "paper_b"):
            p = r.get(k, "")
            if p and p not in seen:
                seen.add(p)
                nodes.append(p)

    cx, cy, rad = 420, 270, 190
    pos = {}
    for i, n in enumerate(nodes):
        ang = (2 * math.pi * i / max(len(nodes), 1))
        pos[n] = (cx + rad * math.cos(ang), cy + rad * math.sin(ang))

    hash_map = {r.get("paper_id", ""): r.get("fingerprint", "")[:6] for r in hash_rows}

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="980" height="560">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="20" y="28" font-size="22" font-family="Arial" font-weight="bold">Hash-Similarity Link Graph (Top Similar Paper Pairs)</text>',
        '<text x="20" y="50" font-size="13" font-family="Arial" fill="#555">Edges weighted by cosine similarity; node labels include hash prefix.</text>',
    ]

    for r in top:
        a, b = r.get("paper_a", ""), r.get("paper_b", "")
        if a not in pos or b not in pos:
            continue
        s = float(r.get("similarity", 0.0))
        x1, y1 = pos[a]
        x2, y2 = pos[b]
        stroke = 1 + 5 * max(0.0, min(1.0, s))
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#6baed6" stroke-width="{stroke:.2f}" opacity="0.6"/>')

    for n, (x, y) in pos.items():
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="11" fill="#1f77b4"/>')
        label = f"{n} ({hash_map.get(n,'------')})"
        parts.append(f'<text x="{x + 14:.1f}" y="{y + 4:.1f}" font-size="10" font-family="Arial">{label}</text>')

    uniq_hash = len({r.get("fingerprint", "") for r in hash_rows if r.get("fingerprint")})
    parts.append('<rect x="20" y="420" width="360" height="110" fill="#f7f7f7" stroke="#ccc"/>')
    parts.append(f'<text x="30" y="445" font-size="13" font-family="Arial">Total hash records: {len(hash_rows)}</text>')
    parts.append(f'<text x="30" y="468" font-size="13" font-family="Arial">Unique fingerprints: {uniq_hash}</text>')
    parts.append(f'<text x="30" y="491" font-size="13" font-family="Arial">Similar pairs shown: {len(top)}</text>')
    parts.append('<text x="30" y="514" font-size="12" font-family="Arial" fill="#555">Use with paper_hash_table.csv + similar_paper_pairs.csv</text>')

    parts.append('</svg>')
    return "\n".join(parts)


def paper_flow_network_svg(papers: list[dict[str, str]], sim_rows: list[dict[str, str]]) -> str:
    """Directed paper network (arrow links), arranged left-to-right by year."""
    by_id = {r.get("paper_id", ""): r for r in papers}
    top = sorted(sim_rows, key=lambda r: float(r.get("similarity", 0.0)), reverse=True)[:14]

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

    x0, x1 = 120, 880
    y_base, row_h = 120, 56
    pos = {}
    year_counts = {}
    for n in nodes:
        y = int(by_id[n].get("year", 0))
        frac = (y - min_y) / max((max_y - min_y), 1)
        x = x0 + frac * (x1 - x0)
        idx = year_counts.get(y, 0)
        year_counts[y] = idx + 1
        yy = y_base + idx * row_h
        pos[n] = (x, yy)

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="680">',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L10,4 L0,8 z" fill="#7f7f7f"/></marker></defs>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="20" y="28" font-size="22" font-family="Arial" font-weight="bold">Directed Paper Network (Similarity Arrows by Time)</text>',
        '<text x="20" y="50" font-size="13" font-family="Arial" fill="#555">Nodes are papers; arrows connect top similar pairs, directed from earlier to later year.</text>',
    ]

    # year axis
    for y in years:
        frac = (y - min_y) / max((max_y - min_y), 1)
        x = x0 + frac * (x1 - x0)
        parts.append(f'<line x1="{x:.1f}" y1="70" x2="{x:.1f}" y2="650" stroke="#f0f0f0"/>')
        parts.append(f'<text x="{x-12:.1f}" y="86" font-size="11" font-family="Arial" fill="#666">{y}</text>')

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
        stroke = 1 + 4 * max(0.0, min(1.0, sim))
        parts.append(
            f'<line x1="{x1p:.1f}" y1="{y1p:.1f}" x2="{x2p:.1f}" y2="{y2p:.1f}" stroke="#7f7f7f" '
            f'stroke-width="{stroke:.2f}" opacity="0.75" marker-end="url(#arrow)"/>'
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
    for n in nodes:
        x, y = pos[n]
        row = by_id[n]
        cluster = row.get("cluster", "unknown")
        color = palette.get(cluster, "#444")
        title = row.get("title", "")[:34]
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="{color}"/>')
        parts.append(f'<text x="{x+10:.1f}" y="{y+4:.1f}" font-size="10" font-family="Arial">{n}: {title}</text>')

    parts.append('<rect x="20" y="560" width="360" height="100" fill="#f7f7f7" stroke="#ccc"/>')
    parts.append(f'<text x="30" y="585" font-size="13" font-family="Arial">Papers shown: {len(nodes)}</text>')
    parts.append(f'<text x="30" y="607" font-size="13" font-family="Arial">Similarity arrows: {len(top)}</text>')
    parts.append('<text x="30" y="629" font-size="12" font-family="Arial" fill="#555">Layout: x-axis by publication year (earlier → later)</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    papers = read_csv(DATA / "papers.csv")
    hashes = read_csv(DATA / "paper_hash_table.csv")
    sim = read_csv(DATA / "similar_paper_pairs.csv")

    save(OUT / "fig14_cluster_distribution.svg", cluster_distribution_svg(papers))
    save(OUT / "fig15_hash_similarity_graph.svg", hash_similarity_svg(hashes, sim))
    save(OUT / "fig16_paper_flow_network.svg", paper_flow_network_svg(papers, sim))

    print(f"Saved: {OUT / 'fig14_cluster_distribution.svg'}")
    print(f"Saved: {OUT / 'fig15_hash_similarity_graph.svg'}")
    print(f"Saved: {OUT / 'fig16_paper_flow_network.svg'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
