from typing import List, Set

CANONICAL_SYNONYMS = {
    "onion": {"red onion", "white onion", "spring onion", "green onion", "onions", "scallion", "scallions"},
    "rice": {"basmati rice", "brown rice", "jasmine rice", "white rice", "cooked rice"},
    "tomato": {"tomatoes", "tomato puree", "tomato sauce", "cherry tomato", "cherry tomatoes"},
    "chili": {"green chili", "green chillies", "red chili", "red chillies", "chilli", "chilies"},
    "jeera": {"cumin", "cumin seeds"},
    "cumin": {"jeera", "cumin seeds"},
    "capsicum": {"bell pepper", "green pepper", "red pepper", "yellow pepper"},
    "bell pepper": {"capsicum", "green pepper", "red pepper", "yellow pepper"},
    "coriander": {"cilantro", "fresh coriander"},
    "cilantro": {"coriander", "fresh coriander"},
    "curd": {"yogurt", "plain yogurt", "yoghurt"},
    "yogurt": {"curd", "plain yogurt", "yoghurt"},
    "aubergine": {"eggplant", "brinjal"},
    "eggplant": {"aubergine", "brinjal"},
    "brinjal": {"eggplant", "aubergine"},
    "chickpeas": {"garbanzo beans", "chana"},
    "garbanzo beans": {"chickpeas", "chana"},
    "chana": {"chickpeas", "garbanzo beans"},
    "cheese": {"paneer", "cottage cheese", "mozzarella", "cheddar"},
    "paneer": {"cheese", "cottage cheese", "indian cottage cheese"},
}


def normalize_text(text: str) -> str:
    return text.strip().lower()


def expand_query_terms(ingredient: str) -> Set[str]:
    ing = normalize_text(ingredient)
    terms = {ing}

    for base, variants in CANONICAL_SYNONYMS.items():
        if ing == base or ing in variants:
            terms.add(base)
            terms.update(variants)

    return terms


def ingredient_matches(input_ingredient: str, recipe_ingredient: str) -> bool:
    recipe_ing = normalize_text(recipe_ingredient)
    for term in expand_query_terms(input_ingredient):
        if term == recipe_ing or term in recipe_ing or recipe_ing in term:
            return True
    return False


def normalize_ingredient_list(items: List[str]) -> List[str]:
    return [normalize_text(item) for item in items if item and item.strip()]