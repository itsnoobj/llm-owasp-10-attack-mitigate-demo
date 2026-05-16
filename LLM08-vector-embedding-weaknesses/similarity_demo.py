"""Semantic similarity ≠ factual alignment — live demo."""
import numpy as np
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

ef = DefaultEmbeddingFunction()

sentences = [
    "I love this product",
    "I hate this product",
    "The weather is nice",
]

embeddings = ef(sentences)

def cosine(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

love_hate = cosine(embeddings[0], embeddings[1])
love_weather = cosine(embeddings[0], embeddings[2])

print("\n🧠 Semantic Similarity Demo")
print("=" * 50)
print(f'\n  "I love this product"  vs  "I hate this product"')
print(f"   Similarity: {love_hate:.4f}")
print(f'\n  "I love this product"  vs  "The weather is nice"')
print(f"   Similarity: {love_weather:.4f}")
print(f"\n{'=' * 50}")
if love_hate > love_weather:
    print("  ⚠️  Love/Hate are MORE similar than Love/Weather!")
    print("  → Semantic similarity ≠ factual alignment")
print()
