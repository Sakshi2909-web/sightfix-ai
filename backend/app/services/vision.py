from typing import List, Tuple
from app.providers.factory import get_vlm_provider, get_embedding_provider
from app.schemas.analysis import VisualFindings
from app.services.ocr import ocr_service


class VisionService:
    async def analyze_visual_evidence(
        self, image_bytes_list: List[bytes], description: str
    ) -> Tuple[VisualFindings, List[List[float]]]:
        vlm = get_vlm_provider()
        embedder = get_embedding_provider()

        # Aggregate OCR across all images
        ocr_texts = []
        for img in image_bytes_list:
            res = ocr_service.extract_text(img)
            if res.text:
                ocr_texts.append(res.text)
        combined_ocr = "\n---\n".join(ocr_texts)

        # Call VLM provider
        findings = await vlm.describe_ui_issue(
            images=image_bytes_list,
            description=description,
            ocr_text=combined_ocr,
        )

        # Compute image embeddings for history / visual similarity
        image_embeddings = await embedder.embed_images(image_bytes_list)

        return findings, image_embeddings


vision_service = VisionService()
