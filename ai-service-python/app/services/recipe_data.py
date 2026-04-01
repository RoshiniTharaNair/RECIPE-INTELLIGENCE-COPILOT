import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "recipes_kaggle_indian.json"

def load_recipes() -> list[dict]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_recipe_by_id(recipe_id: str) -> dict:
    for recipe in load_recipes():
        if recipe.get("id") == recipe_id:
            return recipe
    raise ValueError(f"Recipe not found: {recipe_id}")