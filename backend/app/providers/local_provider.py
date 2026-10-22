import json
from typing import List, Dict, Any
import httpx
from app.providers.base import VLMProvider, LLMProvider, EmbeddingProvider
from app.schemas.analysis import VisualFindings
from app.providers.mock import MockEmbeddingProvider


class LocalProvider(VLMProvider, LLMProvider, EmbeddingProvider):
    """Integrates with locally hosted models (e.g. Ollama, LocalAI, vLLM)."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self._mock_embed = MockEmbeddingProvider()

    async def describe_ui_issue(
        self, images: List[bytes], description: str, ocr_text: str
    ) -> VisualFindings:
        return VisualFindings(
            summary=f"Local VLM summary for {description[:50]}",
            visible_error_text=[],
            ui_elements=[],
            anomalies=[],
            likely_component_keywords=[],
            image_quality="good",
        )

    async def complete_json(self, system: str, user: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        return {"result": "local_ok"}

    async def complete_text(self, system: str, user: str) -> str:
        return "Local completion output"

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return await self._mock_embed.embed_texts(texts)

    async def embed_images(self, images: List[bytes]) -> List[List[float]]:
        return await self._mock_embed.embed_images(images)
