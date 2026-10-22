import json
import base64
from typing import List, Dict, Any
import httpx
from app.providers.base import VLMProvider, LLMProvider
from app.schemas.analysis import VisualFindings


class GeminiProvider(VLMProvider, LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def describe_ui_issue(
        self, images: List[bytes], description: str, ocr_text: str
    ) -> VisualFindings:
        parts: List[Dict[str, Any]] = [
            {
                "text": (
                    f"User bug description:\n{description}\n\n"
                    f"OCR Extracted text:\n{ocr_text}\n\n"
                    "Analyze this screenshot and return a pure JSON object with: summary, visible_error_text (array), "
                    "ui_elements (array of {type, label, state, bbox}), anomalies (array of {kind, description, confidence}), "
                    "likely_component_keywords (array), and image_quality (good|low|irrelevant)."
                )
            }
        ]
        for img in images[:4]:
            b64 = base64.b64encode(img).decode("utf-8")
            parts.append({
                "inline_data": {
                    "mime_type": "image/png",
                    "data": b64,
                }
            })

        url = f"{self.base_url}/gemini-1.5-pro:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {"response_mime_type": "application/json"},
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return VisualFindings(**json.loads(raw_text))

    async def complete_json(self, system: str, user: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"System: {system}\n\nUser: {user}\n\nOutput pure JSON matching schema: {json.dumps(schema)}"
        url = f"{self.base_url}/gemini-1.5-pro:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"},
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)

    async def complete_text(self, system: str, user: str) -> str:
        prompt = f"System: {system}\n\nUser: {user}"
        url = f"{self.base_url}/gemini-1.5-flash:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
