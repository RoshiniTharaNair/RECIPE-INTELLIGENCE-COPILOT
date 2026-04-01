import json
from pathlib import Path
from typing import List

import faiss

from app.models.schemas import RecipeGenerateRequest
from app.services.embeddings import embed_texts
from app.services.ingredient_normalizer import normalize_ingredient_list
from app.services.ingredient_knowledge import (
    canonicalize_ingredient_list,
    normalize_text,
)
from app.services.ingredient_pair_rules import compute_pair_bonus

ALLOWED_PANTRY_BASICS = {
    "salt",
    "water",
    "oil",
    "butter",
    "pepper",
    "garlic",
    "ginger",
    "sugar",
    "flour",
    "olive oil",
    "vegetable oil",
}

MAJOR_INGREDIENT_KEYWORDS = {
    "chicken",
    "egg",
    "eggs",
    "fish",
    "mutton",
    "beef",
    "pork",
    "prawn",
    "shrimp",
    "lamb",
    "bacon",
    "ham",
    "turkey",
    "salmon",
    "tuna",
    "haddock",
}

INDEX_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
INDEX_PATH = INDEX_DIR / "recipes.faiss"
META_PATH = INDEX_DIR / "recipes_faiss_meta.json"

_FAISS_INDEX = None
_FAISS_RECIPES = None


def faiss_available() -> bool:
    return INDEX_PATH.exists() and META_PATH.exists()


def warmup_retriever():
    if faiss_available():
        load_faiss_resources()


def load_faiss_resources():
    global _FAISS_INDEX, _FAISS_RECIPES

    if _FAISS_INDEX is None or _FAISS_RECIPES is None:
        _FAISS_INDEX = faiss.read_index(str(INDEX_PATH))
        with open(META_PATH, "r", encoding="utf-8") as f:
            _FAISS_RECIPES = json.load(f)

    return _FAISS_INDEX, _FAISS_RECIPES


def user_allows_major_ingredients(input_ingredients: List[str]) -> bool:
    input_text = " ".join(input_ingredients)
    return any(word in input_text for word in MAJOR_INGREDIENT_KEYWORDS)


def recipe_has_disallowed_major_ingredient(
    recipe_ingredients: List[str],
    input_ingredients: List[str],
) -> bool:
    if user_allows_major_ingredients(input_ingredients):
        return False

    for recipe_ing in recipe_ingredients:
        if any(word in recipe_ing for word in MAJOR_INGREDIENT_KEYWORDS):
            return True

    return False


def count_disallowed_major_ingredients(
    recipe_ingredients: List[str],
    input_ingredients: List[str],
) -> int:
    if user_allows_major_ingredients(input_ingredients):
        return 0

    count = 0
    for recipe_ing in recipe_ingredients:
        if any(word in recipe_ing for word in MAJOR_INGREDIENT_KEYWORDS):
            count += 1
    return count


def cuisine_similarity_bonus(request_cuisine: str | None, recipe_cuisine: str | None) -> float:
    if not request_cuisine or not recipe_cuisine:
        return 0.0

    req = normalize_text(request_cuisine)
    rec = normalize_text(recipe_cuisine)

    if req == rec:
        return 0.2
    if req in rec or rec in req:
        return 0.12
    return 0.0


def ingredient_intent_bonus(input_ingredients, matched_ingredients, recipe_ingredients) -> float:
    bonus = 0.0
    input_set = set(canonicalize_ingredient_list(input_ingredients))
    recipe_set = set(canonicalize_ingredient_list(recipe_ingredients))

    if "rice" in input_set and "rice" in recipe_set:
        bonus += 0.12
    if "pasta" in input_set and "pasta" in recipe_set:
        bonus += 0.12
    if "bread" in input_set and "bread" in recipe_set:
        bonus += 0.08
    if len(matched_ingredients) >= max(2, len(input_set) - 1):
        bonus += 0.08
    return bonus


