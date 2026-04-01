import json
from pathlib import Path

from app.models.schemas import RecipeGenerateRequest
from app.services.retriever import retrieve_top_recipes

EVAL_PATH = Path(__file__).resolve().parent.parent / "data" / "eval" / "retrieval_eval.json"


def normalize_text(text: str) -> str:
    return text.strip().lower()


def title_matches_expected(title: str, expected_keywords: list[str]) -> bool:
    t = normalize_text(title)
    return any(keyword.lower() in t for keyword in expected_keywords)


def recipe_covers_ingredients(recipe: dict, expected_ingredients: list[str]) -> bool:
    matched = [x.lower() for x in recipe.get("matched_input_ingredients", [])]
    return all(ing.lower() in matched for ing in expected_ingredients)


def main():
    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        eval_cases = json.load(f)

    total = len(eval_cases)
    title_hit_count = 0
    ingredient_hit_count = 0

    for idx, case in enumerate(eval_cases, start=1):
        request = RecipeGenerateRequest(**case["query"])
        results = retrieve_top_recipes(request, top_k=3)

        top_titles = [r["title"] for r in results]
        title_hit = any(
            title_matches_expected(title, case["expected_any_keywords"])
            for title in top_titles
        )
        ingredient_hit = any(
            recipe_covers_ingredients(recipe, case["expected_all_ingredients"])
            for recipe in results
        )

        if title_hit:
            title_hit_count += 1
        if ingredient_hit:
            ingredient_hit_count += 1

        print(f"\nCase {idx}: {case['name']}")
        print("Top titles:", top_titles)
        print("Title hit:", title_hit)
        print("Ingredient coverage hit:", ingredient_hit)

    print("\n=== Retrieval Eval Summary ===")
    print(f"Cases: {total}")
    print(f"Title-hit@3: {title_hit_count}/{total}")
    print(f"Ingredient-coverage-hit@3: {ingredient_hit_count}/{total}")


if __name__ == "__main__":
    main()