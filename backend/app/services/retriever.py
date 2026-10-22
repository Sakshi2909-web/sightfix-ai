import re
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple
from app.services.code_indexer import ChunkMetadata
from app.schemas.analysis import VisualFindings, LogFindings
from app.providers.factory import get_embedding_provider


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm1 * norm2)))


class Retriever:
    async def retrieve_candidates(
        self,
        chunks: List[ChunkMetadata],
        bm25_index: Any,
        description: str,
        visual_findings: VisualFindings,
        log_findings: LogFindings,
        churn_scores: Dict[str, float],
        import_graph: Dict[str, List[str]],
    ) -> Dict[str, Any]:
        embedder = get_embedding_provider()

        # Build query signals
        vlm_text = f"{visual_findings.summary} {' '.join(visual_findings.visible_error_text)} {' '.join(a.description for a in visual_findings.anomalies)}"
        q_text = f"{description} {vlm_text}"
        q_keywords = list(visual_findings.likely_component_keywords)
        for el in visual_findings.ui_elements:
            q_keywords.append(el.label)
        for sig in log_findings.error_signatures:
            q_keywords.append(sig.error_type)
            q_keywords.append(sig.message)

        # 1. Dense retrieval
        q_embedding = (await embedder.embed_texts([q_text]))[0]
        chunk_texts = [f"{c.file_path} {c.symbol_name} {c.content}" for c in chunks]
        chunk_embeddings = await embedder.embed_texts(chunk_texts)

        dense_scores: List[Tuple[int, float]] = []
        for idx, c_emb in enumerate(chunk_embeddings):
            sim = cosine_similarity(q_embedding, c_emb)
            dense_scores.append((idx, sim))
        dense_scores.sort(key=lambda x: x[1], reverse=True)

        # 2. BM25 Lexical retrieval
        tokens = [t.lower() for t in re.findall(r'[a-zA-Z0-9_$]+', f"{q_text} {' '.join(q_keywords)}")]
        if not tokens:
            tokens = ["code"]
        bm25_raw = bm25_index.get_scores(tokens)
        bm25_scores = sorted(list(enumerate(bm25_raw)), key=lambda x: x[1], reverse=True)

        # 3. Stack frame hits
        stack_hits: Dict[int, str] = {}
        for idx, chunk in enumerate(chunks):
            for frame in log_findings.stack_frames:
                frame_file = frame.file.replace("\\", "/")
                # Check suffix match (e.g. src/auth/LoginForm.jsx matches repo path)
                if chunk.file_path.endswith(frame_file) or frame_file.endswith(chunk.file_path):
                    if frame.line and chunk.start_line <= frame.line <= chunk.end_line:
                        stack_hits[idx] = f"Appears directly in stack trace at line {frame.line} in {frame.function or 'function'}"
                    elif not stack_hits.get(idx):
                        stack_hits[idx] = f"File referenced in stack trace ({frame_file})"

        # 4. UI Label match
        ui_label_hits: Dict[int, str] = {}
        ui_terms = [el.label.lower() for el in visual_findings.ui_elements if el.label]
        for idx, chunk in enumerate(chunks):
            content_lower = chunk.content.lower()
            for term in ui_terms:
                if term in content_lower:
                    ui_label_hits[idx] = f"Contains UI label '{term}' detected in screenshot"
                    break

        # 5. Git signals
        git_hits: Dict[int, float] = {}
        for idx, chunk in enumerate(chunks):
            if chunk.file_path in churn_scores:
                git_hits[idx] = churn_scores[chunk.file_path]

        return {
            "dense_ranked": dense_scores,
            "bm25_ranked": bm25_scores,
            "stack_hits": stack_hits,
            "ui_label_hits": ui_label_hits,
            "git_hits": git_hits,
        }


retriever = Retriever()