def calculate_recipe_score(recipe: dict, request: RecipeGenerateRequest) -> dict:
    input_ingredients = [normalize_text(i) for i in request.ingredients]
    recipe_ingredients = [
        normalize_text(i)
        for i in recipe.get("ingredients_clean", recipe.get("ingredients", []))
    ]

    user_canonical = canonicalize_ingredient_list(input_ingredients)
    recipe_canonical = canonicalize_ingredient_list(recipe_ingredients)

    title_text = normalize_text(recipe.get("title", ""))
    description_text = normalize_text(recipe.get("description", ""))

    title_desc_canonical = canonicalize_ingredient_list([title_text, description_text])
    recipe_concepts = list(dict.fromkeys(recipe_canonical + title_desc_canonical))

    matched = [u for u in user_canonical if u in recipe_concepts]
    extras = [r for r in recipe_concepts if r not in user_canonical]

    disallowed_major_count = count_disallowed_major_ingredients(
        recipe_ingredients,
        input_ingredients,
    )

    input_count = max(len(user_canonical), 1)
    matched_count = len(matched)

    base_score = matched_count / input_count
    full_match_bonus = 0.12 if matched_count == input_count else 0.0
    near_match_bonus = 0.05 if matched_count >= max(2, input_count - 1) else 0.0
    extra_penalty = 0.12 * len(extras)
    major_penalty = 0.25 * disallowed_major_count
    cuisine_bonus = cuisine_similarity_bonus(request.cuisine, recipe.get("cuisine"))
    intent_bonus = ingredient_intent_bonus(input_ingredients, matched, recipe_ingredients)

    pair_bonus = compute_pair_bonus(
        user_canonical,
        recipe_concepts,
        extra_major_count=len(extras),
    )

    prep_bonus = 0.0
    if request.prep_time is not None and recipe.get("total_time_mins") is not None:
        if recipe["total_time_mins"] <= request.prep_time:
            prep_bonus = 0.1

    rating_bonus = 0.0
    if recipe.get("rating") is not None:
        try:
            rating_bonus = min(float(recipe["rating"]) / 50.0, 0.1)
        except Exception:
            rating_bonus = 0.0

    popularity_bonus = 0.0
    if recipe.get("popularity") is not None:
        try:
            popularity = int(recipe["popularity"])
            if popularity >= 10000:
                popularity_bonus = 0.05
            elif popularity >= 1000:
                popularity_bonus = 0.03
        except Exception:
            pass

    lexical_score = round(
        max(
            0.0,
            base_score
            + full_match_bonus
            + near_match_bonus
            + intent_bonus
            + pair_bonus
            - extra_penalty
            - major_penalty
            + cuisine_bonus
            + prep_bonus
            + rating_bonus
            + popularity_bonus,
        ),
        3,
    )

    return {
        **recipe,
        "lexical_score": lexical_score,
        "matched_input_ingredients": matched,
        "extra_major_ingredients": extras,
        "extra_major_count": len(extras),
        "disallowed_major_count": disallowed_major_count,
        "pair_bonus": pair_bonus,
    }


def build_why_chosen(recipe: dict) -> str:
    matched = recipe.get("matched_input_ingredients", [])
    extras = recipe.get("extra_major_ingredients", [])
    lexical = recipe.get("lexical_score", 0.0)
    semantic = recipe.get("semantic_score", 0.0)
    hybrid = recipe.get("match_score", 0.0)
    disallowed = recipe.get("disallowed_major_count", 0)
    pair_bonus = recipe.get("pair_bonus", 0.0)

    return (
        f"Matched {len(matched)} ingredient(s); "
        f"needs {len(extras)} extra major ingredient(s); "
        f"disallowed major ingredients {disallowed}; "
        f"pair bonus {round(float(pair_bonus), 3)}; "
        f"lexical {round(float(lexical), 3)}, "
        f"semantic {round(float(semantic), 3)}, "
        f"hybrid {round(float(hybrid), 3)}."
    )


