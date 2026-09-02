# adapters/retrieval_adapter.py
import requests
from adapters.base import BaseAdapter

class RetrievalAdapter(BaseAdapter):
    def __init__(self, config, embeddings_config):
        super().__init__(config)
        self.embeddings_config = embeddings_config

    def run(self, data=None):
        # data here = (collection, query_text)
        collection, query = data
        print(f" Retrieving top_k={self.config.top_k} for: {query}")

        # embed the query using infinity
        q_response = requests.post(
            f"http://localhost:{self.embeddings_config.serving.port}/embed",
            json={
                "model": self.embeddings_config.model,
                "input": [query],
            },
            timeout=300
        )
        q_response.raise_for_status()
        query_vector = q_response.json()["embeddings"][0]

        # query the vector db
        backend = self.config.strategy   # "dense" for POC
        results = self._query_chroma(collection, query_vector)

        print(f" Retrieved {len(results)} chunks")
        return results

    def _query_chroma(self, collection, query_vector):
        results = collection.query(
            query_embeddings = [query_vector],
            n_results        = self.config.top_k,
            include          = ["documents", "metadatas", "distances"]
        )
        chunks = []
        for i, doc in enumerate(results["documents"][0]):
            chunks.append({
                "text":     doc,
                "score":    1 - results["distances"][0][i],
                "metadata": results["metadatas"][0][i],
            })
        return chunks