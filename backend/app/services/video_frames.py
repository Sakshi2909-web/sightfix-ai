import os
import shutil
import subprocess
from pathlib import Path
from typing import List
from app.services.ocr import ocr_service

KEYWORD_ERROR_TRIGGERS = ["error", "fail", "failed", "exception", "undefined", "cannot read", "crash"]


class VideoFrameExtractor:
    def extract_keyframes(self, video_path: str | Path, max_frames: int = 8) -> List[bytes]:
        """Extracts keyframes based on scene changes and error indicators."""
        v_path = Path(video_path)
        if not v_path.exists():
            return []

        extracted_frames: List[bytes] = []
        out_dir = v_path.parent / f"frames_{v_path.stem}"
        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Check if ffmpeg is available
            ffmpeg_cmd = shutil.which("ffmpeg")
            if ffmpeg_cmd:
                # Extract 1 frame per second
                pattern = str(out_dir / "frame_%03d.png")
                cmd = [
                    ffmpeg_cmd,
                    "-y",
                    "-i", str(v_path),
                    "-vf", "fps=1",
                    "-vframes", str(max_frames * 2),
                    pattern,
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

                all_pngs = sorted(list(out_dir.glob("*.png")))
                # Score frames: look for error text moments
                scored: List[tuple[int, Path]] = []
                for p in all_pngs:
                    score = 0
                    ocr_res = ocr_service.extract_text(p)
                    text_lower = ocr_res.text.lower()
                    for kw in KEYWORD_ERROR_TRIGGERS:
                        if kw in text_lower:
                            score += 5
                    scored.append((score, p))

                # Pick top scored frames or evenly sampled
                scored.sort(key=lambda x: x[0], reverse=True)
                selected_paths = [p for _, p in scored[:max_frames]]
                for p in selected_paths:
                    extracted_frames.append(p.read_bytes())
        except Exception:
            pass
        finally:
            shutil.rmtree(out_dir, ignore_errors=True)

        return extracted_frames


video_frame_extractor = VideoFrameExtractor()
