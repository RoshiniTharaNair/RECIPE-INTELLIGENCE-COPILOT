from typing import Iterable, List
from app.services.ingredient_knowledge import canonicalize_ingredient_list, normalize_text

DIETARY_PREFERENCE_AVOIDS = {
    "vegetarian": {"chicken", "egg", "eggs", "fish", "mutton", "beef", "pork", "prawn", "shrimp", "lamb", "bacon", "ham", "turkey", "salmon", "tuna"},
    "egg free": {"egg", "eggs"},
    "dairy free": {"milk", "butter", "cheese", "paneer", "curd", "yogurt", "yoghurt", "cream", "ghee", "mozzarella", "cheddar", "cottage cheese"},
}
def normalize_dietary_preferences(items: Iterable[str] | None) -> List[str]:
    out, seen = [], set()
    for item in items or []:
        value = normalize_text(item)
        if value in DIETARY_PREFERENCE_AVOIDS and value not in seen:
            seen.add(value)
            out.append(value)
    return out

def get_preference_avoid_ingredients(items: Iterable[str] | None) -> List[str]:
    out, seen = [], set()
    for pref in normalize_dietary_preferences(items):
        for item in canonicalize_ingredient_list(list(DIETARY_PREFERENCE_AVOIDS[pref])):
            if item not in seen:
                seen.add(item)
                out.append(item)
    return out

def merge_avoid_ingredients(explicit_avoid: Iterable[str] | None, dietary_preferences: Iterable[str] | None) -> List[str]:
    out, seen = [], set()
    merged = canonicalize_ingredient_list(list(explicit_avoid or [])) + get_preference_avoid_ingredients(dietary_preferences)
    for item in merged:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out