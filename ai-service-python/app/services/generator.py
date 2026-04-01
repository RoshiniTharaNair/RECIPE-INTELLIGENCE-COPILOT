import time
from typing import List

from app.models.schemas import RecipeGenerateRequest
from app.services.retriever import retrieve_top_recipes
from app.services.ingredient_knowledge import normalize_text


def build_retrieval_context(data: RecipeGenerateRequest, candidate_count: int = 1) -> List[dict]:
    try:
        candidates = retrieve_top_recipes(data, top_k=candidate_count)
        if not isinstance(candidates, list):
            return []
        return candidates[:candidate_count]
    except Exception:
        return []


def normalize_generation_ingredient(name: str) -> str:
    value = normalize_text(name)

    synonym_map = {
        "capsicum": "bell pepper",
        "bell peppers": "bell pepper",
        "peppers": "bell pepper",
        "yoghurt": "yogurt",
        "curd": "yogurt",
        "eggs": "egg",
        "tomatoes": "tomato",
        "onions": "onion",
        "potatoes": "potato",
    }

    return synonym_map.get(value, value)


def normalize_generation_ingredients(items: List[str]) -> List[str]:
    return [normalize_generation_ingredient(i) for i in items]


def has_ing(ing_set: set[str], *names: str) -> bool:
    return any(normalize_generation_ingredient(n) in ing_set for n in names)


def ingredient_items(pairs):
    return [{"name": name, "quantity": qty} for name, qty in pairs if name]


def maybe_step(condition: bool, text: str) -> list[str]:
    return [text] if condition else []


