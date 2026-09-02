# containers/embeddings/dispatcher.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

# model loaded once when container starts
# stays in RAM until container stops
model_cache = {}

class EmbedRequest(BaseModel):
    model: str
    input: List[str]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/embed")
def embed(request: EmbedRequest):
    model_name = request.model

    # lazy load — only loads when first request arrives
    if model_name not in model_cache:
        print(f"   loading model {model_name}...")
        from sentence_transformers import SentenceTransformer
        model_cache[model_name] = SentenceTransformer(model_name)
        print(f"   model loaded")

    model      = model_cache[model_name]
    embeddings = model.encode(
        request.input,
        normalize_embeddings = True,
    ).tolist()

    return {"embeddings": embeddings}