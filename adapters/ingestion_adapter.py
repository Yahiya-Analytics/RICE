# adapters/ingestion_adapter.py
import requests
from adapters.base import BaseAdapter

class IngestionAdapter(BaseAdapter):
    def run(self, data=None):
        print(f" Ingesting from {self.config.source}")

        response = requests.post(
            "http://localhost:5001/process",
            json={
                "tool":   self.config.parser.tool,   # "docling"
                "source": "/data/",
                "formats": self.config.formats,
            },
            timeout=700
        )
        response.raise_for_status()
        documents = response.json()["documents"]
        print(f" Ingested {len(documents)} documents")
        return documents