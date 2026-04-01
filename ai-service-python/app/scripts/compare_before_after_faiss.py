import json
from pathlib import Path

import faiss

from app.models.schemas import RecipeGenerateRequest
from app.services.embeddings import embed_texts
from app.services.recipe_data import load_recipes
from app.services.retriever import calculate_recipe_score

INDEX_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
INDEX_PATH = INDEX_DIR / "recipes.faiss"
META_PATH = INDEX_DIR / "recipes_faiss_meta.json"


def lexical_only(request: RecipeGenerateRequest, top_k: int = 3):
    recipes = load_recipes()
    scored = [calculate_recipe_score(r, request) for r in recipes]
    scored.sort(
        key=lambda x: (
            x["lexical_score"],
            len(x.get("matched_input_ingredients", [])),
            -len(x.get("extra_major_ingredients", [])),
        ),
        reverse=True,
    )
    return scored[:top_k]


def semantic_faiss(request: RecipeGenerateRequest, top_k: int = 3):
    index = faiss.read_index(str(INDEX_PATH))
    with open(META_PATH, "r", encoding="utf-8") as f:
        recipes = json.load(f)

    query_text = " | ".join([
        " ".join(request.ingredients),
        request.cuisine or "",
    ]).strip()

    q = embed_texts([query_text]).astype("float32")
    faiss.normalize_L2(q)

    scores, ids = index.search(q, top_k)

    results = []
    for score, idx in zip(scores[0], ids[0]):
        if idx == -1:
            continue
        recipe = recipes[idx]
        results.append({
            "id": recipe.get("id"),
            "title": recipe.get("title"),
            "cuisine": recipe.get("cuisine"),
            "semantic_score": float(score),
        })
    return results


request = RecipeGenerateRequest(
    ingredients=["rice", "tomato", "onion"],
    cuisine="Indian",
    prep_time=45,
    servings=2,
    skill_level="beginner",
)

print("\n=== BEFORE FAISS (Lexical only) ===")
for i, r in enumerate(lexical_only(request), 1):
    print(i, r.get("id"), r.get("title"), "lexical_score=", r.get("lexical_score"))

print("\n=== AFTER FAISS (Semantic) ===")
for i, r in enumerate(semantic_faiss(request), 1):
    print(i, r.get("id"), r.get("title"), "semantic_score=", r.get("semantic_score"))