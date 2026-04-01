from app.models.schemas import RecipeGenerateRequest
from app.services.generator import build_deterministic_recipe


def test_build_deterministic_recipe_spinach_paneer_retrieval_grounded():
    data = RecipeGenerateRequest(
        ingredients=["spinach", "paneer"],
        prep_time=15,
        skill_level="beginner",
    )

    recipe = build_deterministic_recipe(
        data,
        retrieved_candidates=[{"title": "Saag Paneer"}],
    )

    assert recipe["title"] == "Saag Paneer"
    assert recipe["template_name"] == "saag_paneer"
    assert recipe["grounding_source"] == "retrieval_grounded"
    assert recipe["match_score"] == 1.0
    assert recipe["warnings"] == []


def test_build_deterministic_recipe_bread_cheese_template_only():
    data = RecipeGenerateRequest(
        ingredients=["bread", "cheese"],
    )

    recipe = build_deterministic_recipe(
        data,
        retrieved_candidates=[],
    )

    assert recipe["title"] == "Cheese Toast"
    assert recipe["template_name"] == "cheese_toast"
    assert recipe["grounding_source"] == "template_only"
    assert recipe["match_score"] == 1.0
    assert recipe["warnings"] == []


def test_build_deterministic_recipe_generic_fallback_low_confidence():
    data = RecipeGenerateRequest(
        ingredients=["abc", "xyz"],
    )

    recipe = build_deterministic_recipe(
        data,
        retrieved_candidates=[],
    )

    assert recipe["title"] == "Custom Abc Xyz Recipe"
    assert recipe["template_name"] == "generic_fallback"
    assert recipe["grounding_source"] == "template_only"
    assert recipe["match_score"] == 0.25
    assert len(recipe["warnings"]) >= 1
    assert "Low-confidence generated fallback" in recipe["warnings"][0]


