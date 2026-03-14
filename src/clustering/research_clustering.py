"""Cluster Bell Labs papers by semantic similarity and compare with curated domains."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import adjusted_rand_score

BASE = Path(__file__).resolve().parent.parent.parent


def run(base: Path = BASE, n_clusters: int = 8) -> dict:
    df = pd.read_csv(base / "data/processed/papers.csv")
    corpus = (df["title"].fillna("") + " " + df["abstract"].fillna("") + " " + df["keywords"].fillna("")).str.lower()

    vec = TfidfVectorizer(max_features=500, ngram_range=(1, 2), stop_words="english")
    X = vec.fit_transform(corpus)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
    labels = kmeans.fit_predict(X)
    df_out = df.copy()
    df_out["kmeans_cluster"] = labels

    ari = adjusted_rand_score(df_out["cluster"].astype(str), df_out["kmeans_cluster"].astype(str))

    out = base / "data/processed"
    df_out.to_csv(out / "papers_with_kmeans_clusters.csv", index=False)

    print(f"Adjusted Rand Index vs curated domain labels: {ari:.4f}")
    print(f"Saved: {out / 'papers_with_kmeans_clusters.csv'}")
    return {"ari": round(float(ari), 4), "df": df_out}


if __name__ == "__main__":
    run()
