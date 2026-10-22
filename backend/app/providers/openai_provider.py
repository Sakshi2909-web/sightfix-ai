import json
import base64
from typing import List, Dict, Any
import httpx
from app.providers.base import VLMProvider, LLMProvider, EmbeddingProvider
from app.schemas.analysis import VisualFindings


class OpenAIProvider(VLMProvider, LLMProvider, EmbeddingProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.chat_url = "https://api.openai.com/v1/chat/completions"
        self.embed_url = "https://api.openai.com/v1/embeddings"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def describe_ui_issue(
        self, images: List[bytes], description: str, ocr_text: str
    ) -> VisualFindings:
        messages_content: List[Dict[str, Any]] = [
            {
                "type": "text",
                "text": (
                    f"User bug description:\n{description}\n\n"
                    f"OCR Extracted text:\n{ocr_text}\n\n"
                    "Analyze the UI and return a JSON object with: summary, visible_error_text (list), "
                    "ui_elements (list of {type, label, state, bbox}), anomalies (list of {kind, description, confidence}), "
                    "likely_component_keywords (list), and image_quality (good|low|irrelevant)."
                ),
            }
        ]
        for img in images[:4]:
            b64 = base64.b64encode(img).decode("utf-8")
            messages_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"},
            })

        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": messages_content}],
            "response_format": {"type": "json_object"},
            "max_tokens": 1500,
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(self.chat_url, headers=self.headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw_json = json.loads(data["choices"][0]["message"]["content"])
            return VisualFindings(**raw_json)

    async def complete_json(self, system: str, user: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": f"{system}\nReturn JSON matching schema: {json.dumps(schema)}"},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 2048,
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(self.chat_url, headers=self.headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return json.loads(data["choices"][0]["message"]["content"])

    async def complete_text(self, system: str, user: str) -> str:
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": 2048,
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(self.chat_url, headers=self.headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        payload = {
            "model": "text-embedding-3-large",
            "input": texts,
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(self.embed_url, headers=self.headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]

    async def embed_images(self, images: List[bytes]) -> List[List[float]]:
        # Fallback pseudo-embedding when native image embedding not directly exposed
        import hashlib
        return [[0.0] * 128 for _ in images]
