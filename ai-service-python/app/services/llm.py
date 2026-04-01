import json
import time
from typing import List

import requests

from app.models.schemas import RecipeDetailGenerateRequest, RecipeGenerateRequest
from app.services.recipe_data import get_recipe_by_id
from app.services.retriever import retrieve_top_recipes

MODEL_NAME = "llama3.2:1b"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

ALLOWED_PANTRY_BASICS = {
    "salt", "water", "oil", "turmeric", "chili powder", "cumin",
    "mustard seeds", "coriander powder", "pepper", "garlic", "ginger",
}

MAJOR_INGREDIENT_KEYWORDS = {
    "chicken", "paneer", "egg", "eggs", "meat", "fish", "mushroom",
    "tofu", "beef", "pork", "lamb", "shrimp", "prawn"
}


def contains_major_keyword(text: str) -> str | None:
    t = normalize_text(text)
    for word in MAJOR_INGREDIENT_KEYWORDS:
        if word in t:
            return word
    return None

def build_strict_grounded_prompt(data: RecipeGenerateRequest, retrieved_candidates: List[dict]) -> str:
    return f"""
You are a recipe assistant.

Return ONLY valid JSON.
Do not return markdown.
Do not wrap output in triple backticks.

Return exactly this JSON shape:
{{
  "recipes": [
    {{
      "title": "string",
      "why_chosen": "string",
      "ingredients": [{{"name": "string", "quantity": "string"}}],
      "steps": ["string"],
      "substitutions": ["string"],
      "nutrition_summary": {{
        "calories": 0,
        "protein_g": 0,
        "carbs_g": 0,
        "fats_g": 0
      }},
      "warnings": ["string"]
    }}
  ]
}}

User input:
ingredients: {data.ingredients}
cuisine: {data.cuisine}
prep_time: {data.prep_time}
servings: {data.servings}
skill_level: {data.skill_level}

Rules:
- Return exactly 1 recipe
- DO NOT introduce paneer, chicken, egg, meat, fish, mushroom, tofu, or any other major ingredient unless explicitly present in the user input
- If the input says cheese, do not replace it with paneer unless paneer was explicitly given
- Ingredients must be complete
- Steps must be complete
- Output only JSON
""".strip()

def validate_generated_recipe(recipe: dict, user_ingredients: List[str]) -> List[str]:
    issues = []
    normalized_user = [normalize_text(i) for i in user_ingredients]
    user_text = " ".join(normalized_user)

    recipe_title = normalize_text(recipe.get("title", ""))
    why = normalize_text(recipe.get("why_chosen", ""))
    steps_text = " ".join(flatten_to_strings(recipe.get("steps", []))).lower()

    ingredient_names = []
    for item in recipe.get("ingredients", []):
        if isinstance(item, dict):
            ingredient_names.append(normalize_text(item.get("name", "")))
        elif isinstance(item, str):
            ingredient_names.append(normalize_text(item))

    combined_texts = [recipe_title, why, steps_text] + ingredient_names

    for text in combined_texts:
        kw = contains_major_keyword(text)
        if kw and kw not in user_text:
            issues.append(f"Introduced major ingredient '{kw}' not present in user input.")
            break

    if not recipe.get("ingredients"):
        issues.append("Generated recipe has no ingredients.")
    if not recipe.get("steps"):
        issues.append("Generated recipe has no steps.")

    return issues

def normalize_text(text: str) -> str:
    return text.strip().lower()


def flatten_to_strings(value) -> list[str]:
    result = []

    if value is None:
        return result

    if isinstance(value, str):
        text = value.strip()
        if text:
            result.append(text)
        return result

    if isinstance(value, (int, float, bool)):
        result.append(str(value))
        return result

    if isinstance(value, dict):
        for v in value.values():
            result.extend(flatten_to_strings(v))
        return result

    if isinstance(value, list):
        for item in value:
            result.extend(flatten_to_strings(item))
        return result

    result.append(str(value))
    return result


def normalize_single_recipe(recipe: dict) -> dict:
    if recipe.get("substitutions") is None:
        recipe["substitutions"] = []

    if recipe.get("warnings") is None:
        recipe["warnings"] = []

    if recipe.get("steps") is None:
        recipe["steps"] = []

    if recipe.get("ingredients") is None:
        recipe["ingredients"] = []

    if recipe.get("nutrition_summary") is None:
        recipe["nutrition_summary"] = {
            "calories": None,
            "protein_g": None,
            "carbs_g": None,
            "fats_g": None,
        }

    if recipe.get("title") is None:
        recipe["title"] = "Generated Recipe"

    if recipe.get("why_chosen") is None:
        recipe["why_chosen"] = "Chosen based on the provided ingredients and preferences."

    normalized_ingredients = []
    for item in recipe.get("ingredients", []):
        if isinstance(item, dict):
            normalized_ingredients.append(
                {
                    "name": str(item.get("name", "")).strip(),
                    "quantity": str(item.get("quantity", "")).strip(),
                }
            )
        elif isinstance(item, str):
            normalized_ingredients.append(
                {
                    "name": item.strip(),
                    "quantity": "",
                }
            )

    recipe["ingredients"] = normalized_ingredients
    recipe["steps"] = flatten_to_strings(recipe.get("steps"))
    recipe["substitutions"] = flatten_to_strings(recipe.get("substitutions"))
    recipe["warnings"] = flatten_to_strings(recipe.get("warnings"))

    recipe["match_score"] = 0.0
    recipe["matched_input_ingredients"] = []
    recipe["extra_major_ingredients"] = []

    return recipe


