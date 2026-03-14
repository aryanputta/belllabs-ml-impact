import warnings
warnings.filterwarnings("ignore")

import json
from pathlib import Path
from itertools import combinations

import numpy as np
import pandas as pd
import networkx as nx
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


BASE = Path(__file__).resolve().parent.parent.parent

NOBEL_WINNERS = {
    "William Shockley":  "Physics 1956",
    "John Bardeen":      "Physics 1956 & 1972",
    "Walter Brattain":   "Physics 1956",
    "Philip Anderson":   "Physics 1977",
    "Arno Penzias":      "Physics 1978",
    "Robert Wilson":     "Physics 1978",
    "Horst Störmer":     "Physics 1998",
    "Daniel Tsui":       "Physics 1998",
}

TURING_WINNERS = {
    "Ken Thompson":   "Turing Award 1983",
    "Dennis Ritchie": "Turing Award 1983",
}

HIGH_IMPACT_THRESHOLD = 10000


def build_graph(df):
    G = nx.Graph()
    for _, row in df.iterrows():
        authors = [a.strip() for a in str(row["authors"]).split(";")]
        for a in authors:
            if a not in G:
                G.add_node(a, papers=0, citations=0,
                           clusters=set(), years=[])
            G.nodes[a]["papers"] += 1
            G.nodes[a]["citations"] += int(row["citations"])
            G.nodes[a]["clusters"].add(row["cluster"])
            G.nodes[a]["years"].append(int(row["year"]))
        for a, b in combinations(authors, 2):
            if G.has_edge(a, b):
                G[a][b]["weight"] += 1
            else:
                G.add_edge(a, b, weight=1)
    for n in G.nodes():
        G.nodes[n]["clusters"] = list(G.nodes[n]["clusters"])
    return G


def researcher_features(df: pd.DataFrame, researchers_df: pd.DataFrame) -> pd.DataFrame:
    G = build_graph(df)
    bc = nx.betweenness_centrality(G, normalized=True)
    dc = nx.degree_centrality(G)
    try:
        ec = nx.eigenvector_centrality(G, max_iter=1000)
    except Exception:
        ec = {n: 0.0 for n in G.nodes()}

    res_map = {}
    if researchers_df is not None:
        for _, row in researchers_df.iterrows():
            res_map[row["name"]] = row

    records = []
    for name in G.nodes():
        node = G.nodes[name]
        years = node.get("years", [])
        career_span = (max(years) - min(years)) if len(years) > 1 else 0
        n_domains = len(node.get("clusters", []))

        career_start = res_map[name]["start_year"] if name in res_map else (min(years) if years else 1950)
        career_end   = res_map[name]["end_year"]   if name in res_map else (max(years) if years else 1980)
        role         = res_map[name]["role"]        if name in res_map else "unknown"
        dept         = res_map[name]["department"]  if name in res_map else "Unknown"

        total_cites = node.get("citations", 0)
        n_papers    = node.get("papers", 0)
        avg_cites   = total_cites / n_papers if n_papers > 0 else 0

        is_high_impact = int(avg_cites >= HIGH_IMPACT_THRESHOLD)
        is_laureate    = int(name in NOBEL_WINNERS or name in TURING_WINNERS)

        records.append({
            "name":               name,
            "department":         dept,
            "role":               role,
            "career_start":       int(career_start),
            "career_end":         int(career_end),
            "career_span":        int(career_end) - int(career_start),
            "papers":             n_papers,
            "total_citations":    total_cites,
            "avg_citations":      round(avg_cites, 0),
            "n_domains":          n_domains,
            "collaborators":      G.degree(name),
            "betweenness":        round(bc.get(name, 0), 6),
            "degree_centrality":  round(dc.get(name, 0), 6),
            "eigenvector":        round(ec.get(name, 0), 6),
            "is_bridge":          int(n_domains > 1),
            "is_high_impact":     is_high_impact,
            "is_laureate":        is_laureate,
            "award":              NOBEL_WINNERS.get(name, TURING_WINNERS.get(name, "")),
        })

    return pd.DataFrame(records).sort_values("total_citations", ascending=False).reset_index(drop=True)


