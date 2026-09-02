# adapters/vectordb_adapter.py
from adapters.base import BaseAdapter

class VectorDBAdapter(BaseAdapter):
    def __init__(self, config):
        super().__init__(config)
        self.collection = None

    def run(self, data=None):
        embedded_chunks = data
        backend = self.config.backend
        print(f"  Storing {len(embedded_chunks)} vectors → {backend}")

        if backend == "chroma":
            self.collection = self._run_chroma(embedded_chunks)
        elif backend == "qdrant":
            self.collection = self._run_qdrant(embedded_chunks)
        else:
            raise ValueError(f"Unknown backend: {backend}")

        print(f" Vectors stored in {backend}")
        return self.collection

    def _run_chroma(self, embedded_chunks):
        import chromadb
        client = chromadb.PersistentClient(
            path=self.config.local.path
        )
        collection = client.get_or_create_collection(
            name="rice-poc",
            metadata={"hnsw:space": self.config.index.metric}
        )

        # insert in batches
        ids       = [str(i) for i in range(len(embedded_chunks))]
        documents = [c["text"]   for c in embedded_chunks]
        vectors   = [c["vector"] for c in embedded_chunks]
        metadatas = [{
            "source":      c.get("source", ""),
            "page":        str(c.get("page", 0)),
            "chunk_index": str(c.get("chunk_index", 0)),
        } for c in embedded_chunks]

        collection.add(
            ids        = ids,
            documents  = documents,
            embeddings = vectors,
            metadatas  = metadatas,
        )
        return collection

    def _run_qdrant(self, embedded_chunks):
        from qdrant_client import QdrantClient
        from qdrant_client.models import (
            Distance, VectorParams, PointStruct
        )

        client = QdrantClient(
            host = "localhost",
            port = 6333
        )
        client.recreate_collection(
            collection_name = "rice-poc",
            vectors_config  = VectorParams(
                size     = self.config.index.dimensions,
                distance = Distance.COSINE,
            )
        )
        points = [
            PointStruct(
                id      = i,
                vector  = c["vector"],
                payload = {
                    "text":        c["text"],
                    "source":      c.get("source", ""),
                    "page":        c.get("page", 0),
                    "chunk_index": c.get("chunk_index", 0),
                }
            )
            for i, c in enumerate(embedded_chunks)
        ]
        client.upsert(
            collection_name = "rice-poc",
            points          = points
        )
        return client