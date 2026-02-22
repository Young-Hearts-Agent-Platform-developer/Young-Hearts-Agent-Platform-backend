from langchain.embeddings.base import Embeddings
from typing import List
import requests
from app.core.config import settings

class DoubaoEmbeddings(Embeddings):
    def __init__(self, api_key: str = "", base_url: str = "", model: str = ""):
        self.api_key = api_key if api_key != "" else settings.DOUBAO_EMBEDDING_API_KEY
        self.base_url = base_url if base_url != "" else settings.DOUBAO_EMBEDDING_BASE_URL
        self.model = model if model != "" else settings.DOUBAO_EMBEDDING_MODEL

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._embed([text])[0]

    def _embed(self, texts: List[str]) -> List[List[float]]:
        url = self.base_url
        if not url.endswith("/embeddings"):
            url = f"{url}/embeddings"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "input": texts
        }
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]