def test_generate_api_returns_expected_shape(client, monkeypatch):
    from app.api.routes import generate as generate_route

    def fake_generate_recipes(_data):
        return {
            "recipes": [
                {
                    "title": "Saag Paneer",
                    "why_chosen": "Built from spinach and paneer with an Indian-style template.",
                    "ingredients": [
                        {"name": "spinach", "quantity": "3 cups"},
                        {"name": "paneer", "quantity": "200 g"},
                    ],
                    "steps": [
                        "Wash and chop the spinach.",
                        "Cook and serve.",
                    ],
                    "substitutions": [],
                    "nutrition_summary": {
                        "calories": None,
                        "protein_g": None,
                        "carbs_g": None,
                        "fats_g": None,
                    },
                    "warnings": [],
                    "match_score": 1.0,
                    "matched_input_ingredients": ["spinach", "paneer"],
                    "extra_major_ingredients": [],
                    "template_name": "saag_paneer",
                    "grounding_source": "retrieval_grounded",
                }
            ],
            "meta": {
                "latency_ms": 120,
                "model_name": "deterministic_generator",
                "recipe_count": 1,
                "input_ingredients": ["spinach", "paneer"],
                "quality_notes": [
                    "Recipe was assembled deterministically using retrieved grounding."
                ],
            },
        }

    monkeypatch.setattr(generate_route, "generate_recipes", fake_generate_recipes)

    response = client.post(
        "/generate",
        json={
            "ingredients": ["spinach", "paneer"],
            "prep_time": 15,
            "skill_level": "beginner",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["meta"]["recipe_count"] == 1
    assert body["meta"]["model_name"] == "deterministic_generator"

    recipe = body["recipes"][0]
    assert recipe["title"] == "Saag Paneer"
    assert recipe["template_name"] == "saag_paneer"
    assert recipe["grounding_source"] == "retrieval_grounded"

def test_build_deterministic_recipe_tomato_onion_template():
    data = RecipeGenerateRequest(ingredients=["tomato", "onion"])
    recipe = build_deterministic_recipe(data, retrieved_candidates=[])

    assert recipe["title"] == "Tomato Onion Sauté"
    assert recipe["template_name"] == "tomato_onion_saute"
    assert recipe["grounding_source"] == "template_only"
    assert recipe["warnings"] == []


def test_build_deterministic_recipe_onion_rice_template():
    data = RecipeGenerateRequest(ingredients=["rice", "onion"])
    recipe = build_deterministic_recipe(data, retrieved_candidates=[])

    assert recipe["title"] == "Onion Rice"
    assert recipe["template_name"] == "onion_rice"
    assert recipe["grounding_source"] == "template_only"


def test_build_deterministic_recipe_tomato_pasta_template():
    data = RecipeGenerateRequest(ingredients=["pasta", "tomato"])
    recipe = build_deterministic_recipe(data, retrieved_candidates=[])

    assert recipe["title"] == "Tomato Pasta"
    assert recipe["template_name"] == "tomato_pasta"
    assert recipe["grounding_source"] == "template_only"


def test_build_deterministic_recipe_potato_onion_template():
    data = RecipeGenerateRequest(ingredients=["potato", "onion"])
    recipe = build_deterministic_recipe(data, retrieved_candidates=[])

    assert recipe["title"] == "Potato Onion Skillet"
    assert recipe["template_name"] == "potato_onion_skillet"
    assert recipe["grounding_source"] == "template_only"


def test_build_deterministic_recipe_egg_tomato_template():
    data = RecipeGenerateRequest(ingredients=["egg", "tomato"])
    recipe = build_deterministic_recipe(data, retrieved_candidates=[])

    assert recipe["title"] == "Scrambled Egg with Tomato"
    assert recipe["template_name"] == "scrambled_egg_tomato"
    assert recipe["grounding_source"] == "template_only"


def test_build_deterministic_recipe_capsicum_normalizes_to_bell_pepper():
    data = RecipeGenerateRequest(ingredients=["capsicum", "onion"])
    recipe = build_deterministic_recipe(data, retrieved_candidates=[])

    assert recipe["title"] == "Bell Pepper Onion Stir-Fry"
    assert recipe["template_name"] == "bell_pepper_onion_stir_fry"


def test_build_deterministic_recipe_curd_normalizes_to_yogurt():
    data = RecipeGenerateRequest(ingredients=["curd", "onion"])
    recipe = build_deterministic_recipe(data, retrieved_candidates=[])

    assert recipe["title"] == "Yogurt Onion Dip"
    assert recipe["template_name"] == "yogurt_onion_dip"


def test_generate_api_template_only_quality_note(client, monkeypatch):
    from app.api.routes import generate as generate_route

    def fake_generate_recipes(_data):
        return {
            "recipes": [
                {
                    "title": "Onion Rice",
                    "why_chosen": "Built from rice and onion using a quick pan-finished rice template.",
                    "ingredients": [
                        {"name": "rice", "quantity": "1 cup"},
                        {"name": "onion", "quantity": "1 medium"},
                    ],
                    "steps": ["Cook rice.", "Cook onion.", "Mix and serve."],
                    "substitutions": [],
                    "nutrition_summary": {
                        "calories": None,
                        "protein_g": None,
                        "carbs_g": None,
                        "fats_g": None,
                    },
                    "warnings": [],
                    "match_score": 1.0,
                    "matched_input_ingredients": ["rice", "onion"],
                    "extra_major_ingredients": [],
                    "template_name": "onion_rice",
                    "grounding_source": "template_only",
                }
            ],
            "meta": {
                "latency_ms": 100,
                "model_name": "deterministic_generator",
                "recipe_count": 1,
                "input_ingredients": ["rice", "onion"],
                "quality_notes": [
                    "No strong retrieved candidates were available, so recipe was assembled from user ingredients."
                ],
            },
        }

    monkeypatch.setattr(generate_route, "generate_recipes", fake_generate_recipes)

    response = client.post("/generate", json={"ingredients": ["rice", "onion"]})
    assert response.status_code == 200

    body = response.json()
    assert body["recipes"][0]["grounding_source"] == "template_only"
    assert body["meta"]["quality_notes"] == [
        "No strong retrieved candidates were available, so recipe was assembled from user ingredients."
    ]