def build_deterministic_recipe(data: RecipeGenerateRequest, retrieved_candidates: List[dict]) -> dict:
    user_ings = normalize_generation_ingredients(data.ingredients)
    ing_set = set(user_ings)
    cuisine = normalize_text(data.cuisine or "")

    def make_recipe(
        title,
        why,
        ingredients,
        steps,
        substitutions=None,
        template_name="",
        grounding_source="template_only",
        match_score=1.0,
        warnings=None,
    ):
        return {
            "title": title,
            "why_chosen": why,
            "ingredients": ingredient_items(ingredients),
            "steps": steps,
            "substitutions": substitutions or [],
            "nutrition_summary": {
                "calories": None,
                "protein_g": None,
                "carbs_g": None,
                "fats_g": None,
            },
            "warnings": warnings or [],
            "match_score": match_score,
            "matched_input_ingredients": data.ingredients,
            "extra_major_ingredients": [],
            "template_name": template_name,
            "grounding_source": grounding_source,
        }

    if has_ing(ing_set, "spinach") and has_ing(ing_set, "paneer") and (cuisine == "indian" or not cuisine):
        return make_recipe(
            "Saag Paneer",
            "Built from spinach and paneer with an Indian-style template.",
            [("spinach", "3 cups"), ("paneer", "200 g"), ("garlic", "2 cloves"), ("cumin", "1 tsp")],
            [
                "Wash and chop the spinach.",
                "Heat oil and sauté garlic with cumin.",
                "Add spinach and cook until wilted.",
                "Add paneer cubes and cook for 3 to 4 minutes.",
                "Season and serve hot.",
            ],
            substitutions=[],
            template_name="saag_paneer",
            grounding_source="retrieval_grounded" if retrieved_candidates else "template_only",
            match_score=1.0,
            warnings=[],
        )

    if has_ing(ing_set, "spinach") and has_ing(ing_set, "cheese"):
        return make_recipe(
            "Spinach Cheese Skillet",
            "Built from spinach and cheese without introducing paneer.",
            [("spinach", "3 cups"), ("cheese", "1 cup"), ("garlic", "2 cloves")],
            [
                "Wash and chop the spinach.",
                "Heat a little oil in a pan and sauté garlic.",
                "Add spinach and cook until soft.",
                "Add cheese and stir until melted through the spinach.",
                "Serve hot.",
            ],
            substitutions=["Use mozzarella or cheddar for a different texture."],
            template_name="spinach_cheese_skillet",
            grounding_source="retrieval_grounded" if retrieved_candidates else "template_only",
            match_score=1.0,
            warnings=[],
        )

    if has_ing(ing_set, "bread") and has_ing(ing_set, "cheese"):
        return make_recipe(
            "Cheese Toast",
            "Built from bread and cheese using a quick beginner-friendly template.",
            [("bread", "2 slices"), ("cheese", "1/2 cup")],
            [
                "Place the bread on a pan or tray.",
                "Top evenly with cheese.",
                "Toast or cook until the bread is crisp and the cheese melts.",
                "Serve immediately.",
            ],
            substitutions=[],
            template_name="cheese_toast",
            grounding_source="template_only",
            match_score=1.0,
            warnings=[],
        )

    if has_ing(ing_set, "tomato") and has_ing(ing_set, "onion"):
        title = "Onion Tomato Masala" if cuisine == "indian" else "Tomato Onion Sauté"
        return make_recipe(
            title,
            "Built from tomato and onion with a simple stovetop base template.",
            [("onion", "1 medium"), ("tomato", "2 medium"), ("oil", "1 tbsp")],
            [
                "Slice the onion and chop the tomato.",
                "Heat oil in a pan.",
                "Cook onion until softened.",
                "Add tomato and cook until the mixture becomes soft and saucy.",
                "Season lightly and serve warm.",
            ],
            substitutions=["Add garlic or bell pepper for more flavor."],
            template_name="onion_tomato_masala" if cuisine == "indian" else "tomato_onion_saute",
            grounding_source="template_only",
            match_score=1.0,
            warnings=[],
        )

    if has_ing(ing_set, "rice") and has_ing(ing_set, "onion"):
        title = "Onion Rice" if cuisine != "indian" else "Onion Pulao"
        return make_recipe(
            title,
            "Built from rice and onion using a quick pan-finished rice template.",
            [("rice", "1 cup"), ("onion", "1 medium"), ("oil", "1 tbsp")],
            [
                "Cook the rice and let it cool slightly.",
                "Slice the onion.",
                "Heat oil in a pan and cook onion until softened.",
                "Add the cooked rice and mix well.",
                "Season lightly and serve hot.",
            ],
            substitutions=["Use leftover rice for faster preparation."],
            template_name="onion_pulao" if cuisine == "indian" else "onion_rice",
            grounding_source="template_only",
            match_score=1.0,
            warnings=[],
        )

    if has_ing(ing_set, "rice") and (has_ing(ing_set, "tomato") or has_ing(ing_set, "onion") or has_ing(ing_set, "vegetables")):
        title = "Vegetable Pulao" if cuisine == "indian" else "Vegetable Fried Rice"
        return make_recipe(
            title,
            "Built from rice with a simple vegetable-based template.",
            [
                ("rice", "1 cup"),
                ("onion", "1 medium") if has_ing(ing_set, "onion") else (None, None),
                ("tomato", "1 medium") if has_ing(ing_set, "tomato") else (None, None),
                ("vegetables", "1 cup") if has_ing(ing_set, "vegetables") else (None, None),
                ("oil", "1 tbsp"),
            ],
            [
                "Cook the rice and let it cool slightly.",
                "Heat oil in a pan.",
                *maybe_step(has_ing(ing_set, "onion"), "Add onion and cook until softened."),
                *maybe_step(has_ing(ing_set, "tomato"), "Add tomato and cook until softened."),
                *maybe_step(has_ing(ing_set, "vegetables"), "Add vegetables and cook for a few minutes."),
                "Add rice, mix well, season lightly, and serve hot.",
            ],
            substitutions=["Use cooked leftover rice for faster prep."],
            template_name="vegetable_pulao" if cuisine == "indian" else "vegetable_fried_rice",
            grounding_source="template_only",
            match_score=1.0,
            warnings=[],
        )

    if has_ing(ing_set, "pasta") and has_ing(ing_set, "tomato"):
        return make_recipe(
            "Tomato Pasta",
            "Built from pasta and tomato using a quick tomato-based template.",
            [("pasta", "1 cup"), ("tomato", "2 medium"), ("oil", "1 tbsp")],
            [
                "Boil the pasta until tender and drain.",
                "Chop the tomato.",
                "Heat a little oil in a pan.",
                "Add tomato and cook until soft and saucy.",
                "Add pasta, mix well, and serve hot.",
            ],
            substitutions=["Add garlic or chili flakes for more flavor."],
            template_name="tomato_pasta",
            grounding_source="template_only",
            match_score=1.0,
            warnings=[],
        )

    if has_ing(ing_set, "pasta") and (has_ing(ing_set, "cheese") or has_ing(ing_set, "tomato")):
        return make_recipe(
            "Simple Pasta",
            "Built from pasta with a quick cheese or tomato-based template.",
            [
                ("pasta", "1 cup"),
                ("cheese", "1/2 cup") if has_ing(ing_set, "cheese") else (None, None),
                ("tomato", "1 medium") if has_ing(ing_set, "tomato") else (None, None),
                ("oil", "1 tbsp"),
            ],
            [
                "Boil the pasta until tender and drain.",
                "Heat a little oil in a pan.",
                *maybe_step(has_ing(ing_set, "tomato"), "Add tomato and cook until soft."),
                "Add pasta and mix well.",
                *maybe_step(has_ing(ing_set, "cheese"), "Add cheese, stir briefly, and serve hot."),
                *maybe_step(not has_ing(ing_set, "cheese"), "Season lightly and serve hot."),
            ],
            substitutions=["Add garlic for more flavor."],
            template_name="simple_pasta",
            grounding_source="template_only",
            match_score=1.0,
            warnings=[],
        )

    if has_ing(ing_set, "egg") and has_ing(ing_set, "tomato"):
        title = "Egg Tomato Bhurji" if cuisine == "indian" else "Scrambled Egg with Tomato"
        return make_recipe(
            title,
            "Built from egg and tomato using a quick stovetop template.",
            [("egg", "2"), ("tomato", "1 medium"), ("oil", "1 tsp")],
            [
                "Beat the egg in a bowl.",
                "Chop the tomato.",
                "Heat oil in a pan and cook tomato briefly.",
                "Add egg and stir gently until just cooked.",
                "Serve hot.",
            ],
            substitutions=["Add onion or black pepper for more flavor."],
            template_name="egg_tomato_bhurji" if cuisine == "indian" else "scrambled_egg_tomato",
            grounding_source="template_only",
            match_score=1.0,
            warnings=[],
        )

    if has_ing(ing_set, "egg") and (has_ing(ing_set, "onion") or has_ing(ing_set, "tomato")):
        title = "Egg Bhurji" if cuisine == "indian" else "Vegetable Omelette"
        return make_recipe(
            title,
            "Built from egg with onion or tomato in a quick stovetop template.",
            [
                ("egg", "2"),
                ("onion", "1 small") if has_ing(ing_set, "onion") else (None, None),
                ("tomato", "1 small") if has_ing(ing_set, "tomato") else (None, None),
            ],
            [
                "Beat the egg in a bowl.",
                "Heat oil in a pan.",
                *maybe_step(has_ing(ing_set, "onion"), "Cook onion until softened."),
                *maybe_step(has_ing(ing_set, "tomato"), "Add tomato and cook briefly."),
                "Add egg and stir gently until just cooked.",
                "Serve hot.",
            ],
            substitutions=["Use black pepper or chili for extra flavor."],
            template_name="egg_bhurji" if cuisine == "indian" else "vegetable_omelette",
            grounding_source="template_only",
            match_score=1.0,
            warnings=[],
        )

    if has_ing(ing_set, "potato") and has_ing(ing_set, "onion"):
        title = "Aloo Pyaz Sabzi" if cuisine == "indian" else "Potato Onion Skillet"
        return make_recipe(
            title,
            "Built from potato and onion in a simple pan-cooked template.",
            [("potato", "2 medium"), ("onion", "1 medium"), ("oil", "1 tbsp")],
            [
                "Peel and chop the potatoes.",
                "Slice the onion.",
                "Heat oil in a pan and cook onion until softened.",
                "Add potatoes and cook until tender.",
                "Season lightly and serve hot.",
            ],
            substitutions=["Add cumin or chili for more flavor."],
            template_name="aloo_pyaz_sabzi" if cuisine == "indian" else "potato_onion_skillet",
            grounding_source="template_only",
            match_score=1.0,
            warnings=[],
        )

    if has_ing(ing_set, "potato") and (has_ing(ing_set, "onion") or has_ing(ing_set, "tomato")):
        title = "Aloo Sabzi" if cuisine == "indian" else "Potato Skillet"
        return make_recipe(
            title,
            "Built from potato with onion or tomato in a simple pan-cooked template.",
            [
                ("potato", "2 medium"),
                ("onion", "1 medium") if has_ing(ing_set, "onion") else (None, None),
                ("tomato", "1 medium") if has_ing(ing_set, "tomato") else (None, None),
            ],
            [
                "Peel and chop the potatoes.",
                "Heat oil in a pan.",
                *maybe_step(has_ing(ing_set, "onion"), "Cook onion until softened."),
                "Add potatoes and cook until they begin to soften.",
                *maybe_step(has_ing(ing_set, "tomato"), "Add tomato and cook until everything is tender."),
                "Season lightly and serve hot.",
            ],
            substitutions=["Add cumin or chili for more flavor."],
            template_name="aloo_sabzi" if cuisine == "indian" else "potato_skillet",
            grounding_source="template_only",
            match_score=1.0,
            warnings=[],
        )

    if has_ing(ing_set, "bell pepper") and has_ing(ing_set, "onion"):
        return make_recipe(
            "Bell Pepper Onion Stir-Fry",
            "Built from bell pepper and onion using normalized ingredient matching.",
            [("bell pepper", "1 medium"), ("onion", "1 medium"), ("oil", "1 tbsp")],
            [
                "Slice the bell pepper and onion.",
                "Heat oil in a pan.",
                "Cook onion until softened.",
                "Add bell pepper and cook until just tender.",
                "Season lightly and serve hot.",
            ],
            substitutions=["Capsicum works the same as bell pepper here."],
            template_name="bell_pepper_onion_stir_fry",
            grounding_source="template_only",
            match_score=1.0,
            warnings=[],
        )

    if has_ing(ing_set, "yogurt") and has_ing(ing_set, "onion"):
        return make_recipe(
            "Yogurt Onion Dip",
            "Built from yogurt and onion using normalized ingredient matching.",
            [("yogurt", "1 cup"), ("onion", "2 tbsp finely chopped")],
            [
                "Finely chop the onion.",
                "Add onion to the yogurt.",
                "Mix well until evenly combined.",
                "Season lightly if desired.",
                "Serve chilled or at room temperature.",
            ],
            substitutions=["Curd works the same as yogurt here."],
            template_name="yogurt_onion_dip",
            grounding_source="template_only",
            match_score=1.0,
            warnings=[],
        )

    title = "Custom " + " ".join(i.title() for i in data.ingredients[:2]) + " Recipe"
    if retrieved_candidates and retrieved_candidates[0].get("title"):
        top_title = retrieved_candidates[0]["title"]
        if not ("paneer" in normalize_text(top_title) and "paneer" not in ing_set):
            title = top_title

    generic_warnings = [
        "Low-confidence generated fallback: no known recipe template matched these ingredients."
    ]
    if not retrieved_candidates:
        generic_warnings.append(
            "No retrieval grounding was available, so this recipe is only a basic placeholder."
        )

    return make_recipe(
        title,
        f"Built directly from your ingredients: {', '.join(data.ingredients)}.",
        [(ing, "1 unit") for ing in user_ings],
        [
            f"Prepare the ingredients: {', '.join(user_ings)}.",
            "Heat a pan with a little oil.",
            f"Cook the main ingredients: {', '.join(user_ings)} until combined and tender.",
            "Season lightly and adjust to taste.",
            "Serve hot.",
        ],
        substitutions=[],
        template_name="generic_fallback",
        grounding_source="retrieval_grounded" if retrieved_candidates else "template_only",
        match_score=0.25 if not retrieved_candidates else 0.4,
        warnings=generic_warnings,
    )


def generate_recipes(data: RecipeGenerateRequest) -> dict:
    started_at = time.perf_counter()
    retrieved_candidates = build_retrieval_context(data, candidate_count=1)

    recipe = build_deterministic_recipe(data, retrieved_candidates)
    latency_ms = int((time.perf_counter() - started_at) * 1000)

    quality_notes = []
    if recipe.get("template_name") == "generic_fallback":
        quality_notes.append("No known template matched the input ingredients.")
        quality_notes.append("Generated output is a low-confidence fallback.")
        if retrieved_candidates:
            quality_notes.append("A retrieved title influenced the fallback recipe naming.")
        else:
            quality_notes.append("No strong retrieved candidates were available for grounding.")
    elif recipe.get("grounding_source") == "retrieval_grounded":
        quality_notes.append("Recipe was assembled deterministically using retrieved grounding.")
    else:
        quality_notes.append(
            "No strong retrieved candidates were available, so recipe was assembled from user ingredients."
        )

    return {
        "recipes": [recipe],
        "meta": {
            "latency_ms": latency_ms,
            "model_name": "deterministic_generator",
            "recipe_count": 1,
            "input_ingredients": data.ingredients,
            "quality_notes": quality_notes,
        },
    }