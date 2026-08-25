# models.py
from dataclasses import dataclass, field
from typing import List, Optional

# ── Runtime ──────────────────────────────
@dataclass
class RuntimeConfig:
    execution: str         = "sequential"
    ram_budget_gb: int     = 6
    cache_between_stages: bool = True
    auto_cleanup: bool     = True

# ── Ingestion ─────────────────────────────
@dataclass
class IngestionParserConfig:
    tool: str              = "docling"

@dataclass
class IngestionCacheConfig:
    enabled: bool          = True
    cache_dir: str         = ".rice_cache/ingestion"

@dataclass
class IngestionConfig:
    source: str            = "./data/"
    formats: List[str]     = field(default_factory=lambda: ["pdf"])
    batch_size: int        = 5
    parser: IngestionParserConfig = field(default_factory=IngestionParserConfig)
    cache: IngestionCacheConfig   = field(default_factory=IngestionCacheConfig)

# ── Chunking ──────────────────────────────
@dataclass
class RecursiveConfig:
    target_tokens: int     = 512
    overlap_tokens: int    = 50

@dataclass
class ChunkingCacheConfig:
    enabled: bool          = True
    cache_dir: str         = ".rice_cache/chunking"

@dataclass
class ChunkingConfig:
    strategy: str          = "recursive"
    recursive: RecursiveConfig    = field(default_factory=RecursiveConfig)
    cache: ChunkingCacheConfig    = field(default_factory=ChunkingCacheConfig)

# ── Embeddings ────────────────────────────
@dataclass
class EmbeddingsServingConfig:
    backend: str           = "infinity"
    host: str              = "localhost"
    port: int              = 7997

@dataclass
class EmbeddingsModelParams:
    dimensions: int        = 384
    normalize: bool        = True
    batch_size: int        = 32

@dataclass
class EmbeddingsCacheConfig:
    enabled: bool          = True
    cache_dir: str         = ".rice_cache/embeddings"

@dataclass
class EmbeddingsConfig:
    provider: str          = "huggingface"
    model: str             = "BAAI/bge-small-en-v1.5"
    type: str              = "dense"
    serving: EmbeddingsServingConfig = field(default_factory=EmbeddingsServingConfig)
    model_params: EmbeddingsModelParams = field(default_factory=EmbeddingsModelParams)
    cache: EmbeddingsCacheConfig       = field(default_factory=EmbeddingsCacheConfig)

# ── Vector DB ─────────────────────────────
@dataclass
class VectorDBLocalConfig:
    path: str              = ".rice_cache/vectordb"

@dataclass
class VectorDBIndexConfig:
    metric: str            = "cosine"
    dimensions: int        = 384

@dataclass
class VectorDBConfig:
    backend: str           = "chroma"
    mode: str              = "local"
    local: VectorDBLocalConfig  = field(default_factory=VectorDBLocalConfig)
    index: VectorDBIndexConfig  = field(default_factory=VectorDBIndexConfig)

# ── Retrieval ─────────────────────────────
@dataclass
class RetrievalOutputConfig:
    return_chunks: bool    = True
    return_scores: bool    = True
    return_metadata: bool  = True

@dataclass
class RetrievalConfig:
    top_k: int             = 5
    strategy: str          = "dense"
    output: RetrievalOutputConfig = field(default_factory=RetrievalOutputConfig)

# ── LLM ───────────────────────────────────
@dataclass
class LLMLocalConfig:
    backend: str           = "ollama"
    host: str              = "localhost"
    port: int              = 11434
    context_length: int    = 4096

@dataclass
class LLMSamplingConfig:
    temperature: float     = 0.3
    max_tokens: int        = 512

@dataclass
class LLMPromptConfig:
    system: str            = """
    You are a helpful assistant.
    Answer only from the provided context.
    If the answer is not in context say I don't know.
    """

@dataclass
class LLMConfig:
    provider: str          = "local"
    model: str             = "llama3.2:3b"
    local: LLMLocalConfig        = field(default_factory=LLMLocalConfig)
    sampling: LLMSamplingConfig  = field(default_factory=LLMSamplingConfig)
    prompt: LLMPromptConfig      = field(default_factory=LLMPromptConfig)

# ── Root Config ───────────────────────────
@dataclass
class RiceConfig:
    runtime:    RuntimeConfig    = field(default_factory=RuntimeConfig)
    ingestion:  IngestionConfig  = field(default_factory=IngestionConfig)
    chunking:   ChunkingConfig   = field(default_factory=ChunkingConfig)
    embeddings: EmbeddingsConfig = field(default_factory=EmbeddingsConfig)
    vector_db:  VectorDBConfig   = field(default_factory=VectorDBConfig)
    retrieval:  RetrievalConfig  = field(default_factory=RetrievalConfig)
    llm:        LLMConfig        = field(default_factory=LLMConfig)