"""Author co-authorship network construction and centrality exports."""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import networkx as nx
import pandas as pd

BASE = Path(__file__).resolve().parent.parent.parent


def build_author_graph(df: pd.DataFrame) -> nx.Graph:
    g = nx.Graph()
    for _, row in df.iterrows():
        authors = [a.strip() for a in str(row["authors"]).split(";") if a.strip()]
        for a in authors:
            g.add_node(a)
        for a, b in combinations(authors, 2):
            g.add_edge(a, b, weight=g.get_edge_data(a, b, {"weight": 0})["weight"] + 1)
    return g


def graph_metrics(g: nx.Graph) -> pd.DataFrame:
    bc = nx.betweenness_centrality(g) if g.number_of_nodes() > 1 else {}
    dc = nx.degree_centrality(g) if g.number_of_nodes() > 1 else {}
    try:
        ec = nx.eigenvector_centrality(g, max_iter=1000) if g.number_of_nodes() > 1 else {}
    except Exception:
        ec = {n: 0.0 for n in g.nodes}

    rows = []
    for n in g.nodes:
        rows.append(
            {
                "author": n,
                "degree": int(g.degree(n)),
                "betweenness": round(float(bc.get(n, 0.0)), 6),
                "degree_centrality": round(float(dc.get(n, 0.0)), 6),
                "eigenvector": round(float(ec.get(n, 0.0)), 6),
            }
        )
    return pd.DataFrame(rows).sort_values(["betweenness", "degree"], ascending=False)


def run(base: Path = BASE) -> dict:
    df = pd.read_csv(base / "data/processed/papers.csv")
    g = build_author_graph(df)
    metrics = graph_metrics(g)

    out_dir = base / "data/processed"
    metrics.to_csv(out_dir / "author_network_metrics.csv", index=False)

    meta = {
        "nodes": g.number_of_nodes(),
        "edges": g.number_of_edges(),
        "density": round(float(nx.density(g)) if g.number_of_nodes() > 1 else 0.0, 6),
    }
    with open(out_dir / "author_network_summary.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Graph nodes={meta['nodes']} edges={meta['edges']} density={meta['density']}")
    print(f"Saved: {out_dir / 'author_network_metrics.csv'}")
    return {"metrics": metrics, "summary": meta}


if __name__ == "__main__":
    run()
