# adapters/chunking_adapter.py
# pure python — no container, no HTTP
from adapters.base import BaseAdapter

class ChunkingAdapter(BaseAdapter):
    def run(self, data=None):
        documents = data
        print(f" Chunking {len(documents)} documents "
              f"strategy={self.config.strategy}")

        chunks = []
        for doc in documents:
            text = doc.get("text", "")
            doc_chunks = self._recursive_chunk(
                text,
                target_tokens = self.config.recursive.target_tokens,
                overlap_tokens = self.config.recursive.overlap_tokens,
                metadata = {
                    "source":     doc.get("source", ""),
                    "page":       doc.get("page", 0),
                }
            )
            chunks.extend(doc_chunks)

        print(f" Produced {len(chunks)} chunks")
        return chunks

    def _recursive_chunk(self, text: str,
                          target_tokens: int,
                          overlap_tokens: int,
                          metadata: dict) -> list:
        # approximate tokens as words for POC
        # real tokenizer comes in full build
        words = text.split()
        chunks = []
        start  = 0

        while start < len(words):
            end   = start + target_tokens
            chunk = " ".join(words[start:end])

            chunks.append({
                "text":         chunk,
                "chunk_index":  len(chunks),
                "source":       metadata.get("source"),
                "page":         metadata.get("page"),
                "word_count":   len(chunk.split()),
            })

            # overlap: step back by overlap_tokens
            start = end - overlap_tokens

        return chunks