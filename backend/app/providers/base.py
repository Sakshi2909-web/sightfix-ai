from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.schemas.analysis import VisualFindings


class VLMProvider(ABC):
    @abstractmethod
    async def describe_ui_issue(
        self, images: List[bytes], description: str, ocr_text: str
    ) -> VisualFindings:
        pass


class LLMProvider(ABC):
    @abstractmethod
    async def complete_json(self, system: str, user: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def complete_text(self, system: str, user: str) -> str:
        pass


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    async def embed_images(self, images: List[bytes]) -> List[List[float]]:
        pass