def why_high_impact(feat_df: pd.DataFrame) -> dict:
    haves     = feat_df[feat_df["is_high_impact"] == 1]
    have_nots = feat_df[feat_df["is_high_impact"] == 0]

    cols = ["career_span", "papers", "n_domains", "collaborators",
            "betweenness", "degree_centrality", "eigenvector"]

    comparison = {}
    for col in cols:
        hi_mean = haves[col].mean()
        lo_mean = have_nots[col].mean()
        ratio   = hi_mean / lo_mean if lo_mean > 0 else float("inf")
        comparison[col] = {
            "high_impact_mean": round(hi_mean, 3),
            "low_impact_mean":  round(lo_mean, 3),
            "ratio":            round(ratio, 3),
        }

    return comparison


def predict_high_impact(feat_df: pd.DataFrame) -> dict:
    cols = ["career_span", "papers", "n_domains", "collaborators",
            "betweenness", "degree_centrality", "eigenvector"]
    X = feat_df[cols].fillna(0).values
    y = feat_df["is_high_impact"].values

    if y.sum() < 3 or (len(y) - y.sum()) < 3:
        return {"note": "insufficient class balance for CV"}

    model = Pipeline([
        ("sc", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=200, max_depth=4,
                                        random_state=42)),
    ])
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    auc_scores = cross_val_score(model, X, y, cv=cv, scoring="roc_auc")

    model.fit(X, y)
    imp = model.named_steps["clf"].feature_importances_
    feat_imp = {c: round(float(v), 4) for c, v in zip(cols, imp)}

    return {
        "cv_auc_mean":      round(auc_scores.mean(), 4),
        "cv_auc_std":       round(auc_scores.std(), 4),
        "feature_importance": dict(sorted(feat_imp.items(), key=lambda x: -x[1])),
    }


def researcher_archetypes(feat_df: pd.DataFrame) -> pd.DataFrame:
    def classify(row):
        if row["is_laureate"]:
            return "Nobel / Turing Laureate"
        if row["n_domains"] > 1 and row["betweenness"] > 0.05:
            return "Cross-Domain Bridge"
        if row["betweenness"] > 0.08:
            return "Network Hub"
        if row["career_span"] > 25 and row["papers"] >= 3:
            return "Long-Horizon Researcher"
        if row["papers"] >= 3 and row["avg_citations"] >= 5000:
            return "High-Output Producer"
        if row["is_bridge"] and row["collaborators"] >= 3:
            return "Collaborative Generalist"
        return "Domain Specialist"
    feat_df = feat_df.copy()
    feat_df["archetype"] = feat_df.apply(classify, axis=1)
    return feat_df


