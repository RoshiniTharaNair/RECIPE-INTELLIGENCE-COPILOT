import re
from typing import List, Set, Tuple

CANONICAL_MAP = {
    "paneer": "cheese",
    "mozzarella": "cheese",
    "cheddar": "cheese",
    "cottage cheese": "cheese",
    "indian cottage cheese": "cheese",
    "cheese": "cheese",

    "curd": "yogurt",
    "yoghurt": "yogurt",
    "yogurt": "yogurt",

    "capsicum": "bell_pepper",
    "bell pepper": "bell_pepper",
    "green pepper": "bell_pepper",
    "red pepper": "bell_pepper",
    "yellow pepper": "bell_pepper",

    "brinjal": "eggplant",
    "aubergine": "eggplant",
    "eggplant": "eggplant",

    "palak": "spinach",
    "spinach": "spinach",

    "tomatoes": "tomato",
    "tomato": "tomato",

    "basmati rice": "rice",
    "brown rice": "rice",
    "white rice": "rice",
    "jasmine rice": "rice",
    "rice": "rice",

    "scallion": "onion",
    "scallions": "onion",
    "spring onion": "onion",
    "green onion": "onion",
    "red onion": "onion",
    "white onion": "onion",
    "onions": "onion",
    "onion": "onion",

    "garlic": "garlic",
    "chicken": "chicken",
    "eggs": "egg",
    "egg": "egg",
}

UNITS = {"g", "kg", "ml", "l", "tbsp", "tsp", "cup", "cups"}


def normalize_text(text: str) -> str:
    t = (text or "").lower().replace("-", " ")
    t = re.sub(r"[^a-z\s]", " ", t)
    tokens = [x for x in t.split() if x not in UNITS and not x.isdigit()]
    return " ".join(tokens)


def canonicalize_ingredient(item: str) -> str | None:
    t = normalize_text(item)
    if not t:
        return None

    for raw in sorted(CANONICAL_MAP, key=len, reverse=True):
        pattern = r"\b" + re.escape(raw) + r"\b"
        if re.search(pattern, t):
            return CANONICAL_MAP[raw]

    return t


def canonicalize_ingredient_list(items: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()

    for item in items or []:
        c = canonicalize_ingredient(item)
        if c and c not in seen:
            seen.add(c)
            out.append(c)

    return out


def canonical_overlap(
    user_ingredients: List[str],
    recipe_ingredients: List[str],
) -> Tuple[List[str], List[str]]:
    user = canonicalize_ingredient_list(user_ingredients)
    recipe = canonicalize_ingredient_list(recipe_ingredients)

    matched = [u for u in user if u in recipe]
    extras = [r for r in recipe if r not in user]
    return matched, extras


def canonical_search_terms(item: str) -> Set[str]:
    canonical = canonicalize_ingredient(item)
    if not canonical:
        return set()

    terms = {canonical}

    for raw, canon in CANONICAL_MAP.items():
        if canon == canonical:
            terms.add(raw)

    return terms