def confidence_level_from_score(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


def build_confidence_reasons(recipe: dict, request: RecipeGenerateRequest) -> List[str]:
    reasons = []

    matched_count = len(recipe.get("matched_input_ingredients", []))
    extra_count = int(recipe.get("extra_major_count", 0))
    pair_bonus = float(recipe.get("pair_bonus", 0.0))
    lexical = float(recipe.get("lexical_score", 0.0))
    semantic = float(recipe.get("semantic_score", 0.0))
    hybrid = float(recipe.get("match_score", 0.0))

    input_count = max(len(request.ingredients), 1)

    requested_cuisine = normalize_text(request.cuisine or "")
    recipe_cuisine = normalize_text(recipe.get("cuisine", ""))

    if matched_count == input_count:
        reasons.append("All requested ingredients matched.")
    elif matched_count >= max(2, input_count - 1):
        reasons.append("Most requested ingredients matched.")
    elif matched_count > 0:
        reasons.append("Some requested ingredients matched.")
    else:
        reasons.append("Very few requested ingredients matched.")

    if extra_count <= 2:
        reasons.append("Recipe needs few extra major ingredients.")
    elif extra_count <= 5:
        reasons.append("Recipe needs a moderate number of extra ingredients.")
    else:
        reasons.append("Recipe needs many extra ingredients.")

    if requested_cuisine and recipe_cuisine:
        if requested_cuisine == recipe_cuisine:
            reasons.append("Cuisine preference matches well.")
        else:
            reasons.append("Cuisine preference does not match strongly.")

    if pair_bonus > 0:
        reasons.append("Ingredient pair compatibility improved ranking.")

    if hybrid >= 0.75:
        reasons.append("Hybrid retrieval score is strong.")
    elif hybrid >= 0.5:
        reasons.append("Hybrid retrieval score is moderate.")
    else:
        reasons.append("Hybrid retrieval score is weak.")

    if lexical >= 0.7:
        reasons.append("Lexical ingredient overlap is strong.")

    if semantic >= 0.6:
        reasons.append("Semantic similarity helped this result.")

    return reasons


def compute_confidence_score(recipe: dict, request: RecipeGenerateRequest) -> float:
    matched_count = len(recipe.get("matched_input_ingredients", []))
    extra_count = int(recipe.get("extra_major_count", 0))
    pair_bonus = float(recipe.get("pair_bonus", 0.0))
    hybrid = float(recipe.get("match_score", 0.0))

    input_count = max(len(request.ingredients), 1)
    coverage_score = matched_count / input_count
    extra_penalty = min(extra_count * 0.06, 0.36)

    requested_cuisine = normalize_text(request.cuisine or "")
    recipe_cuisine = normalize_text(recipe.get("cuisine", ""))
    cuisine_score = 1.0 if (requested_cuisine and recipe_cuisine and requested_cuisine == recipe_cuisine) else 0.4

    score = (
        0.5 * min(hybrid, 1.0)
        + 0.3 * coverage_score
        + 0.1 * cuisine_score
        + 0.1 * min(pair_bonus * 4, 1.0)
        - extra_penalty
    )

    return round(max(0.0, min(score, 1.0)), 3)


def compute_meta_confidence(recipes: List[dict]) -> dict:
    if not recipes:
        return {
            "confidence_score": 0.0,
            "confidence_level": "low",
            "confidence_reasons": ["No retrieval candidates were found."],
        }

    top = recipes[0]
    top_score = float(top.get("confidence_score", 0.0))
    reasons = list(top.get("confidence_reasons", []))

    if len(recipes) >= 2:
        gap = float(top.get("match_score", 0.0)) - float(recipes[1].get("match_score", 0.0))
        if gap >= 0.15:
            reasons.append("Top result is clearly ahead of the next candidate.")
        elif gap <= 0.03:
            reasons.append("Top results are very close, so ranking confidence is lower.")

    return {
        "confidence_score": round(top_score, 3),
        "confidence_level": confidence_level_from_score(top_score),
        "confidence_reasons": reasons,
    }


def passes_quality_gate(recipe: dict, request: RecipeGenerateRequest) -> bool:
    match_score = float(recipe.get("match_score", 0.0))
    matched_count = len(recipe.get("matched_input_ingredients", []))
    extra_count = int(recipe.get("extra_major_count", 0))
    confidence_score = float(recipe.get("confidence_score", 0.0))
    input_count = max(len(request.ingredients), 1)

    requested_cuisine = normalize_text(request.cuisine or "")
    recipe_cuisine = normalize_text(recipe.get("cuisine", ""))
    cuisine_mismatch = bool(
        requested_cuisine and recipe_cuisine and requested_cuisine != recipe_cuisine
    )

    if matched_count == 0:
        return False

    if input_count == 1:
        if match_score < 0.35:
            return False
    elif input_count == 2:
        if matched_count < 2:
            return False
        if match_score < 0.55:
            return False
    else:
        if matched_count < 2:
            return False
        if match_score < 0.45:
            return False

    if extra_count >= 8:
        return False

    if confidence_score < 0.35:
        return False

    if cuisine_mismatch and match_score < 0.75:
        return False

    return True


def apply_quality_gate(recipes: List[dict], request: RecipeGenerateRequest) -> List[dict]:
    filtered = [r for r in recipes if passes_quality_gate(r, request)]

    if filtered:
        return filtered

    return []


def to_recipe_summary(recipe: dict, request: RecipeGenerateRequest) -> dict:
    confidence_score = compute_confidence_score(recipe, request)
    confidence_level = confidence_level_from_score(confidence_score)
    confidence_reasons = build_confidence_reasons(recipe, request)

    return {
        "id": recipe.get("id", ""),
        "title": recipe.get("title", ""),
        "description": recipe.get("description", ""),
        "cuisine": recipe.get("cuisine", ""),
        "prep_time_mins": recipe.get("prep_time_mins"),
        "total_time_mins": recipe.get("total_time_mins"),
        "servings": recipe.get("servings"),
        "match_score": recipe.get("match_score", 0.0),
        "why_chosen": build_why_chosen(recipe),
        "extra_major_count": recipe.get("extra_major_count", 0),
        "matched_input_ingredients": recipe.get("matched_input_ingredients", []),
        "confidence_score": confidence_score,
        "confidence_level": confidence_level,
        "confidence_reasons": confidence_reasons,
    }


def build_query_text(request: RecipeGenerateRequest) -> str:
    parts = [
        " ".join(request.ingredients),
        request.cuisine or "",
    ]
    return " | ".join(part for part in parts if part).strip()


def retrieve_top_recipes_lexical(request: RecipeGenerateRequest, top_k: int = 10) -> List[dict]:
    from app.services.recipe_data import load_recipes

    recipes = load_recipes()
    candidates = []
    normalized_input = normalize_ingredient_list(request.ingredients)

    for recipe in recipes:
        scored = calculate_recipe_score(recipe, request)
        recipe_ingredients = [
            normalize_text(i)
            for i in recipe.get("ingredients_clean", recipe.get("ingredients", []))
        ]

        if recipe_has_disallowed_major_ingredient(recipe_ingredients, normalized_input):
            continue

        scored["semantic_score"] = 0.0
        scored["match_score"] = scored["lexical_score"]
        candidates.append(scored)

    candidates.sort(
        key=lambda x: (
            x["match_score"],
            x["lexical_score"],
            len(x.get("matched_input_ingredients", [])),
            -x.get("extra_major_count", 0),
            x.get("semantic_score", 0.0),
            -x.get("disallowed_major_count", 0),
        ),
        reverse=True,
    )

    summaries = [to_recipe_summary(r, request) for r in candidates[:top_k]]
    return apply_quality_gate(summaries, request)[:top_k]


def retrieve_top_recipes(request: RecipeGenerateRequest, top_k: int = 10) -> List[dict]:
    if not faiss_available():
        return retrieve_top_recipes_lexical(request, top_k=top_k)

    index, recipes = load_faiss_resources()

    query_text = build_query_text(request)
    query_vector = embed_texts([query_text]).astype("float32")
    faiss.normalize_L2(query_vector)

    candidate_k = min(max(top_k * 8, 30), len(recipes))
    scores, ids = index.search(query_vector, candidate_k)

    results = []
    normalized_input = normalize_ingredient_list(request.ingredients)

    for score, idx in zip(scores[0], ids[0]):
        if idx == -1:
            continue

        raw_recipe = recipes[idx]
        recipe_ingredients = [
            normalize_text(i)
            for i in raw_recipe.get("ingredients_clean", raw_recipe.get("ingredients", []))
        ]

        if recipe_has_disallowed_major_ingredient(recipe_ingredients, normalized_input):
            continue

        recipe = calculate_recipe_score(raw_recipe, request)
        recipe["semantic_score"] = float(score)
        recipe["match_score"] = round((0.9 * recipe["lexical_score"]) + (0.1 * float(score)), 3)
        results.append(recipe)

    results.sort(
        key=lambda x: (
            x["match_score"],
            x["lexical_score"],
            len(x.get("matched_input_ingredients", [])),
            -x.get("extra_major_count", 0),
            x.get("semantic_score", 0.0),
            -x.get("disallowed_major_count", 0),
        ),
        reverse=True,
    )

    summaries = [to_recipe_summary(r, request) for r in results[:top_k]]
    return apply_quality_gate(summaries, request)[:top_k]


def should_fallback_to_generation(recipes: List[dict], request: RecipeGenerateRequest) -> bool:
    if not recipes:
        return True

    top = recipes[0]
    top_score = float(top.get("match_score", 0.0))
    matched_count = len(top.get("matched_input_ingredients", []))
    extra_count = int(top.get("extra_major_count", 0))
    input_count = max(len(request.ingredients), 1)

    requested_cuisine = normalize_text(request.cuisine or "")
    top_cuisine = normalize_text(top.get("cuisine", ""))

    cuisine_mismatch = bool(
        requested_cuisine and top_cuisine and requested_cuisine != top_cuisine
    )

    if top_score < 0.55:
        return True
    if input_count == 2 and matched_count < 2:
        return True
    if input_count >= 3 and matched_count < 2:
        return True
    if input_count >= 2 and matched_count == 0:
        return True
    if extra_count >= 8:
        return True
    if cuisine_mismatch and top_score < 1.5:
        return True

    return False


def retrieve_with_fallback_signal(request: RecipeGenerateRequest, top_k: int = 10) -> dict:
    recipes = retrieve_top_recipes(request, top_k=top_k)
    fallback_needed = should_fallback_to_generation(recipes, request)
    meta_confidence = compute_meta_confidence(recipes)

    fallback_reason = None
    if not recipes:
        fallback_reason = "no_retrieval_results"
    elif meta_confidence["confidence_level"] == "low":
        fallback_reason = "retrieval_low_confidence"
    elif fallback_needed:
        fallback_reason = "retrieval_rule_triggered"

    return {
        "recipes": recipes,
        "fallback_needed": fallback_needed,
        "fallback_reason": fallback_reason,
        "confidence_score": meta_confidence["confidence_score"],
        "confidence_level": meta_confidence["confidence_level"],
        "confidence_reasons": meta_confidence["confidence_reasons"],
    }