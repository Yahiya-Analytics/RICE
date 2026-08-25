## Schema Reference
### Project Block
```
[project]
name = "your-project-name"
version = "0.1.0"
description = "what this pipeline does"
```
### Runtime Block
```
[runtime]
execution = "sequential"        # only option for now
ram_budget_gb = 6               # warn if stage needs more than this
cache_between_stages = true     # always keep true
auto_cleanup = true             # containers removed after stopping
```
### Ingestion Block
```
[ingestion]
source = "./data/"              # folder with your documents
formats = ["pdf", "docx", "csv"]
batch_size = 10                 # files processed at a time
recursive = true                # scan subdirectories
exclude = ["temp/", "*.tmp"]

  [ingestion.parser]
  tool = "docling"              # Options: docling, unstructured, marker
  fallback = "unstructured"     # if primary tool fails
  ocr = true
  extract_tables = true
  extract_images = false

  [ingestion.output]
  format = "markdown"           # Options: markdown, json, plain_text

  [ingestion.metadata]
  extract_filename = true
  extract_page_numbers = true
  extract_section_headers = true

  [ingestion.cache]
  enabled = true
  cache_dir = ".rice_cache/ingestion"

  [ingestion.errors]
  on_failure = "skip"           # Options: skip, halt, log_and_continue
  log_failed_files = true
```
### Chunking Block
```
[chunking]
strategy = "recursive"          # Options: fixed, fixed_overlap,
                                #          sentence, paragraph,
                                #          recursive, semantic,
                                #          structure_aware, token_aware,
                                #          proposition, late_chunking,
                                #          parent_child, contextual_retrieval,
                                #          raptor
fallback_strategy = "fixed"
batch_size = 20
min_chunk_tokens = 50
max_chunk_tokens = 1024

  # ── use only the block matching your strategy ──

  [chunking.fixed]
  target_tokens = 512

  [chunking.fixed_overlap]
  target_tokens = 512
  overlap_tokens = 50

  [chunking.sentence]
  library = "spacy"             # Options: spacy, nltk, regex

  [chunking.paragraph]
  separator = "\n\n"

  [chunking.recursive]
  target_tokens = 512
  overlap_tokens = 50

  [chunking.semantic]
  embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
  similarity_threshold = 0.85
  target_tokens = 512

  [chunking.structure_aware]
  split_on = ["h1", "h2", "h3"]
  fallback = "paragraph"

  [chunking.token_aware]
  tokenizer = "tiktoken"
  model_name = "gpt-4"
  target_tokens = 512

  [chunking.proposition]
  decomposition_model = "llama3.2"
  max_propositions = 5

  [chunking.late_chunking]
  pool_strategy = "mean"

  [chunking.parent_child]
  parent_strategy = "paragraph"
  child_strategy = "sentence"
  return_parent_on_retrieval = true

  [chunking.contextual_retrieval]
  context_model = "llama3.2"
  context_prompt = "Summarize this chunk in context of the full document"

  [chunking.raptor]
  summarization_model = "llama3.2"
  levels = 3
  collapse_tree = true

  [chunking.output]
  format = "documents"
  include_metadata = true
  include_chunk_index = true
  include_parent_id = true

  [chunking.postprocessing]
  dedup = true
  filter_empty = true

  [chunking.cache]
  enabled = true
  cache_dir = ".rice_cache/chunking"
```
### Embeddings Block
```
[embeddings]
provider = "huggingface"        # Options: huggingface, ollama,
                                #          openai, cohere, voyage, google
model = "BAAI/bge-small-en-v1.5"
model_family = "bge"            # Options: bert, bge, e5, qwen2,
                                #          clip, splade
type = "dense"                  # Options: dense, sparse, hybrid,
                                #          multimodal, multilingual,
                                #          matryoshka, cross_encoder,
                                #          ensemble
task = "retrieval"              # Options: retrieval, classification,
                                #          clustering, similarity,
                                #          reranking, pair_classification,
                                #          bitext_mining, summarization
fallback_model = "sentence-transformers/all-MiniLM-L6-v2"

  [embeddings.model_params]
  dimensions = 384              # must match vector_db.index.dimensions
  max_tokens = 512              # must match chunking max_chunk_tokens
  normalize = true
  batch_size = 32

  [embeddings.serving]
  backend = "infinity"          # Options: infinity, tei, ollama
  host = "localhost"
  port = 7997

  [embeddings.quantization]
  enabled = false
  type = "int8"                 # Options: none, int8, binary, fp16

  # ── use only the block matching your type ──

  [embeddings.sparse]
  model = "naver/splade-v3"
  weight = 0.3

  [embeddings.hybrid]
  dense_weight = 0.7
  sparse_weight = 0.3

  [embeddings.matryoshka]
  dimensions = [1536, 768, 256]
  active_dimension = 256

  [embeddings.multimodal]
  model = "openai/clip-vit-base-patch32"
  modalities = ["text", "image"]

  [embeddings.ensemble]
  models = ["BAAI/bge-large-en-v1.5",
            "sentence-transformers/all-MiniLM-L6-v2"]
  weights = [0.7, 0.3]

  [embeddings.custom]
  enabled = false
  path = "./models/finetuned-embeddings"
  base_model = "BAAI/bge-large-en-v1.5"

  [embeddings.output]
  include_metadata = true
  include_sparse_vectors = false

  [embeddings.cache]
  enabled = true
  cache_dir = ".rice_cache/embeddings"
```
### Vector DB Block
```
[vector_db]
backend = "chroma"              # Options: faiss, chroma, qdrant,
                                #          weaviate, milvus, pgvector,
                                #          lancedb, redis
mode = "local"                  # Options: local, container
                                # local     = faiss, chroma, lancedb
                                # container = qdrant, weaviate, milvus
fallback_backend = "chroma"
insert_batch_size = 100

  [vector_db.connection]        # only if mode = container
  host = "localhost"
  port = 6333
  timeout = 30

  [vector_db.local]             # only if mode = local
  path = ".rice_cache/vectordb"

  [vector_db.index]
  type = "hnsw"                 # Options: flat, ivf, hnsw, lsh
  metric = "cosine"             # Options: cosine, dot_product, euclidean
  dimensions = 384              # must match embeddings.model_params.dimensions

  [vector_db.index.hnsw]
  ef_construct = 128
  m = 16

  [vector_db.index.ivf]
  n_lists = 100
  n_probes = 10

  [vector_db.sparse]
  enabled = false               # set true if embeddings.type = hybrid

  [vector_db.metadata]
  store_metadata = true
  indexed_fields = [
    "source_file",
    "page_number",
    "chunk_index",
    "parent_id",
  ]

  [vector_db.quantization]
  enabled = false
  type = "scalar"               # Options: scalar, product, binary

  [vector_db.output]
  return_vectors = false
  return_metadata = true
  return_score = true

  [vector_db.cache]
  enabled = true
  cache_dir = ".rice_cache/vectordb"
```
### Retrieval Block
```
[retrieval]
top_k = 5
score_threshold = 0.5
fallback_strategy = "dense"
batch_size = 5

  [retrieval.pre]               # pre-retrieval techniques
  enabled = true
  techniques = [
    "query_rewriting",          # Options: query_rewriting, hyde,
    "hyde",                     #          query_expansion, step_back,
  ]                             #          query_routing, flare

    [retrieval.pre.query_rewriting]
    model = "llama3.2"
    n_rewrites = 3

    [retrieval.pre.hyde]
    model = "llama3.2"
    n_hypothetical = 1

    [retrieval.pre.query_expansion]
    model = "llama3.2"
    n_expansions = 3
    fusion_method = "rrf"       # Options: rrf, linear, reciprocal

    [retrieval.pre.step_back]
    model = "llama3.2"
    abstraction_level = 1

    [retrieval.pre.flare]
    model = "llama3.2"
    confidence_threshold = 0.5
    max_retrievals = 5

  [retrieval.strategy]
  type = "dense"                # Options: dense, sparse, hybrid,
                                #          multi_query, ensemble,
                                #          parent_child, self_query,
                                #          time_weighted, multi_hop

    [retrieval.strategy.hybrid]
    dense_weight = 0.7
    sparse_weight = 0.3
    fusion_method = "rrf"

    [retrieval.strategy.multi_query]
    n_queries = 3
    fusion_method = "rrf"
    deduplicate = true

    [retrieval.strategy.ensemble]
    retrievers = ["dense", "sparse", "bm25"]
    weights = [0.5, 0.3, 0.2]

    [retrieval.strategy.parent_child]
    retrieve = "child"
    return = "parent"

    [retrieval.strategy.self_query]
    model = "llama3.2"
    metadata_fields = ["source_file", "page_number"]

    [retrieval.strategy.time_weighted]
    decay_rate = 0.01
    time_field = "created_at"

    [retrieval.strategy.multi_hop]
    max_hops = 3
    model = "llama3.2"

  [retrieval.post]              # post-retrieval techniques
  enabled = true
  techniques = [
    "reranking",                # Options: reranking, compression,
    "deduplication",            #          deduplication, diversity,
  ]                             #          lost_in_middle_fix

    [retrieval.post.reranking]
    model = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    top_n = 3
    provider = "local"          # Options: local, cohere, voyage, jina

    [retrieval.post.compression]
    model = "llama3.2"
    target_tokens = 256
    method = "extractive"       # Options: extractive, abstractive

    [retrieval.post.diversity]
    method = "mmr"
    lambda_param = 0.5
    top_n = 3

    [retrieval.post.deduplication]
    method = "minhash"          # Options: exact, minhash, semantic
    threshold = 0.9

  [retrieval.output]
  return_chunks = true
  return_scores = true
  return_metadata = true
  max_context_tokens = 4096

  [retrieval.cache]
  enabled = true
  cache_dir = ".rice_cache/retrieval"
  ttl_seconds = 3600
```
### RAG Block
```
[rag]
type = "advanced"               # Options: naive, advanced, modular,
                                #          graph_rag, hippo_rag,
                                #          self_rag, corrective_rag,
                                #          adaptive_rag, agentic_rag,
                                #          multimodal_rag
fallback_type = "naive"
batch_size = 5

  # ── use only the block matching your type ──

  [rag.graph_rag]
  graph_backend = "neo4j"       # Options: neo4j, memgraph, kuzu
  entity_extraction_model = "llama3.2"
  community_detection = true
  community_model = "leiden"

  [rag.hippo_rag]
  memory_backend = "redis"
  episodic_memory = true
  semantic_memory = true

  [rag.self_rag]
  reflection_model = "llama3.2"
  max_iterations = 3

  [rag.corrective_rag]
  evaluator_model = "llama3.2"
  relevance_threshold = 0.5
  web_search_fallback = true
  web_search_provider = "tavily"

  [rag.adaptive_rag]
  classifier_model = "llama3.2"
  simple_strategy = "naive"
  moderate_strategy = "advanced"
  complex_strategy = "self_rag"

  [rag.agentic_rag]
  agent_model = "llama3.2"
  max_iterations = 5
  tools = ["retriever", "web_search", "calculator"]
  planning_strategy = "react"

  [rag.multimodal_rag]
  modalities = ["text", "image", "table"]
  image_model = "llava"

  [rag.context]
  max_tokens = 4096
  assembly_method = "sorted"    # Options: sorted, interleaved, weighted
  include_source_labels = true
  separator = "\n\n---\n\n"

  [rag.prompt]
  system = """
  You are a helpful assistant.
  Answer only from the provided context.
  If the answer is not in context say I don't know.
  Cite your sources.
  """

  [rag.response]
  format = "text"               # Options: text, json, markdown
  max_tokens = 1024
  streaming = true
  include_sources = true
  citation_format = "inline"    # Options: inline, footnote, endnote

  [rag.memory]
  enabled = false               # multi-turn conversations
  backend = "in_memory"         # Options: in_memory, redis, sqlite
  max_turns = 10

  [rag.evaluation]
  enabled = false
  framework = "ragas"           # Options: ragas, trulens, deepeval
  sample_rate = 0.1

  [rag.cache]
  enabled = true
  cache_dir = ".rice_cache/rag"
  ttl_seconds = 3600
```
### LLM Block
```
[llm]
provider = "local"              # Options: local, openrouter, groq,
                                #          together, fireworks, mistral
model = "llama3.2:3b"
fallback_model = "tinyllama"

  [llm.local]
  backend = "ollama"
  host = "localhost"
  port = 11434
  gpu_layers = -1               # -1 = all on GPU, 0 = CPU only
  context_length = 4096
  keep_alive = "10m"

  [llm.api]                     # only if provider != local
  api_key = "env:LLM_API_KEY"  # never hardcode keys

    [llm.api.openrouter]
    base_url = "https://openrouter.ai/api/v1"

    [llm.api.groq]
    base_url = "https://api.groq.com/openai/v1"

    [llm.api.together]
    base_url = "https://api.together.xyz/v1"

    [llm.api.fireworks]
    base_url = "https://api.fireworks.ai/inference/v1"

  [llm.sampling]
  temperature = 0.3
  top_p = 0.9
  top_k = 40
  repeat_penalty = 1.1
  max_tokens = 512
  stop_sequences = []

  [llm.prompt]
  format = "chatml"             # Options: chatml, llama2, llama3,
                                #          mistral, alpaca, raw
  system = """
  You are a helpful assistant.
  Answer only from the provided context.
  If the answer is not in context say I don't know.
  """

  [llm.response]
  streaming = true
  format = "text"               # Options: text, json, markdown

  [llm.cache]
  enabled = true
  cache_dir = ".rice_cache/llm"
  ttl_seconds = 3600
```

