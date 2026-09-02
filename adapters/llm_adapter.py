# adapters/llm_adapter.py
import requests
from adapters.base import BaseAdapter

class LLMAdapter(BaseAdapter):
    def run(self, data=None):
        prompt = data
        print(f"Generating answer model={self.config.model}")

        response = requests.post(
            f"http://localhost:{self.config.local.port}/api/generate",
            json={
                "model":  self.config.model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": self.config.sampling.temperature,
                    "num_predict": self.config.sampling.max_tokens,
                }
            },
            stream=True,
            timeout=600 )
        response.raise_for_status()
        full_answer = ""
        for line in response.iter_lines():
            if line:
                import json
                chunk = json.loads(line)
                token = chunk.get("response", "")
                print(token, end="", flush=True)
                full_answer += token
                if chunk.get("done"):
                    break

        print(f" Answer generated")
        return full_answer