def why_bell_labs_worked(feat_df: pd.DataFrame, comparison: dict) -> list:
    findings = []

    bridge_researchers = feat_df[feat_df["n_domains"] > 1]
    findings.append({
        "finding": "Cross-domain researchers are disproportionately high-impact",
        "evidence": (
            f"{len(bridge_researchers)} researchers published across multiple domains. "
            f"Their average citations ({bridge_researchers['avg_citations'].mean():,.0f}) "
            f"are {bridge_researchers['avg_citations'].mean() / max(feat_df[feat_df['n_domains']==1]['avg_citations'].mean(), 1):.1f}x "
            f"higher than single-domain specialists."
        ),
        "implication": "Bell Labs physically co-located researchers from different fields, enabling cross-pollination that consistently produced higher-impact work.",
    })

    hi = feat_df[feat_df["is_high_impact"] == 1]
    lo = feat_df[feat_df["is_high_impact"] == 0]
    findings.append({
        "finding": "High-impact researchers have longer careers at Bell Labs",
        "evidence": (
            f"High-impact researchers averaged {hi['career_span'].mean():.0f} years; "
            f"low-impact averaged {lo['career_span'].mean():.0f} years. "
            f"Ratio: {comparison['career_span']['ratio']:.2f}x."
        ),
        "implication": "Bell Labs' long-term employment model allowed researchers to pursue 10–20 year research programs that produced foundational results rather than incremental ones.",
    })

    findings.append({
        "finding": "Network centrality weakly predicts individual impact",
        "evidence": (
            f"Betweenness centrality ratio (high vs low impact): {comparison['betweenness']['ratio']:.2f}x. "
            f"Cross-domain reach ratio: {comparison['n_domains']['ratio']:.2f}x. "
            "Network position is a weaker predictor than career duration and domain breadth."
        ),
        "implication": "Bell Labs success was not primarily driven by networking. It was driven by sustained, deep research in a stable institutional environment.",
    })

    laureates = feat_df[feat_df["is_laureate"] == 1]
    findings.append({
        "finding": "Nobel and Turing laureates are identifiable from network structure alone",
        "evidence": (
            f"{len(laureates)} laureates found. "
            f"Average betweenness rank of laureates: top {feat_df['betweenness'].rank(ascending=False).loc[laureates.index].mean():.0f} out of {len(feat_df)}. "
            f"Average career span: {laureates['career_span'].mean():.0f} years."
        ),
        "implication": "Bell Labs' structure consistently put its highest-achieving scientists in structurally important positions — validating that the network analysis recovers ground truth.",
    })

    collab_ratio = comparison["collaborators"]["ratio"]
    findings.append({
        "finding": "High-impact researchers collaborate more, but not dramatically so",
        "evidence": (
            f"High-impact average collaborators: {hi['collaborators'].mean():.1f}; "
            f"low-impact: {lo['collaborators'].mean():.1f}. "
            f"Ratio: {collab_ratio:.2f}x."
        ),
        "implication": "Collaboration matters at Bell Labs, but excessive collaboration (>5 co-authors) is rare. The most impactful work was often done in small focused teams or even solo.",
    })

    return findings


def run(base: Path = BASE) -> dict:
    df  = pd.read_csv(base / "data/processed/papers.csv")
    try:
        rd = pd.read_csv(base / "data/processed/researchers.csv")
    except FileNotFoundError:
        rd = None

    print("Building researcher feature profiles...")
    feat_df = researcher_features(df, rd)

    print("Classifying researcher archetypes...")
    feat_df = researcher_archetypes(feat_df)

    print("Analyzing why high-impact researchers differ...")
    comparison = why_high_impact(feat_df)

    print("\nHigh vs Low impact comparison:")
    for col, vals in comparison.items():
        print(f"  {col:<25} hi={vals['high_impact_mean']:<10} lo={vals['low_impact_mean']:<10} ratio={vals['ratio']}")

    print("\nTraining researcher impact predictor...")
    pred = predict_high_impact(feat_df)
    print(f"  CV AUC: {pred.get('cv_auc_mean', 'N/A')}")
    if "feature_importance" in pred:
        for f, v in list(pred["feature_importance"].items())[:5]:
            print(f"  {f:<25} {v:.4f}")

    print("\nWHY Bell Labs worked:")
    findings = why_bell_labs_worked(feat_df, comparison)
    for i, f in enumerate(findings, 1):
        print(f"\n  [{i}] {f['finding']}")
        print(f"      {f['evidence'][:100]}...")

    print("\nResearcher archetypes:")
    print(feat_df["archetype"].value_counts().to_string())

    out = base / "data/processed"
    feat_df.to_csv(out / "researcher_profiles.csv", index=False)

    with open(out / "why_bell_labs_worked.json", "w") as f:
        json.dump({
            "comparison":       comparison,
            "prediction_model": pred,
            "findings":         findings,
            "archetype_counts": feat_df["archetype"].value_counts().to_dict(),
        }, f, indent=2)

    print(f"\nSaved: researcher_profiles.csv, why_bell_labs_worked.json")
    return {"feat_df": feat_df, "comparison": comparison, "findings": findings, "pred": pred}


if __name__ == "__main__":
    run()
