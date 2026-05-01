"""Phase 0 — validate Chroma persistence.

First run downloads ~80MB ONNX embedder for Chroma's default function. Subsequent
runs are instant. In production we pass our own Vertex-embedded vectors and never
touch this default model.
"""
import chromadb

client = chromadb.PersistentClient(path="data/chroma")
collection = client.get_or_create_collection(name="smoke_test")
collection.upsert(
    ids=["1", "2"],
    documents=["I love Lisbon", "I love Tokyo"],
    metadatas=[{"city": "Lisbon"}, {"city": "Tokyo"}],
)
results = collection.query(query_texts=["coastal European capital"], n_results=2)
print(results["documents"])
