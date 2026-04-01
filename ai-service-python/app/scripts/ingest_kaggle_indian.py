import json
import math
import re
from pathlib import Path

import pandas as pd

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "IndianHealthyRecipe.csv"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "recipes_kaggle_indian.json"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

UNITS = {
    "g", "kg", "mg", "ml", "l", "cup", "cups", "tbsp", "tsp", "teaspoon", "teaspoons",
    "tablespoon", "tablespoons", "pinch", "pinches", "oz", "ounce", "ounces", "lb", "lbs",
    "pound", "pounds", "mug", "mugs", "bunch", "bunches", "slice", "slices", "clove", "cloves",
    "inch", "inches"
}

PREP_WORDS = {
    "chopped", "finely", "roughly", "sliced", "thinly", "diced", "crushed", "grated", "minced",
    "peeled", "cubed", "washed", "rinsed", "boiled", "cooked", "uncooked", "fresh", "small",
    "medium", "large", "extra", "virgin", "optional", "to", "taste", "for", "garnish", "and",
    "or", "needed", "room", "temperature", "halved", "quartered"
}

KNOWN_INGREDIENT_PHRASES = [
    "red onion", "white onion", "spring onion", "green chili", "green chillies",
    "red chili", "red chillies", "chili powder", "coriander powder", "mustard seeds",
    "cumin seeds", "garam masala", "ginger garlic paste", "curry leaves", "basmati rice",
    "brown rice", "olive oil", "coconut oil", "black pepper", "lemon juice", "tomato puree"
]


def safe_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def parse_int_from_text(value):
    text = safe_str(value)
    if not text:
        return None
    match = re.search(r"\d+", text)
    return int(match.group()) if match else None


def parse_time_minutes(value):
    text = safe_str(value).lower()
    if not text:
        return None

    total = 0
    hr_match = re.search(r"(\d+)\s*h", text)
    min_match = re.search(r"(\d+)\s*m", text)

    if hr_match:
        total += int(hr_match.group(1)) * 60
    if min_match:
        total += int(min_match.group(1))

    if total > 0:
        return total

    match = re.search(r"\d+", text)
    return int(match.group()) if match else None


def split_list_text(value):
    text = safe_str(value)
    if not text:
        return []

    # Try Python-list-like strings: "['A', 'B']"
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if inner:
            parts = [p.strip().strip("'").strip('"') for p in inner.split(",")]
            return [p for p in parts if p]
        return []

    if "\n" in text:
        parts = [x.strip(" -•\t\r") for x in text.split("\n")]
        parts = [p for p in parts if p]
        if parts:
            return parts

    parts = [x.strip() for x in text.split(",")]
    return [p for p in parts if p]


def clean_ingredient_line(line: str) -> str:
    text = safe_str(line).lower()

    # remove leading numbering like "1)" or "2."
    text = re.sub(r"^\s*\d+\s*[\)\.\-:]*\s*", "", text)

    # remove bracketed text
    text = re.sub(r"\([^)]*\)", " ", text)

    # normalize separators
    text = text.replace("/", " ").replace("\\", " ").replace("-", " ")

    # remove numbers and fractions
    text = re.sub(r"\b\d+(\.\d+)?\b", " ", text)
    text = re.sub(r"\b\d+\s*/\s*\d+\b", " ", text)

    # remove units
    unit_pattern = r"\b(" + "|".join(re.escape(u) for u in sorted(UNITS, key=len, reverse=True)) + r")\b"
    text = re.sub(unit_pattern, " ", text)

    # collapse whitespace
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # first, detect known multi-word phrases
    found_phrases = [phrase for phrase in KNOWN_INGREDIENT_PHRASES if phrase in text]
    if found_phrases:
        # keep the longest matching phrase
        found_phrases.sort(key=len, reverse=True)
        return found_phrases[0]

    tokens = [t for t in text.split() if t not in PREP_WORDS]
    if not tokens:
        return ""

    # heuristic: keep last 1-2 meaningful words
    if len(tokens) >= 2:
        candidate = " ".join(tokens[-2:])
    else:
        candidate = tokens[-1]

    return candidate.strip()


def clean_ingredients(ingredients_raw: list[str]) -> list[str]:
    cleaned = []
    seen = set()

    for item in ingredients_raw:
        c = clean_ingredient_line(item)
        if c and c not in seen:
            cleaned.append(c)
            seen.add(c)

    return cleaned


def normalize_row(row, idx):
    title = safe_str(row.get("Dish Name"))
    description = safe_str(row.get("Description"))
    spice = safe_str(row.get("Spice"))
    prep_time = parse_time_minutes(row.get("Prep Time"))
    cook_time = parse_time_minutes(row.get("Cook Time"))
    views = parse_int_from_text(row.get("Views"))

    try:
        rating = float(row.get("Rating")) if safe_str(row.get("Rating")) else None
    except Exception:
        rating = None

    votes = parse_int_from_text(row.get("Number of Votes"))
    heat = safe_str(row.get("Heat"))
    serves = parse_int_from_text(row.get("Serves"))

    dietary_info = split_list_text(row.get("Dietary Info"))

    ingredients_raw = (
        split_list_text(row.get("Ingredents"))
        or split_list_text(row.get("Ingredients"))
    )
    ingredients_clean = clean_ingredients(ingredients_raw)

    instructions = split_list_text(row.get("Instructions"))

    total_time = None
    if prep_time is not None or cook_time is not None:
        total_time = (prep_time or 0) + (cook_time or 0)

    tags = []
    if spice:
        tags.append(spice)
    if heat and heat not in tags:
        tags.append(heat)
    for item in dietary_info:
        if item not in tags:
            tags.append(item)

    return {
        "id": f"kaggle_indian_{idx}",
        "title": title,
        "description": description,
        "cuisine": "Indian",
        "dietary_info": dietary_info,
        "spice_level": spice or heat,
        "prep_time_mins": prep_time,
        "cook_time_mins": cook_time,
        "total_time_mins": total_time,
        "servings": serves,
        "ingredients_raw": ingredients_raw,
        "ingredients_clean": ingredients_clean,
        "ingredients": ingredients_clean,
        "instructions": instructions,
        "rating": rating,
        "review_count": votes,
        "popularity": views,
        "tags": tags,
        "source": "kaggle_healthy_indian_recipes"
    }


def main():
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Raw file not found: {RAW_PATH}")

    df = pd.read_csv(RAW_PATH)

    print("\nLoaded rows:", len(df))
    print("Columns found:")
    print(df.columns.tolist())
    print("\nFirst 3 rows preview:")
    print(df.head(3).to_string())

    normalized = []
    for idx, row in df.iterrows():
        item = normalize_row(row.to_dict(), idx)

        if item["title"] and item["ingredients_clean"]:
            normalized.append(item)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(normalized)} normalized recipes to:")
    print(OUT_PATH)

    if normalized:
        print("\nSample normalized record:")
        print(json.dumps(normalized[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()