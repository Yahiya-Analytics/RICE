# containers/ingestion/dispatcher.py
import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

class IngestRequest(BaseModel):
    tool: str
    source: str
    formats: List[str]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/process")
def process(request: IngestRequest):
    if request.tool == "docling":
        return run_docling(request.source, request.formats)
    else:
        return {"error": f"Unknown tool: {request.tool}"}

def run_docling(source: str, formats: List[str]):
    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    documents = []

    # source is a directory — walk all files
    for root, dirs, files in os.walk(source):
        for filename in files:
            ext = filename.split(".")[-1].lower()
            if ext not in formats:
                continue

            filepath = os.path.join(root, filename)
            print(f"   converting {filepath}...")

            try:
                result = converter.convert(filepath)
                text   = result.document.export_to_markdown()
                documents.append({
                    "text":   text,
                    "source": filename,
                    "page":   0,
                    "format": ext,
                })
            except Exception as e:
                print(f"   ❌ failed {filepath}: {e}")

    return {"documents": documents}