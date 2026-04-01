from app.services.recipe_data import load_recipes
from app.services.embeddings import build_embedding_text, embed_texts

recipes = load_recipes()[:3]
texts = [build_embedding_text(r) for r in recipes]

print("TEXT SAMPLE:")
for i, t in enumerate(texts, 1):
    print(f"{i}. {t[:200]}")

embeddings = embed_texts(texts)
print("EMBEDDING SHAPE:", embeddings.shape)