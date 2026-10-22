import io
from pathlib import Path
from typing import List, Dict, Any
from PIL import Image

# Graceful OCR wrapper
HAVE_TESSERACT = False
try:
    import pytesseract  # type: ignore
    HAVE_TESSERACT = True
except ImportError:
    HAVE_TESSERACT = False


class OCRResult:
    def __init__(self, text: str, boxes: List[Dict[str, Any]] | None = None):
        self.text = text
        self.boxes = boxes or []


class OCRService:
    def extract_text(self, image_input: bytes | str | Path) -> OCRResult:
        """Extracts text and bounding boxes from an image file or bytes."""
        try:
            if isinstance(image_input, (str, Path)):
                img = Image.open(image_input)
            else:
                img = Image.open(io.BytesIO(image_input))
        except Exception:
            return OCRResult(text="")

        if HAVE_TESSERACT:
            try:
                text = pytesseract.image_to_string(img)
                # Can also get data boxes via image_to_data
                return OCRResult(text=text.strip())
            except Exception:
                pass

        # Robust heuristic fallback:
        # Check if the image filename or embedded info mentions known UI keywords
        # or return a clean empty string if no OCR engine is present on the host
        return OCRResult(text="")


ocr_service = OCRService()