def normalize_recipe_list(result: dict) -> dict:
    recipes = result.get("recipes")

    if recipes is None or not isinstance(recipes, list):
        recipes = []

    normalized = []
    for recipe in recipes:
        if isinstance(recipe, dict):
            normalized.append(normalize_single_recipe(recipe))

    result["recipes"] = normalized
    return result


def get_recipe_ingredient_names(recipe: dict) -> List[str]:
    ingredients = recipe.get("ingredients", [])
    names = []

    for item in ingredients:
        if isinstance(item, dict) and item.get("name"):
            names.append(normalize_text(item["name"]))

    return names


def score_recipe(recipe: dict, input_ingredients: List[str]) -> dict:
    normalized_input = [normalize_text(i) for i in input_ingredients]
    recipe_ingredient_names = get_recipe_ingredient_names(recipe)

    matched = [i for i in normalized_input if i in recipe_ingredient_names]

    extras = []
    for ingredient in recipe_ingredient_names:
        if ingredient not in normalized_input and ingredient not in ALLOWED_PANTRY_BASICS:
            extras.append(ingredient)

    match_ratio = len(matched) / max(len(normalized_input), 1)
    extra_penalty = 0.15 * len(extras)
    score = max(0.0, round(match_ratio - extra_penalty, 10))

    recipe["match_score"] = score
    recipe["matched_input_ingredients"] = matched
    recipe["extra_major_ingredients"] = extras

    if extras:
        recipe["warnings"].append(
            f"Contains additional major ingredients not in input: {', '.join(extras)}"
        )

    return recipe


def rank_and_filter_recipes(recipes: List[dict], input_ingredients: List[str]) -> List[dict]:
    scored = [score_recipe(recipe, input_ingredients) for recipe in recipes]

    scored.sort(
        key=lambda r: (
            r.get("match_score", 0),
            len(r.get("matched_input_ingredients", [])),
            -len(r.get("extra_major_ingredients", [])),
        ),
        reverse=True,
    )

    strong = [r for r in scored if r.get("match_score", 0.0) >= 0.35]
    if strong:
        return strong[:10]

    return scored[:10]


def build_retrieval_context(data: RecipeGenerateRequest, candidate_count: int = 5) -> List[dict]:
    try:
        candidates = retrieve_top_recipes(data, top_k=candidate_count)
        if not isinstance(candidates, list):
            return []
        return candidates[:candidate_count]
    except Exception:
        return []


def build_grounded_prompt(data: RecipeGenerateRequest, retrieved_candidates: List[dict]) -> str:
    candidate_lines = []

    for idx, recipe in enumerate(retrieved_candidates, start=1):
        candidate_lines.append(
            {
                "rank": idx,
                "title": recipe.get("title", ""),
                "cuisine": recipe.get("cuisine", ""),
                "description": recipe.get("description", ""),
                "matched_input_ingredients": recipe.get("matched_input_ingredients", []),
            }
        )

    grounding_section = json.dumps(candidate_lines, ensure_ascii=False, indent=2)

    return f"""
You are a recipe assistant.

Return ONLY valid JSON.
Do not return markdown.
Do not wrap output in triple backticks.

Return exactly this JSON shape:
{{
  "recipes": [
    {{
      "title": "string",
      "why_chosen": "string",
      "ingredients": [
        {{
          "name": "string",
          "quantity": "string"
        }}
      ],
      "steps": ["string"],
      "substitutions": ["string"],
      "nutrition_summary": {{
        "calories": 0,
        "protein_g": 0,
        "carbs_g": 0,
        "fats_g": 0
      }},
      "warnings": ["string"]
    }}
  ]
}}

User input:
ingredients: {data.ingredients}
cuisine: {data.cuisine}
prep_time: {data.prep_time}
servings: {data.servings}
skill_level: {data.skill_level}

Retrieved candidates:
{grounding_section}

Rules:
- Return exactly 1 recipe
- Use the retrieved candidates only as inspiration and grounding context
- Do not copy retrieval metadata into the output
- Do not output fields like match_score, confidence_score, confidence_level, matched_input_ingredients, or extra_major_count
- The recipe must include full ingredients and full step-by-step instructions
- Use only the provided ingredients as the primary ingredients
- Do not add chicken, paneer, egg, meat, fish, mushroom, tofu, or other major ingredients unless explicitly provided
- Small pantry basics like salt, water, oil, turmeric, chili powder, cumin, mustard seeds, coriander powder, pepper, garlic, and ginger are allowed only if needed
- Prefer recipes matching the requested cuisine
- Prefer recipes that fit the prep_time and skill_level
- why_chosen should explain why the recipe fits the user request
- substitutions must always be an array, never null
- warnings must always be an array, never null
- steps must always be an array, never null
- ingredients must always be an array, never null
- nutrition_summary must always be an object, never null
- Output only JSON
""".strip()


