# adapters/embeddings_adapter.py
import requests
from adapters.base import BaseAdapter

class EmbeddingsAdapter(BaseAdapter):
    def run(self, data=None):
        chunks = data
        print(f" Embedding {len(chunks)} chunks "
              f"model={self.config.model}")

        texts    = [c["text"] for c in chunks]
        batch_sz = self.config.model_params.batch_size
        vectors  = []

        # send in batches
        for i in range(0, len(texts), batch_sz):
            batch = texts[i : i + batch_sz]
            response = requests.post(
                f"http://localhost:{self.config.serving.port}/embed",
                json={
                    "model": self.config.model,
                    "input": batch,
                },
                timeout=60
            )
            response.raise_for_status()
            vectors.extend(response.json()["embeddings"])

        # attach vectors to chunks
        embedded = []
        for chunk, vector in zip(chunks, vectors):
            embedded.append({**chunk, "vector": vector})

        print(f" Generated {len(embedded)} embeddings "
              f"dim={len(vectors[0])}")
        return embedded