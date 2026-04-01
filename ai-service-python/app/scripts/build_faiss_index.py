import json
from pathlib import Path
import faiss
import numpy as np

from app.services.recipe_data import load_recipes
from app.services.embeddings import build_embedding_text, embed_texts

INDEX_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
INDEX_DIR.mkdir(parents=True, exist_ok=True)

INDEX_PATH = INDEX_DIR / "recipes.faiss"
META_PATH = INDEX_DIR / "recipes_faiss_meta.json"

recipes = load_recipes()
texts = [build_embedding_text(r) for r in recipes]
vectors = embed_texts(texts).astype("float32")

faiss.normalize_L2(vectors)
index = faiss.IndexFlatIP(vectors.shape[1])
index.add(vectors)

faiss.write_index(index, str(INDEX_PATH))

with open(META_PATH, "w", encoding="utf-8") as f:
    json.dump(recipes, f, ensure_ascii=False, indent=2)

print("Saved index:", INDEX_PATH)
print("Saved meta:", META_PATH)
print("Total recipes indexed:", index.ntotal)
print("Vector dimension:", vectors.shape[1])