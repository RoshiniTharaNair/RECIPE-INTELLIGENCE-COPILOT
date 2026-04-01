import json
from pathlib import Path
import faiss
import numpy as np

from app.services.embeddings import embed_texts

INDEX_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
INDEX_PATH = INDEX_DIR / "recipes.faiss"
META_PATH = INDEX_DIR / "recipes_faiss_meta.json"

index = faiss.read_index(str(INDEX_PATH))

with open(META_PATH, "r", encoding="utf-8") as f:
    recipes = json.load(f)

query = "quick tomato rice onion indian"
q = embed_texts([query]).astype("float32")
faiss.normalize_L2(q)

scores, ids = index.search(q, 3)

print("QUERY:", query)
for rank, idx in enumerate(ids[0], 1):
    recipe = recipes[idx]
    print(rank, recipe.get("id"), recipe.get("title"), recipe.get("cuisine"))