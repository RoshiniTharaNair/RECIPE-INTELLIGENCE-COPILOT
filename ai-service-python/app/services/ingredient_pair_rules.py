from typing import Iterable

PAIR_BOOSTS = {
    frozenset({"spinach", "cheese"}): 0.25,
    frozenset({"tomato", "rice"}): 0.18,
    frozenset({"chicken", "cheese"}): 0.18,
    frozenset({"tomato", "garlic"}): 0.10,
    frozenset({"bread", "cheese"}): 0.10,
}


def compute_pair_bonus(
    user_items: Iterable[str],
    recipe_items: Iterable[str],
    extra_major_count: int = 0,
) -> float:
    user_set = set(user_items)
    recipe_set = set(recipe_items)

    # guard: do not reward noisy recipes too much
    if extra_major_count >= 4:
        return 0.0

    bonus = 0.0
    for pair, weight in PAIR_BOOSTS.items():
        if pair.issubset(user_set) and pair.issubset(recipe_set):
            bonus += weight

    return bonus