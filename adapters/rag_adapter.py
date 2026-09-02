# adapters/rag_adapter.py
from adapters.base import BaseAdapter

class RAGAdapter(BaseAdapter):
    def run(self, data=None):
        # data = (retrieved_chunks, query)
        chunks, query = data

        print(f" Assembling context from {len(chunks)} chunks")

        # build context string with source labels
        context_parts = []
        for i, chunk in enumerate(chunks):
            source = chunk["metadata"].get("source", "unknown")
            page = chunk["metadata"].get("page", "?")
            score = chunk.get("score", 0)
            text = chunk["text"]
            words = text.split()
            if len(words) > 200:
                text = " ".join(words[:200]) + "..."
            context_parts.append(
                f"[Source {i+1}: {source} p.{page}]\n{chunk['text']}")
        context = "\n\n---\n\n".join(context_parts)

        # build final prompt
        prompt = f"""
{self.config.prompt.system}

Context:
{context}

Question: {query}

Answer:
"""
        print(" Context assembled")
        return prompt