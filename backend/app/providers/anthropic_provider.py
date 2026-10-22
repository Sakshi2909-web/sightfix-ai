import json
import base64
from typing import List, Dict, Any
import httpx
from app.providers.base import VLMProvider, LLMProvider
from app.schemas.analysis import VisualFindings


class AnthropicProvider(VLMProvider, LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    async def describe_ui_issue(
        self, images: List[bytes], description: str, ocr_text: str
    ) -> VisualFindings:
        content: List[Dict[str, Any]] = []
        for img in images[:4]:
            b64 = base64.b64encode(img).decode("utf-8")
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": b64,
                },
            })

        prompt = (
            f"User bug description:\n{description}\n\n"
            f"OCR Extracted text from screenshot:\n{ocr_text}\n\n"
            "Analyze the screenshot and return a JSON object with this exact schema:\n"
            "{\n"
            '  "summary": "string describing visual UI bug",\n'
            '  "visible_error_text": ["array of exact error strings"],\n'
            '  "ui_elements": [{"type":"button|input|modal|list|nav|other", "label":"...", "state":"normal|disabled|hidden|overlapped|misaligned|loading|error", "bbox":[x,y,w,h]}],\n'
            '  "anomalies": [{"kind":"layout_break|overlap|clipped|missing_element|wrong_state|empty_state|error_banner|other", "description":"...", "confidence":0.9}],\n'
            '  "likely_component_keywords": ["ComponentName", "methodName"],\n'
            '  "image_quality": "good|low|irrelevant"\n'
            "}\nReturn ONLY the JSON object."
        )
        content.append({"type": "text", "text": prompt})

        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": content}],
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(self.api_url, headers=self.headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["content"][0]["text"]
            # Clean JSON formatting if wrapped in code blocks
            clean_text = raw_text.strip()
            if clean_text.startswith("```"):
                clean_text = clean_text.split("```")[1]
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:]
            parsed = json.loads(clean_text)
            return VisualFindings(**parsed)

    async def complete_json(self, system: str, user: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"{user}\n\nReturn ONLY a valid JSON object matching schema: {json.dumps(schema)}"
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 2048,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(self.api_url, headers=self.headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["content"][0]["text"].strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
            return json.loads(raw_text)

    async def complete_text(self, system: str, user: str) -> str:
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 2048,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(self.api_url, headers=self.headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]