def parse_llm_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        try:
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(raw[start:end + 1])
        except Exception:
            pass

    return {"recipes": []}


def call_ollama_json(prompt: str) -> dict:
    try:
        response = requests.post(
            OLLAMA_URL,
            headers={"Content-Type": "application/json"},
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "keep_alive": "10m",
                "options": {
                    "temperature": 0,
                    "num_predict": 400,
                },
            },
            timeout=120,
        )
        response.raise_for_status()

        raw = response.json()["response"].strip()
        print("RAW OLLAMA OUTPUT:")
        print(raw)
        return parse_llm_json(raw)

    except requests.exceptions.Timeout:
        return {
            "recipes": []
        }

def has_ing(ing_set: set[str], *names: str) -> bool:
    return any(normalize_text(n) in ing_set for n in names)

def first_present(ing_set: set[str], *names: str) -> str | None:
    for n in names:
        if normalize_text(n) in ing_set:
            return normalize_text(n)
    return None

def ingredient_items(pairs):
    return [{"name": name, "quantity": qty} for name, qty in pairs if name]

def maybe_step(condition: bool, text: str) -> list[str]:
    return [text] if condition else []


def build_deterministic_recipe(data: RecipeGenerateRequest, retrieved_candidates: List[dict]) -> dict:
    user_ings = [normalize_text(i) for i in data.ingredients]
    ing_set = set(user_ings)
    cuisine = normalize_text(data.cuisine or "")

    def make_recipe(title, why, ingredients, steps, substitutions=None, template_name="", grounding_source="template_only"):
        return {
            "title": title,
            "why_chosen": why,
            "ingredients": ingredient_items(ingredients),
            "steps": steps,
            "substitutions": substitutions or [],
            "nutrition_summary": {"calories": None, "protein_g": None, "carbs_g": None, "fats_g": None},
            "warnings": [],
            "match_score": 1.0,
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
        )

    if has_ing(ing_set, "rice") and (has_ing(ing_set, "tomato") or has_ing(ing_set, "onion") or has_ing(ing_set, "vegetables")):
        title = "Vegetable Pulao" if cuisine == "indian" else "Vegetable Fried Rice"
        return make_recipe(
            title,
            "Built from rice with a simple vegetable-based template.",
            [("rice", "1 cup"),
            ("onion", "1 medium") if has_ing(ing_set, "onion") else (None, None),
            ("tomato", "1 medium") if has_ing(ing_set, "tomato") else (None, None),
            ("vegetables", "1 cup") if has_ing(ing_set, "vegetables") else (None, None),
            ("oil", "1 tbsp")],
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
        )

    if has_ing(ing_set, "pasta") and (has_ing(ing_set, "cheese") or has_ing(ing_set, "tomato")):
        return make_recipe(
            "Simple Pasta",
            "Built from pasta with a quick cheese or tomato-based template.",
            [("pasta", "1 cup"),
            ("cheese", "1/2 cup") if has_ing(ing_set, "cheese") else (None, None),
            ("tomato", "1 medium") if has_ing(ing_set, "tomato") else (None, None),
            ("oil", "1 tbsp")],
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
        )

    if has_ing(ing_set, "egg", "eggs") and (has_ing(ing_set, "onion") or has_ing(ing_set, "tomato")):
        title = "Egg Bhurji" if cuisine == "indian" else "Vegetable Omelette"
        return make_recipe(
            title,
            "Built from egg with onion or tomato in a quick stovetop template.",
            [("egg", "2"),
            ("onion", "1 small") if has_ing(ing_set, "onion") else (None, None),
            ("tomato", "1 small") if has_ing(ing_set, "tomato") else (None, None)],
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
        )

    if has_ing(ing_set, "potato") and (has_ing(ing_set, "onion") or has_ing(ing_set, "tomato")):
        title = "Aloo Sabzi" if cuisine == "indian" else "Potato Skillet"
        return make_recipe(
            title,
            "Built from potato with onion or tomato in a simple pan-cooked template.",
            [("potato", "2 medium"),
            ("onion", "1 medium") if has_ing(ing_set, "onion") else (None, None),
            ("tomato", "1 medium") if has_ing(ing_set, "tomato") else (None, None)],
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
        )
    title = "Custom " + " ".join(i.title() for i in data.ingredients[:2]) + " Recipe"
    if retrieved_candidates and retrieved_candidates[0].get("title"):
        top_title = retrieved_candidates[0]["title"]
        if not ("paneer" in normalize_text(top_title) and "paneer" not in ing_set):
            title = top_title

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
    )


