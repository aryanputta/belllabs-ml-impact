import hashlib
import json
import warnings
warnings.filterwarnings("ignore")

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering


BASE = Path(__file__).resolve().parent.parent.parent


def paper_fingerprint(row) -> str:
    text = " ".join([
        str(row.get("title", "")),
        str(row.get("keywords", "")),
        str(row.get("cluster", "")),
        str(row.get("year", "")),
    ]).lower().strip()
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def minhash_signature(text: str, n_hashes: int = 64) -> np.ndarray:
    words = set(text.lower().split())
    sig = np.full(n_hashes, np.inf)
    for word in words:
        for i in range(n_hashes):
            h = int(hashlib.md5(f"{word}_{i}".encode()).hexdigest(), 16) % (2**32)
            if h < sig[i]:
                sig[i] = h
    return sig


def jaccard_from_minhash(sig_a: np.ndarray, sig_b: np.ndarray) -> float:
    return float((sig_a == sig_b).mean())


def build_similarity_matrix(df: pd.DataFrame, method: str = "cosine") -> np.ndarray:
    corpus = (
        df["title"].fillna("") + " " +
        df["abstract"].fillna("") + " " +
        df["keywords"].fillna("")
    ).str.lower()

    vec = TfidfVectorizer(max_features=200, stop_words="english",
                          ngram_range=(1, 2), sublinear_tf=True, min_df=1)
    X = vec.fit_transform(corpus).toarray()

    if method == "cosine":
        return cosine_similarity(X)
    elif method == "minhash":
        sigs = [minhash_signature(text) for text in corpus]
        n = len(sigs)
        sim = np.eye(n)
        for i in range(n):
            for j in range(i + 1, n):
                s = jaccard_from_minhash(sigs[i], sigs[j])
                sim[i, j] = sim[j, i] = s
        return sim
    else:
        raise ValueError(f"Unknown method: {method}")


def find_similar_papers(df: pd.DataFrame, paper_id: str,
                        sim_matrix: np.ndarray, top_k: int = 5) -> pd.DataFrame:
    idx = df[df["paper_id"] == paper_id].index
    if len(idx) == 0:
        return pd.DataFrame()
    i = df.index.get_loc(idx[0])
    scores = sim_matrix[i].copy()
    scores[i] = -1
    top_idx = np.argsort(scores)[::-1][:top_k]

    results = df.iloc[top_idx][["paper_id", "title", "authors", "year",
                                 "cluster", "citations"]].copy()
    results["similarity"] = scores[top_idx].round(4)
    return results.reset_index(drop=True)


def cluster_papers_by_similarity(df: pd.DataFrame, sim_matrix: np.ndarray,
                                  n_clusters: int = 8) -> np.ndarray:
    distance = 1 - np.clip(sim_matrix, 0, 1)
    hc = AgglomerativeClustering(n_clusters=n_clusters, metric="precomputed",
                                  linkage="average")
    return hc.fit_predict(distance)


def build_paper_hash_table(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, row in df.iterrows():
        fp = paper_fingerprint(row)
        corpus = (str(row.get("title","")) + " " +
                  str(row.get("abstract","")) + " " +
                  str(row.get("keywords",""))).lower()
        sig = minhash_signature(corpus, n_hashes=32)
        records.append({
            "paper_id":      row["paper_id"],
            "fingerprint":   fp,
            "minhash_lsb":   int(sig[:4].min()),
            "title":         row["title"],
            "cluster":       row["cluster"],
            "year":          row["year"],
            "citations":     row["citations"],
        })
    return pd.DataFrame(records)


def near_duplicate_pairs(df: pd.DataFrame, sim_matrix: np.ndarray,
                          threshold: float = 0.70) -> list:
    pairs = []
    n = len(df)
    for i in range(n):
        for j in range(i + 1, n):
            if sim_matrix[i, j] >= threshold:
                pairs.append({
                    "paper_a": df.iloc[i]["paper_id"],
                    "title_a": df.iloc[i]["title"][:50],
                    "paper_b": df.iloc[j]["paper_id"],
                    "title_b": df.iloc[j]["title"][:50],
                    "similarity": round(float(sim_matrix[i, j]), 4),
                    "same_cluster": df.iloc[i]["cluster"] == df.iloc[j]["cluster"],
                })
    return sorted(pairs, key=lambda x: -x["similarity"])


def run(base: Path = BASE) -> dict:
    df = pd.read_csv(base / "data/processed/papers.csv")

    print("Building cosine similarity matrix...")
    sim = build_similarity_matrix(df, method="cosine")

    print("Building paper hash table (MinHash fingerprints)...")
    hash_table = build_paper_hash_table(df)

    print("Clustering papers by similarity...")
    sim_cluster_labels = cluster_papers_by_similarity(df, sim)
    df_out = df.copy()
    df_out["similarity_cluster"] = sim_cluster_labels

    print("Finding near-duplicate / highly similar pairs...")
    pairs = near_duplicate_pairs(df, sim, threshold=0.55)

    print(f"\nTop 10 most similar paper pairs (cosine sim >= 0.55):")
    for p in pairs[:10]:
        print(f"  [{p['similarity']:.3f}]  '{p['title_a'][:40]}...'")
        print(f"          vs  '{p['title_b'][:40]}...'")
        print(f"          same_cluster={p['same_cluster']}")

    print("\nSimilar papers to Shannon 1948:")
    shannon_id = df[df["title"].str.contains("Mathematical Theory", na=False)].iloc[0]["paper_id"]
    similar = find_similar_papers(df, shannon_id, sim, top_k=5)
    print(similar[["title", "cluster", "similarity"]].to_string(index=False))

    out = base / "data/processed"
    hash_table.to_csv(out / "paper_hash_table.csv", index=False)
    df_out.to_csv(out / "papers_with_sim_clusters.csv", index=False)

    sim_df = pd.DataFrame(sim, index=df["paper_id"], columns=df["paper_id"])
    sim_df.to_csv(out / "paper_similarity_matrix.csv")

    if pairs:
        pd.DataFrame(pairs).to_csv(out / "similar_paper_pairs.csv", index=False)

    print(f"\nSaved: paper_hash_table.csv, paper_similarity_matrix.csv, similar_paper_pairs.csv")
    return {"sim": sim, "hash_table": hash_table, "pairs": pairs, "df": df_out}


if __name__ == "__main__":
    run()
