# parser/parser.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tomllib
from models import (
    RiceConfig, RuntimeConfig,
    IngestionConfig, IngestionParserConfig, IngestionCacheConfig,
    ChunkingConfig, RecursiveConfig, ChunkingCacheConfig,
    EmbeddingsConfig, EmbeddingsServingConfig,
    EmbeddingsModelParams, EmbeddingsCacheConfig,
    VectorDBConfig, VectorDBLocalConfig, VectorDBIndexConfig,
    RetrievalConfig, RetrievalOutputConfig,
    LLMConfig, LLMLocalConfig, LLMSamplingConfig, LLMPromptConfig
)

class Parser:
    def __init__(self, toml_path: str):
        self.toml_path = toml_path

    def parse(self) -> RiceConfig:
        # Step 1: file → dict
        with open(self.toml_path, "rb") as f:
            raw = tomllib.load(f)

        # Step 2: dict → objects
        return RiceConfig(
            runtime    = self._parse_runtime(raw.get("runtime", {})),
            ingestion  = self._parse_ingestion(raw.get("ingestion", {})),
            chunking   = self._parse_chunking(raw.get("chunking", {})),
            embeddings = self._parse_embeddings(raw.get("embeddings", {})),
            vector_db  = self._parse_vectordb(raw.get("vector_db", {})),
            retrieval  = self._parse_retrieval(raw.get("retrieval", {})),
            llm        = self._parse_llm(raw.get("llm", {})),
        )

    def _parse_runtime(self, raw: dict) -> RuntimeConfig:
        return RuntimeConfig(
            execution            = raw.get("execution", "sequential"),
            ram_budget_gb        = raw.get("ram_budget_gb", 6),
            cache_between_stages = raw.get("cache_between_stages", True),
            auto_cleanup         = raw.get("auto_cleanup", True),
        )

    def _parse_ingestion(self, raw: dict) -> IngestionConfig:
        parser_raw = raw.get("parser", {})
        cache_raw  = raw.get("cache", {})
        return IngestionConfig(
            source     = raw.get("source", "./data/"),
            formats    = raw.get("formats", ["pdf"]),
            batch_size = raw.get("batch_size", 5),
            parser = IngestionParserConfig(
                tool = parser_raw.get("tool", "docling"),
            ),
            cache = IngestionCacheConfig(
                enabled   = cache_raw.get("enabled", True),
                cache_dir = cache_raw.get("cache_dir", ".rice_cache/ingestion"),
            ),
        )

    def _parse_chunking(self, raw: dict) -> ChunkingConfig:
        recursive_raw = raw.get("recursive", {})
        cache_raw     = raw.get("cache", {})
        return ChunkingConfig(
            strategy = raw.get("strategy", "recursive"),
            recursive = RecursiveConfig(
                target_tokens = recursive_raw.get("target_tokens", 512),
                overlap_tokens = recursive_raw.get("overlap_tokens", 50),
            ),
            cache = ChunkingCacheConfig(
                enabled   = cache_raw.get("enabled", True),
                cache_dir = cache_raw.get("cache_dir", ".rice_cache/chunking"),
            ),
        )

    def _parse_embeddings(self, raw: dict) -> EmbeddingsConfig:
        serving_raw     = raw.get("serving", {})
        model_params_raw = raw.get("model_params", {})
        cache_raw       = raw.get("cache", {})
        return EmbeddingsConfig(
            provider = raw.get("provider", "huggingface"),
            model    = raw.get("model", "BAAI/bge-small-en-v1.5"),
            type     = raw.get("type", "dense"),
            serving = EmbeddingsServingConfig(
                backend = serving_raw.get("backend", "infinity"),
                host    = serving_raw.get("host", "localhost"),
                port    = serving_raw.get("port", 7997),
            ),
            model_params = EmbeddingsModelParams(
                dimensions = model_params_raw.get("dimensions", 384),
                normalize  = model_params_raw.get("normalize", True),
                batch_size = model_params_raw.get("batch_size", 32),
            ),
            cache = EmbeddingsCacheConfig(
                enabled   = cache_raw.get("enabled", True),
                cache_dir = cache_raw.get("cache_dir", ".rice_cache/embeddings"),
            ),
        )

    def _parse_vectordb(self, raw: dict) -> VectorDBConfig:
        local_raw = raw.get("local", {})
        index_raw = raw.get("index", {})
        return VectorDBConfig(
            backend = raw.get("backend", "chroma"),
            mode    = raw.get("mode", "local"),
            local = VectorDBLocalConfig(
                path = local_raw.get("path", ".rice_cache/vectordb"),
            ),
            index = VectorDBIndexConfig(
                metric     = index_raw.get("metric", "cosine"),
                dimensions = index_raw.get("dimensions", 384),
            ),
        )

    def _parse_retrieval(self, raw: dict) -> RetrievalConfig:
        output_raw = raw.get("output", {})
        return RetrievalConfig(
            top_k    = raw.get("top_k", 5),
            strategy = raw.get("strategy", "dense"),
            output = RetrievalOutputConfig(
                return_chunks   = output_raw.get("return_chunks", True),
                return_scores   = output_raw.get("return_scores", True),
                return_metadata = output_raw.get("return_metadata", True),
            ),
        )

    def _parse_llm(self, raw: dict) -> LLMConfig:
        local_raw    = raw.get("local", {})
        sampling_raw = raw.get("sampling", {})
        prompt_raw   = raw.get("prompt", {})
        return LLMConfig(
            provider = raw.get("provider", "local"),
            model    = raw.get("model", "llama3.2:3b"),
            local = LLMLocalConfig(
                backend        = local_raw.get("backend", "ollama"),
                host           = local_raw.get("host", "localhost"),
                port           = local_raw.get("port", 11434),
                context_length = local_raw.get("context_length", 4096),
            ),
            sampling = LLMSamplingConfig(
                temperature = sampling_raw.get("temperature", 0.3),
                max_tokens  = sampling_raw.get("max_tokens", 512),
            ),
            prompt = LLMPromptConfig(
                system = prompt_raw.get("system", "You are a helpful assistant."),
            ),
        )


# ── Test parser standalone ─────────────────
if __name__ == "__main__":
    parser = Parser("rice.toml")
    config = parser.parse()

    # verify every section parsed correctly
    print(f"project runtime:       {config.runtime.execution}")
    print(f"ingestion tool:        {config.ingestion.parser.tool}")
    print(f"ingestion source:      {config.ingestion.source}")
    print(f"chunking strategy:     {config.chunking.strategy}")
    print(f"chunking target_tokens:{config.chunking.recursive.target_tokens}")
    print(f"embeddings model:      {config.embeddings.model}")
    print(f"embeddings dimensions: {config.embeddings.model_params.dimensions}")
    print(f"embeddings port:       {config.embeddings.serving.port}")
    print(f"vector db backend:     {config.vector_db.backend}")
    print(f"vector db path:        {config.vector_db.local.path}")
    print(f"retrieval top_k:       {config.retrieval.top_k}")
    print(f"llm model:             {config.llm.model}")
    print(f"llm port:              {config.llm.local.port}")
    print(" parser working correctly")