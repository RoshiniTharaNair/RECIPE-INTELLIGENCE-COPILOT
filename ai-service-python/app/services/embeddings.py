from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None


def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def build_embedding_text(recipe: dict) -> str:
    parts = [
        recipe.get("title", ""),
        recipe.get("description", ""),
        recipe.get("cuisine", ""),
        " ".join(recipe.get("dietary_info", [])),
        recipe.get("spice_level", ""),
        " ".join(recipe.get("ingredients", [])),
        " ".join(recipe.get("tags", [])),
    ]
    return " | ".join(part for part in parts if part).strip()


def embed_texts(texts: list[str]):
    model = get_embedding_model()
    return model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=False,
    )