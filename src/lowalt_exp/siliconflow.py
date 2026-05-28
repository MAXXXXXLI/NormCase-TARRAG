import json
import os
import time
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:  # pragma: no cover - only needed for offline/no-LLM runs.
    requests = None


class SiliconFlowClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, timeout: Optional[int] = None):
        self.api_key = api_key or os.environ.get("SILICONFLOW_API_KEY", "")
        self.base_url = (base_url or os.environ.get("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")).rstrip("/")
        self.timeout = int(os.environ.get("SILICONFLOW_TIMEOUT", str(timeout or 180)))
        self.max_retries = int(os.environ.get("SILICONFLOW_MAX_RETRIES", "2"))
        if not self.api_key:
            raise RuntimeError("SILICONFLOW_API_KEY is not set")

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if requests is None:
            raise RuntimeError("requests is required for SiliconFlow API calls; install requirements.txt or run with --no-llm.")
        url = f"{self.base_url}/{path.lstrip('/')}"
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                r = requests.post(url, headers=self._headers(), json=payload, timeout=self.timeout)
                if r.status_code in {429, 500, 502, 503, 504} and attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                    continue
                r.raise_for_status()
                return r.json()
            except requests.exceptions.RequestException as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(2 ** attempt)
        raise last_error

    def chat(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.1, max_tokens: int = 2048) -> str:
        payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        data = self._post("chat/completions", payload)
        return data["choices"][0]["message"].get("content", "")

    def embeddings(self, model: str, inputs: List[str]) -> List[List[float]]:
        payload = {"model": model, "input": inputs}
        data = self._post("embeddings", payload)
        return [item["embedding"] for item in data["data"]]

    def rerank(self, model: str, query: str, documents: List[str], top_n: int) -> List[Dict[str, Any]]:
        payload = {"model": model, "query": query, "documents": documents, "top_n": top_n, "return_documents": False}
        data = self._post("rerank", payload)
        return data.get("results", [])
