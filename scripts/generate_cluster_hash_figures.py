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

    parts.append("</svg>")
    return "\n".join(parts)


def hash_similarity_svg(hash_rows: list[dict[str, str]], sim_rows: list[dict[str, str]]) -> str:
    top = sorted(sim_rows, key=lambda r: float(r.get("similarity", 0)), reverse=True)[:12]
    nodes = []
    seen = set()
    neighbors = {}
    for r in top:
        a = r.get("paper_a", "")
        b = r.get("paper_b", "")
        if a and b:
            neighbors.setdefault(a, set()).add(b)
            neighbors.setdefault(b, set()).add(a)
        for k in ("paper_a", "paper_b"):
            p = r.get(k, "")
            if p and p not in seen:
                seen.add(p)
                nodes.append(p)

    components = []
    unvisited = set(nodes)
    while unvisited:
        start = unvisited.pop()
        stack = [start]
        comp = [start]
        while stack:
            cur = stack.pop()
            for nxt in neighbors.get(cur, set()):
                if nxt in unvisited:
                    unvisited.remove(nxt)
                    stack.append(nxt)
                    comp.append(nxt)
        components.append(sorted(comp))
    components.sort(key=len, reverse=True)

    width, height = 1080, 620
    pos = {}
    cols = 3
    for i, comp in enumerate(components):
        col = i % cols
        row = i // cols
        cx = 200 + col * 320
        cy = 180 + row * 250
        rad = max(48, 24 * len(comp))
        for j, node in enumerate(comp):
            ang = 2 * math.pi * j / max(len(comp), 1)
            pos[node] = (cx + rad * math.cos(ang), cy + rad * math.sin(ang))

    hash_map = {r.get("paper_id", ""): r.get("fingerprint", "")[:6] for r in hash_rows}

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="24" y="34" font-size="24" font-family="Arial" font-weight="bold" fill="#17202a">Hash Similarity Links (Highest-Scoring Pairs)</text>',
        '<text x="24" y="58" font-size="13" font-family="Arial" fill="#5d6d7e">Cleaner component layout with weighted edges and compact node tags.</text>',
    ]

    for r in top:
        a, b = r.get("paper_a", ""), r.get("paper_b", "")
        if a not in pos or b not in pos:
            continue
        s = float(r.get("similarity", 0.0))
        x1, y1 = pos[a]
        x2, y2 = pos[b]
        stroke = 1.5 + 4.5 * max(0.0, min(1.0, s))
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#5499c7" stroke-width="{stroke:.2f}" opacity="0.52"/>')

    for n, (x, y) in pos.items():
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9.5" fill="#2e86c1" stroke="#ffffff" stroke-width="1.2"/>')
        label = escape(f"{n} · {hash_map.get(n, '------')}")
        tx, ty = x + 12.5, y - 12
        parts.append(f'<rect x="{tx - 4:.1f}" y="{ty - 10:.1f}" width="112" height="16" rx="3" fill="#ffffff" opacity="0.88"/>')
        parts.append(f'<text x="{tx:.1f}" y="{ty:.1f}" font-size="10" font-family="Arial" fill="#1b2631">{label}</text>')

    uniq_hash = len({r.get("fingerprint", "") for r in hash_rows if r.get("fingerprint")})
    parts.append('<rect x="24" y="498" width="410" height="98" fill="#f8f9f9" stroke="#d5dbdb" rx="4"/>')
    parts.append(f'<text x="36" y="526" font-size="13" font-family="Arial" fill="#1b2631">Total hash records: {len(hash_rows)}</text>')
    parts.append(f'<text x="36" y="547" font-size="13" font-family="Arial" fill="#1b2631">Unique fingerprints: {uniq_hash}</text>')
    parts.append(f'<text x="36" y="568" font-size="13" font-family="Arial" fill="#1b2631">Top similarity links shown: {len(top)}</text>')
    parts.append('<text x="36" y="587" font-size="11" font-family="Arial" fill="#5d6d7e">Source: paper_hash_table.csv + similar_paper_pairs.csv</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def paper_flow_network_svg(papers: list[dict[str, str]], sim_rows: list[dict[str, str]]) -> str:
    """Directed paper network (arrow links), arranged left-to-right by year."""
    by_id = {r.get("paper_id", ""): r for r in papers}
    top = sorted(sim_rows, key=lambda r: float(r.get("similarity", 0.0)), reverse=True)[:10]

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

    width, height = 1120, 720
    x0, x1 = 130, 1020
    row_h = 58
    pos = {}
    year_nodes = {y: [n for n in nodes if int(by_id[n].get("year", 0)) == y] for y in years}
    for n in nodes:
        y = int(by_id[n].get("year", 0))
        frac = (y - min_y) / max((max_y - min_y), 1)
        x = x0 + frac * (x1 - x0)
        cohort = year_nodes.get(y, [n])
        idx = cohort.index(n)
        start_offset = -((len(cohort) - 1) * row_h / 2)
        yy = 360 + start_offset + idx * row_h
        pos[n] = (x, yy)

    axis_years = []
    for y in years:
        if y in (min_y, max_y) or (y - min_y) % 5 == 0 or len(year_nodes.get(y, [])) > 1:
            axis_years.append(y)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L10,4 L0,8 z" fill="#7f8c8d"/></marker></defs>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="24" y="34" font-size="24" font-family="Arial" font-weight="bold" fill="#17202a">Directed Paper Flow Network</text>',
        '<text x="24" y="57" font-size="13" font-family="Arial" fill="#5d6d7e">Reduced clutter: fewer links, curved arrows, and simplified timeline markers.</text>',
    ]

    for y in axis_years:
        frac = (y - min_y) / max((max_y - min_y), 1)
        x = x0 + frac * (x1 - x0)
        parts.append(f'<line x1="{x:.1f}" y1="90" x2="{x:.1f}" y2="674" stroke="#ecf0f1"/>')
        parts.append(f'<text x="{x-12:.1f}" y="103" font-size="11" font-family="Arial" fill="#7b8a8b">{y}</text>')

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
        stroke = 1.2 + 3.4 * max(0.0, min(1.0, sim))
        mx = (x1p + x2p) / 2
        curve = y1p - 26 if y2p >= y1p else y1p + 26
        parts.append(
            f'<path d="M{x1p:.1f},{y1p:.1f} Q{mx:.1f},{curve:.1f} {x2p:.1f},{y2p:.1f}" stroke="#7f8c8d" '
            f'fill="none" stroke-width="{stroke:.2f}" opacity="0.66" marker-end="url(#arrow)"/>'
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
        color = palette.get(cluster, "#566573")
        title = row.get("title", "")[:26]
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8.5" fill="{color}" stroke="#ffffff" stroke-width="1"/>')
        parts.append(f'<rect x="{x + 10:.1f}" y="{y - 11:.1f}" width="170" height="16" rx="3" fill="#ffffff" opacity="0.88"/>')
        parts.append(f'<text x="{x+14:.1f}" y="{y+1:.1f}" font-size="10" font-family="Arial" fill="#1b2631">{escape(n)}: {escape(title)}</text>')

    parts.append('<rect x="24" y="604" width="460" height="94" fill="#f8f9f9" stroke="#d5dbdb" rx="4"/>')
    parts.append(f'<text x="36" y="631" font-size="13" font-family="Arial" fill="#1b2631">Papers shown: {len(nodes)}</text>')
    parts.append(f'<text x="36" y="652" font-size="13" font-family="Arial" fill="#1b2631">Similarity arrows: {len(top)}</text>')
    parts.append('<text x="36" y="673" font-size="11" font-family="Arial" fill="#5d6d7e">Layout: x by year, y by within-year separation. Arrow thickness = similarity.</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def _split_authors(value: str) -> list[str]:
    return [p.strip() for p in re.split(r";|,| and ", value or "") if p.strip()]


def innovation_map_svg(papers: list[dict[str, str]], researchers: list[dict[str, str]]) -> str:
    """Bell Labs innovation map: researchers + domains + cross-domain bridges."""
    highlight = ["Claude Shannon", "Harry Nyquist", "John Tukey", "Richard Hamming"]

    # researcher -> domains and volume
    author_domains: dict[str, set[str]] = defaultdict(set)
    author_papers: Counter[str] = Counter()
    for row in papers:
        cluster = row.get("cluster", "unknown")
        for a in _split_authors(row.get("authors", "")):
            author_domains[a].add(cluster)
            author_papers[a] += 1

    # include highlighted + strongest contributors
    core = set(highlight)
    ranked = sorted(author_papers.items(), key=lambda kv: kv[1], reverse=True)
    for name, _ in ranked:
        if len(core) >= 18:
            break
        if len(author_domains.get(name, set())) >= 2 or author_papers[name] >= 2:
            core.add(name)

    domain_counts = Counter(r.get("cluster", "unknown") for r in papers)
    domains = [d for d, _ in domain_counts.most_common(8)]

    width, height = 1240, 780
    cx, cy = 630, 390
    dom_rad, person_rad = 175, 315

    domain_pos = {}
    for i, d in enumerate(domains):
        ang = -math.pi / 2 + 2 * math.pi * i / max(len(domains), 1)
        domain_pos[d] = (cx + dom_rad * math.cos(ang), cy + dom_rad * math.sin(ang))

    core_names = sorted(core)
    person_pos = {}
    for i, n in enumerate(core_names):
        ang = -math.pi / 2 + 2 * math.pi * i / max(len(core_names), 1)
        jitter = (i % 3 - 1) * 12
        person_pos[n] = (cx + (person_rad + jitter) * math.cos(ang), cy + (person_rad + jitter) * math.sin(ang))


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

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="24" y="34" font-size="27" font-family="Arial" font-weight="bold" fill="#17202a">Bell Labs Innovation Map</text>',
        '<text x="24" y="59" font-size="14" font-family="Arial" fill="#5d6d7e">Researchers connected to research domains; multi-domain people are cross-domain bridges.</text>',
    ]

    # bridge edges first (lighter)
    for name in core_names:
        doms = sorted(author_domains.get(name, set()), key=lambda d: domain_counts.get(d, 0), reverse=True)
        for d in doms:
            if d not in domain_pos:
                continue
            x1, y1 = person_pos[name]
            x2, y2 = domain_pos[d]
            is_bridge = len(doms) >= 2
            opacity = 0.52 if is_bridge else 0.25
            width_edge = 2.2 if is_bridge else 1.1
            parts.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="#95a5a6" stroke-width="{width_edge:.1f}" opacity="{opacity:.2f}"/>'
            )

    # domain nodes
    for d in domains:
        x, y = domain_pos[d]
        color = cluster_colors.get(d, "#7f8c8d")
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="28" fill="{color}" opacity="0.95"/>')
        parts.append(f'<text x="{x:.1f}" y="{y+4:.1f}" text-anchor="middle" font-size="10" font-family="Arial" fill="#ffffff">{escape(d.replace("_", " "))}</text>')

    # people nodes
    for name in core_names:
        x, y = person_pos[name]
        papers_n = author_papers.get(name, 1)
        dom_n = len(author_domains.get(name, set()))
        is_highlight = name in highlight
        ring = '#1b2631' if is_highlight else '#d5dbdb'
        fill = '#fef9e7' if is_highlight else '#f8f9f9'
        radius = 13 if is_highlight else 10
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{fill}" stroke="{ring}" stroke-width="2"/>')
        if dom_n >= 2:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius+4}" fill="none" stroke="#5dade2" stroke-width="1.5" stroke-dasharray="3 2"/>')
        label = f"{name} ({papers_n}p/{dom_n}d)"
        parts.append(f'<rect x="{x+12:.1f}" y="{y-12:.1f}" width="190" height="17" rx="3" fill="#ffffff" opacity="0.9"/>')
        parts.append(f'<text x="{x+16:.1f}" y="{y+0.5:.1f}" font-size="10" font-family="Arial" fill="#1b2631">{escape(label)}</text>')

    bridge_count = sum(1 for n in core_names if len(author_domains.get(n, set())) >= 2)
    parts.append('<rect x="24" y="640" width="620" height="116" rx="4" fill="#f8f9f9" stroke="#d5dbdb"/>')
    parts.append(f'<text x="38" y="667" font-size="13" font-family="Arial" fill="#1b2631">Researchers shown: {len(core_names)} | Domains shown: {len(domains)} | Cross-domain bridges: {bridge_count}</text>')
    parts.append('<text x="38" y="688" font-size="12" font-family="Arial" fill="#5d6d7e">Dashed outer ring = cross-domain researcher. Thicker links indicate bridge-like domain connections.</text>')
    parts.append('<text x="38" y="709" font-size="12" font-family="Arial" fill="#5d6d7e">Highlighted figures: Shannon, Nyquist, Tukey, Hamming.</text>')
    parts.append('<text x="38" y="730" font-size="11" font-family="Arial" fill="#5d6d7e">Source: papers.csv + researcher_profiles.csv.</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    papers = read_csv(DATA / "papers.csv")
    hashes = read_csv(DATA / "paper_hash_table.csv")
    sim = read_csv(DATA / "similar_paper_pairs.csv")
    researchers = read_csv(DATA / "researcher_profiles.csv")

    save(OUT / "fig14_cluster_distribution.svg", cluster_distribution_svg(papers))
    save(OUT / "fig15_hash_similarity_graph.svg", hash_similarity_svg(hashes, sim))
    save(OUT / "fig16_paper_flow_network.svg", paper_flow_network_svg(papers, sim))
    save(OUT / "fig17_bell_labs_innovation_map.svg", innovation_map_svg(papers, researchers))

    print(f"Saved: {OUT / 'fig14_cluster_distribution.svg'}")
    print(f"Saved: {OUT / 'fig15_hash_similarity_graph.svg'}")
    print(f"Saved: {OUT / 'fig16_paper_flow_network.svg'}")
    print(f"Saved: {OUT / 'fig17_bell_labs_innovation_map.svg'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
