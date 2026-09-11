import hashlib
import json
import os
from typing import Any


MANIFEST_PATH = ".rice_cache/manifest.json"


class CacheHasher:
    """
    SHA-256 hashing and integrity checks for pipeline cache.

    Responsibilities:
      - Hash stage output and store in manifest after saving
      - Verify hash before loading cached data
      - Cross-stage count and coverage checks
    """

    #manifest read / write 
    def _load_manifest(self) -> dict:
        if os.path.exists(MANIFEST_PATH):
            with open(MANIFEST_PATH, "r") as f:
                return json.load(f)
        return {}

    def _save_manifest(self, manifest: dict) -> None:
        os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
        with open(MANIFEST_PATH, "w") as f:
            json.dump(manifest, f, indent=2)

    # hash helpers
    def _hash_file(self, path: str) -> str:
        sha = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)
        return sha.hexdigest()[:8]          # short hash for readability

    # save hash after a stage writes its cache
    def stamp(self, stage: str, cache_path: str) -> str:
        """Hash the output file and store in manifest."""
        output_file = os.path.join(cache_path, "output.json")
        if not os.path.exists(output_file):
            return ""

        h = self._hash_file(output_file)
        manifest = self._load_manifest()
        manifest[stage] = {"hash": h, "path": output_file}
        self._save_manifest(manifest)
        print(f" 🔐 Hash: {h} → manifest updated")
        return h

    # verify hash before a stage loads its cache ─
    def verify(self, stage: str, cache_path: str) -> bool:
        """
        Returns True if cached file matches stored hash.
        Raises RuntimeError if hash mismatch (corruption detected).
        """
        output_file = os.path.join(cache_path, "output.json")
        if not os.path.exists(output_file):
            return False                    # no cache — not an error

        manifest = self._load_manifest()
        if stage not in manifest:
            return True                     # first run, no hash stored yet

        stored_hash = manifest[stage]["hash"]
        current_hash = self._hash_file(output_file)

        if stored_hash != current_hash:
            raise RuntimeError(
                f"❌ Cache integrity failure for '{stage}'\n"
                f"   stored hash:  {stored_hash}\n"
                f"   current hash: {current_hash}\n"
                f"   Cache may be corrupted. Delete .rice_cache/{stage}/ and re-run."
            )

        print(f" 🔐 Hash verified: {current_hash}")
        return True

    #cross-stage integrity checks
    def check_ingestion(self, documents: list[dict]) -> None:
        """Basic checks after ingestion."""
        count = len(documents)
        if count == 0:
            raise RuntimeError("❌ Integrity: ingestion returned 0 documents.")

        total_chars = sum(len(d.get("text", "")) for d in documents)
        print(f"   🔍 Integrity: {count} doc(s) | {total_chars:,} chars ingested")

    def check_chunking(self, documents: list[dict], chunks: list[dict]) -> None:
        """Coverage check: what % of source text survived chunking."""
        source_chars = sum(len(d.get("text", "")) for d in documents)
        chunk_chars  = sum(len(c.get("text", "")) for c in chunks)

        if len(chunks) == 0:
            raise RuntimeError("❌ Integrity: chunking returned 0 chunks.")

        coverage = (chunk_chars / source_chars * 100) if source_chars > 0 else 0
        avg_len  = chunk_chars // len(chunks)

        status = "✅" if coverage >= 60 else "⚠️ "
        print(
            f"   🔍 Integrity: {len(chunks)} chunks | "
            f"coverage {coverage:.1f}% {status} | "
            f"avg {avg_len} chars/chunk"
        )
        if coverage < 60:
            print(
                f"   ⚠️  Low coverage ({coverage:.1f}%) — "
                f"chunking strategy may be dropping significant content."
            )

    def check_embeddings(self, chunks: list[dict], embedded: list[dict]) -> None:
        """Count match: every chunk must have exactly one embedding."""
        n_chunks = len(chunks)
        n_embeds = len(embedded)

        if n_embeds == 0:
            raise RuntimeError("❌ Integrity: embeddings returned 0 vectors.")

        if n_chunks != n_embeds:
            raise RuntimeError(
                f"❌ Integrity: chunk count ({n_chunks}) ≠ "
                f"embedding count ({n_embeds}). Data loss between stages."
            )

        # check all embeddings have the same dimension
        dims = {len(e["embedding"]) for e in embedded if "embedding" in e}
        if len(dims) > 1:
            raise RuntimeError(
                f"❌ Integrity: inconsistent embedding dimensions found: {dims}"
            )

        dim = dims.pop() if dims else "?"
        print(
            f"   🔍 Integrity: {n_chunks} chunks → "
            f"{n_embeds} embeddings | dim={dim} ✅"
        )

    def check_retrieval(self, chunks: list[dict]) -> None:
        """Score range and non-empty check after retrieval."""
        if len(chunks) == 0:
            print("   ⚠️  Retrieval returned 0 chunks — query may not match corpus.")
            return

        scores = [c.get("score", 0) for c in chunks]
        avg    = sum(scores) / len(scores)
        lo     = min(scores)
        hi     = max(scores)

        out_of_range = [s for s in scores if not (0.0 <= s <= 1.0)]
        score_status = "⚠️  scores out of [0,1]" if out_of_range else "✅"

        print(
            f"   🔍 Integrity: {len(chunks)} chunks retrieved | "
            f"scores [{lo:.3f}, {hi:.3f}] avg={avg:.3f} {score_status}"
        )
    def check_vectordb_storage(self, collection, expected_count: int) -> None:
        """Verify vectors were stored in ChromaDB correctly."""
        try:
            # Get actual count from collection
            count = collection.count()
            
            if count == 0:
                raise RuntimeError(
                    "❌ Integrity: Vector DB storage failed. "
                    f"Expected {expected_count} vectors, got 0."
                )
            
            if count != expected_count:
                raise RuntimeError(
                    "❌ Integrity: Vector count mismatch. "
                    f"Expected {expected_count}, stored {count}. Data loss detected."
                )
            
            print(f"   🔍 Integrity: {count} vectors stored in ChromaDB ✅")
            
        except Exception as e:
            if "count" in str(e).lower():
                # ChromaDB might not have .count(), try alternative
                print(f"   ⚠️  Could not verify vector DB count (method unavailable)")
            else:
                raise RuntimeError(f"❌ Vector DB integrity check failed: {e}")
 
    def check_retrieval_membership(
        self, 
        retrieved_chunks: list[dict], 
        embedded_chunks: list[dict] ) -> None:
        """Verify all retrieved chunks actually exist in the embedded pool."""
        if len(retrieved_chunks) == 0:
            print("   🔍 Integrity: No chunks retrieved (query may not match corpus)")
            return
 
        # Build a set of chunk text hashes from embedded pool for comparison
        embedded_texts = {c.get("text", ""): i for i, c in enumerate(embedded_chunks)}
        missing_chunks = []
        found_chunks = 0
 
        for retrieved in retrieved_chunks:
            chunk_text = retrieved.get("text", "")
            if chunk_text in embedded_texts:
                found_chunks += 1
            else:
                missing_chunks.append(chunk_text[:50])  # first 50 chars for debug
        
        if missing_chunks:
            raise RuntimeError(
                f"❌ Integrity: Retrieved chunks not in embedded pool. "
                f"Found {found_chunks}/{len(retrieved_chunks)} chunks in pool. "
                f"Data corruption or wrong pool queried."
            )
        
        print(
            f"   🔍 Integrity: All {found_chunks} retrieved chunks "
            f"verified in embedded pool ✅"
        )
 
    def check_rag_assembly(
        self, 
        chunks: list[dict], 
        context: str
    ) -> None:
        """Verify RAG context assembly is complete with no data loss."""
        if not context or len(context.strip()) == 0:
            raise RuntimeError(
                "❌ Integrity: RAG context is empty. "
                "Context assembly failed or context truncated."
            )
        
        if len(chunks) == 0:
            print("   🔍 Integrity: RAG context assembled (no chunks to verify)")
            return
 
        # Verify all chunk texts are present in context
        total_chunk_chars = sum(len(c.get("text", "")) for c in chunks)
        context_chars = len(context)
        
        missing_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_text = chunk.get("text", "")
            # Check if chunk content appears in context (may be truncated, so check first 100 chars)
            if chunk_text[:100] not in context:
                missing_chunks.append(i)
        
        if missing_chunks:
            print(
                f"   ⚠️  Integrity: {len(missing_chunks)} chunk(s) not fully in context "
                f"(may be truncated or excluded). Indices: {missing_chunks}"
            )
        else:
            print(
                f"   🔍 Integrity: RAG context complete | "
                f"{len(chunks)} chunks | {context_chars:,} context chars ✅"
            )