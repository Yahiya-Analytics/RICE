# orchestrator/orchestrator.py
from orchestrator.lifecycle import Lifecycle
from registry.registry import NEEDS_CONTAINER
from adapters.ingestion_adapter  import IngestionAdapter
from adapters.chunking_adapter   import ChunkingAdapter
from adapters.embeddings_adapter import EmbeddingsAdapter
from adapters.vectordb_adapter   import VectorDBAdapter
from adapters.retrieval_adapter  import RetrievalAdapter
from adapters.rag_adapter        import RAGAdapter
from adapters.llm_adapter        import LLMAdapter

class Orchestrator:
    def __init__(self, config):
        self.config = config
        self.lc     = Lifecycle()

    def run(self, query: str):
        cfg = self.config
        lc  = self.lc
        import os
        print("\n" + "="*50)
        print(" RICE Pipeline Starting")
        print("="*50 + "\n")

        # ── Stage 1: Ingestion
        ingestion_cache = cfg.ingestion.cache.cache_dir
        if os.path.exists(os.path.join(ingestion_cache, "output.json")):
            print("⚡ Ingestion cache found — skipping")
        else:
            print("\n── Stage 1: Ingestion ──")
            lc.check_ram("ingestion", cfg.runtime.ram_budget_gb)
            lc.start("ingestion")
            lc.health_check("ingestion")
            documents = IngestionAdapter(cfg.ingestion).run()
            lc.save_cache("ingestion", documents, ingestion_cache)
            lc.stop("ingestion")

        # ── Stage 2: Chunking: Pure python — no container
        chunking_cache = cfg.chunking.cache.cache_dir
        if os.path.exists(os.path.join(chunking_cache, "output.json")):
            print("⚡ Chunking cache found — skipping")
        else:
            print("\n── Stage 2: Chunking ──")
            lc.check_ram("chunking", cfg.runtime.ram_budget_gb)
            documents = lc.load_cache("ingestion",ingestion_cache)
            chunks = ChunkingAdapter(cfg.chunking).run(documents)
            lc.save_cache("chunking", chunks,chunking_cache)

        # ── Stage 3: Embeddings
        embeddings_cache = cfg.embeddings.cache.cache_dir
        if os.path.exists(os.path.join(embeddings_cache, "output.json")):
            print("⚡ Embeddings cache found — skipping")
        else:
            print("\n── Stage 3: Embeddings ──")
            lc.check_ram("embeddings", cfg.runtime.ram_budget_gb)
            lc.start("embeddings")
            lc.health_check("embeddings")
            chunks = lc.load_cache("chunking",chunking_cache)
            embedded = EmbeddingsAdapter(cfg.embeddings).run(chunks)
            lc.save_cache("embeddings", embedded,embeddings_cache)
            lc.stop("embeddings")

        # ── Stage 4: Vector DB: Pure python (chroma)
        print("\n── Stage 4: Vector DB ──")
        lc.check_ram("vector_db", cfg.runtime.ram_budget_gb)
        embedded = lc.load_cache("embeddings", embeddings_cache)
        vdb = VectorDBAdapter(cfg.vector_db)
        collection = vdb.run(embedded)

        # ── Stage 5: Retrieval: Embeddings container still needed for query embedding
        print("\n── Stage 5: Retrieval ──")
        lc.check_ram("embeddings", cfg.runtime.ram_budget_gb)
        lc.start("embeddings")
        lc.health_check("embeddings")
        retriever = RetrievalAdapter(cfg.retrieval, cfg.embeddings)
        chunks    = retriever.run((collection, query))
        lc.stop("embeddings")

        # ── Stage 6: RAG ───────────────────
        print("\n── Stage 6: RAG ──")
        prompt = RAGAdapter(cfg.llm).run((chunks, query))

        # ── Stage 7: LLM ───────────────────
        print("\n── Stage 7: LLM ──")
        lc.check_ram("llm", cfg.runtime.ram_budget_gb)
        lc.start("llm")
        lc.health_check("llm")
        answer = LLMAdapter(cfg.llm).run(prompt)

        print("\n" + "="*50)
        print(" RICE Pipeline Complete")
        print("="*50)
        return answer, chunks