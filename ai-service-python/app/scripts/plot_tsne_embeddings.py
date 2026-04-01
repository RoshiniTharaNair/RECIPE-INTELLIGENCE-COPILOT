import json
from pathlib import Path

import faiss
import matplotlib.pyplot as plt
import numpy as np
from sklearn.manifold import TSNE

from app.services.embeddings import embed_texts

INDEX_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
META_PATH = INDEX_DIR / "recipes_faiss_meta.json"

with open(META_PATH, "r", encoding="utf-8") as f:
    recipes = json.load(f)

sample_recipes = recipes[:60]

recipe_texts = []
recipe_labels = []
for r in sample_recipes:
    text = " | ".join([
        r.get("title", ""),
        r.get("description", ""),
        r.get("cuisine", ""),
        " ".join(r.get("ingredients", [])),
    ])
    recipe_texts.append(text)
    recipe_labels.append(r.get("title", "recipe"))

query_before = "rice tomato onion"
query_after = "quick tomato rice onion indian"

all_texts = recipe_texts + [query_before, query_after]
vectors = embed_texts(all_texts).astype("float32")
faiss.normalize_L2(vectors)

tsne = TSNE(n_components=2, random_state=42, perplexity=10)
points = tsne.fit_transform(vectors)

recipe_points = points[:-2]
before_point = points[-2]
after_point = points[-1]

plt.figure(figsize=(10, 8))
plt.scatter(recipe_points[:, 0], recipe_points[:, 1], alpha=0.6)
plt.scatter(before_point[0], before_point[1], marker="X", s=200, label="Before FAISS query")
plt.scatter(after_point[0], after_point[1], marker="D", s=180, label="After FAISS query")

for i in range(min(12, len(recipe_points))):
    plt.annotate(recipe_labels[i], (recipe_points[i, 0], recipe_points[i, 1]), fontsize=8)

plt.title("t-SNE of Recipe Embeddings with Queries")
plt.xlabel("t-SNE 1")
plt.ylabel("t-SNE 2")
plt.legend()
plt.tight_layout()
plt.show()