def generate_recipes(data: RecipeGenerateRequest) -> dict:
    started_at = time.perf_counter()
    retrieved_candidates = build_retrieval_context(data, candidate_count=1)

    recipe = build_deterministic_recipe(data, retrieved_candidates)
    latency_ms = int((time.perf_counter() - started_at) * 1000)

    quality_notes = []
    if retrieved_candidates:
        quality_notes.append("Recipe was assembled deterministically using retrieved grounding.")
    else:
        quality_notes.append("No strong retrieved candidates were available, so recipe was assembled from user ingredients.")

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


def build_detail_prompt(recipe: dict, data: RecipeDetailGenerateRequest) -> str:
    return f"""
You are a recipe assistant.

Return ONLY valid JSON.
Do not return markdown.
Do not wrap output in triple backticks.

Return exactly this JSON shape:
{{
  "title": "string",
  "why_chosen": "string",
  "ingredients": [
    {{
      "name": "string",
      "quantity": "string"
    }}
  ],
  "steps": ["string"],
  "substitutions": ["string"],
  "nutrition_summary": {{
    "calories": 0,
    "protein_g": 0,
    "carbs_g": 0,
    "fats_g": 0
  }},
  "warnings": ["string"],
  "source_recipe_title": "string",
  "grounded": true
}}

User ingredients:
{data.user_ingredients}

Requested servings:
{data.servings}

Skill level:
{data.skill_level}

Retrieved recipe:
{json.dumps(recipe, ensure_ascii=False)}

Rules:
- Use the retrieved recipe as the source of truth
- Do not invent a completely different recipe
- Keep the output grounded in the retrieved recipe title, ingredients, and instructions
- If some detail is missing, make a small reasonable assumption and mention it in warnings
- Keep steps easy to follow for a home cook
- substitutions must always be an array
- warnings must always be an array
- steps must always be an array
- ingredients must always be an array
- nutrition_summary must always be an object
- grounded must be true
- Output only JSON
""".strip()


def normalize_recipe_detail(result: dict) -> dict:
    if result.get("ingredients") is None:
        result["ingredients"] = []

    if result.get("steps") is None:
        result["steps"] = []

    if result.get("substitutions") is None:
        result["substitutions"] = []

    if result.get("warnings") is None:
        result["warnings"] = []

    if result.get("nutrition_summary") is None:
        result["nutrition_summary"] = {
            "calories": None,
            "protein_g": None,
            "carbs_g": None,
            "fats_g": None,
        }

    result["steps"] = flatten_to_strings(result.get("steps"))
    result["substitutions"] = flatten_to_strings(result.get("substitutions"))
    result["warnings"] = flatten_to_strings(result.get("warnings"))

    normalized_ingredients = []
    for item in result.get("ingredients", []):
        if isinstance(item, dict):
            normalized_ingredients.append(
                {
                    "name": str(item.get("name", "")).strip(),
                    "quantity": str(item.get("quantity", "")).strip(),
                }
            )
        elif isinstance(item, str):
            normalized_ingredients.append(
                {
                    "name": item.strip(),
                    "quantity": "",
                }
            )

    result["ingredients"] = normalized_ingredients

    if result.get("title") is None:
        result["title"] = "Recipe Detail"

    if result.get("why_chosen") is None:
        result["why_chosen"] = "Chosen from retrieved recipe candidates based on user ingredients."

    if result.get("source_recipe_title") is None:
        result["source_recipe_title"] = result.get("title", "")

    if result.get("grounded") is None:
        result["grounded"] = True

    return result


def generate_recipe_detail(data: RecipeDetailGenerateRequest) -> dict:
    recipe = get_recipe_by_id(data.recipe_id)

    return {
        "title": recipe.get("title", "Recipe Detail"),
        "why_chosen": f"Selected because it matches your ingredients: {', '.join(data.user_ingredients)}.",
        "ingredients": [
            {"name": str(item), "quantity": ""}
            for item in recipe.get("ingredients", [])
        ],
        "steps": [str(step) for step in recipe.get("instructions", [])],
        "substitutions": [],
        "nutrition_summary": {
            "calories": None,
            "protein_g": None,
            "carbs_g": None,
            "fats_g": None,
        },
        "warnings": [],
        "source_recipe_title": recipe.get("title", ""),
        "grounded": True,
    }