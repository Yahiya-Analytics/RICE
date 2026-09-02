# registry/registry.py

# ── Stage → Adapter class mapping ─────────
# filled as we build each adapter

from adapters.ingestion_adapter  import IngestionAdapter
from adapters.chunking_adapter   import ChunkingAdapter
from adapters.embeddings_adapter import EmbeddingsAdapter
from adapters.vectordb_adapter   import VectorDBAdapter
from adapters.retrieval_adapter  import RetrievalAdapter
from adapters.rag_adapter        import RAGAdapter
from adapters.llm_adapter        import LLMAdapter

STAGE_REGISTRY = {
    "ingestion":  IngestionAdapter,
    "chunking":   ChunkingAdapter,
    "embeddings": EmbeddingsAdapter,
    "vector_db":  VectorDBAdapter,
    "retrieval":  RetrievalAdapter,
    "rag":        RAGAdapter,
    "llm":        LLMAdapter,
}

import os
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
# ── Container images ───────────────────────
IMAGE_REGISTRY = {
    "ingestion":  "localhost/rice/ingestion:latest",
    "embeddings": "localhost/rice/embeddings:latest",
    "llm":        "docker.io/ollama/ollama:latest",
    # chroma and chunking = pure python, no image
}

# ── Container ports ────────────────────────
PORT_REGISTRY = {
    "ingestion":  ("5001", "5001"),
    "embeddings": ("7997", "7997"),
    "llm":        ("11434", "11434"),
}

# ── Health check URLs ──────────────────────
HEALTH_REGISTRY = {
    "ingestion":  "http://localhost:5001/health",
    "embeddings": "http://localhost:7997/health",
    "llm":        "http://localhost:11434/api/tags",
}

# ── Volume mounts ──────────────────────────
VOLUME_REGISTRY = {
    "ingestion":  [f"{PROJECT_ROOT}/data:/data:ro", f"{PROJECT_ROOT}/.rice_cache:/cache:rw"],
    "embeddings": [f"{PROJECT_ROOT}/.rice_cache:/cache:rw"],
    "llm":        ["ollama_models:/root/.ollama"],
}

# ── RAM requirements per stage (GB) ───────
RAM_REQUIREMENTS = {
    "ingestion":  2.0,
    "chunking":   0.5,   # pure python
    "embeddings": 2.0,
    "vector_db":  0.3,   # pure python
    "retrieval":  0.3,   # pure python
    "llm":        4.0,
}

# ── Which stages need containers ──────────
NEEDS_CONTAINER = {
    "ingestion":  True,
    "chunking":   False,   # pure python
    "embeddings": True,
    "vector_db":  False,   # chroma = pure python for POC
    "retrieval":  False,   # pure python
    "llm":        False,
}