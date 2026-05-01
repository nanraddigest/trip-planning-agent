"""Phase 0 — validate Vertex AI embeddings."""
import os

from dotenv import load_dotenv
from langchain_google_vertexai import VertexAIEmbeddings

load_dotenv()

emb = VertexAIEmbeddings(
    model_name="text-embedding-005",
    project=os.environ["GCP_PROJECT_ID"],
    location=os.environ.get("GCP_REGION", "us-central1"),
)

vectors = emb.embed_documents([
    "Lisbon is a coastal capital known for its trams and seafood.",
    "Tokyo is a sprawling metropolis with deep traditional roots.",
])
print(f"Embedded 2 docs. Vector dim: {len(vectors[0])}")
print(f"First 5 dims of doc 1: {vectors[0][:5]}")
