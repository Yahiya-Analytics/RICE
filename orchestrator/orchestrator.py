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

from utils.timer import StageTimer
from utils.hasher import CacheHasher

class Orchestrator:
    def __init__(self, config):
        self.config = config
        self.lc     = Lifecycle()
        self.timer  = StageTimer()
        self.hasher = CacheHasher()

    def run(self, query: str):
        cfg = self.config
        lc  = self.lc
        import os
        print(" RICE Pipeline Starting")
        print("--"*30 + "\n")

        # Stage 1: Ingestion
        ingestion_cache = cfg.ingestion.cache.cache_dir
        if os.path.exists(os.path.join(ingestion_cache, "output.json")):
            self.hasher.verify("ingestion", ingestion_cache)
            print("⚡ Ingestion cache found — skipping")
            documents = lc.load_cache("ingestion", ingestion_cache)
        else:
            print("\n── Stage 1: Ingestion ──")
            lc.check_ram("ingestion", cfg.runtime.ram_budget_gb)
            lc.start("ingestion")
            lc.health_check("ingestion")
            #Addition of Time module 
            self.timer.start("ingestion")
            documents = IngestionAdapter(cfg.ingestion).run()
            self.timer.stop("ingestion")

            self.hasher.check_ingestion(documents)
            lc.save_cache("ingestion", documents, ingestion_cache)
            self.hasher.stamp("ingestion", ingestion_cache)
            lc.stop("ingestion")

        # ── Stage 2: Chunking: Pure python — no container
        chunking_cache = cfg.chunking.cache.cache_dir
        if os.path.exists(os.path.join(chunking_cache, "output.json")):
            self.hasher.verify("chunking", chunking_cache)
            print("⚡ Chunking cache found — skipping")
            chunks = lc.load_cache("chunking", chunking_cache)
        else:
            print("\n── Stage 2: Chunking ──")
            lc.check_ram("chunking", cfg.runtime.ram_budget_gb)

            self.timer.start("chunking")
            documents = lc.load_cache("ingestion",ingestion_cache)
            chunks = ChunkingAdapter(cfg.chunking).run(documents)
            self.timer.stop("chunking")

            self.hasher.check_chunking(documents, chunks)
            lc.save_cache("chunking", chunks,chunking_cache)
            self.hasher.stamp("chunking", chunking_cache)

        # ── Stage 3: Embeddings
        embeddings_cache = cfg.embeddings.cache.cache_dir
        if os.path.exists(os.path.join(embeddings_cache, "output.json")):
            self.hasher.verify("embeddings", embeddings_cache)
            print("⚡ Embeddings cache found — skipping")
            embedded = lc.load_cache("embeddings", embeddings_cache)

        else:
            print("\n── Stage 3: Embeddings ──")
            lc.check_ram("embeddings", cfg.runtime.ram_budget_gb)
            lc.start("embeddings")
            lc.health_check("embeddings")

            self.timer.start("embeddings")
            # chunks = lc.load_cache("chunking",chunking_cache) doubt??
            embedded = EmbeddingsAdapter(cfg.embeddings).run(chunks)
            self.timer.stop("embeddings")

            self.hasher.check_embeddings(chunks, embedded)
            lc.save_cache("embeddings", embedded,embeddings_cache)
            self.hasher.stamp("embeddings", embeddings_cache)
            lc.stop("embeddings")

        # ── Stage 4: Vector DB: Pure python (chroma)
        print("\n── Stage 4: Vector DB ──")
        lc.check_ram("vector_db", cfg.runtime.ram_budget_gb)
        # embedded = lc.load_cache("embeddings", embeddings_cache) doubt??

        self.timer.start("vector_db")
        vdb = VectorDBAdapter(cfg.vector_db)
        collection = vdb.run(embedded)
        self.timer.stop("vector_db")

        # Verify vectors were stored correctly
        self.hasher.check_vectordb_storage(collection, len(embedded))

        # ── Stage 5: Retrieval: Embeddings container still needed for query embedding
        print("\n── Stage 5: Retrieval ──")
        lc.check_ram("embeddings", cfg.runtime.ram_budget_gb)
        lc.start("embeddings")
        lc.health_check("embeddings")

        self.timer.start("retrieval")
        retriever = RetrievalAdapter(cfg.retrieval, cfg.embeddings)
        chunks    = retriever.run((collection, query))
        self.timer.stop("retrieval")

        self.hasher.check_retrieval(chunks)
         # Verify retrieved chunks actually exist in the embedded pool
        self.hasher.check_retrieval_membership(chunks, embedded)
        lc.stop("embeddings")

        # ── Stage 6: RAG ───────────────────
        print("\n── Stage 6: RAG ──")

        self.timer.start("rag")
        prompt = RAGAdapter(cfg.llm).run((chunks, query))
        self.timer.stop("rag")

        # Verify context assembly is complete with no data loss
        self.hasher.check_rag_assembly(chunks, prompt)

        # ── Stage 7: LLM ───────────────────
        print("\n── Stage 7: LLM ──")
        lc.check_ram("llm", cfg.runtime.ram_budget_gb)
        lc.start("llm")
        lc.health_check("llm")

        self.timer.start("llm")
        answer = LLMAdapter(cfg.llm).run(prompt)
        self.timer.stop("llm")

        print("\n" + "="*50)
        print(" RICE Pipeline Complete")
        print("="*50)
        self.timer.summary()
        return answer, chunks