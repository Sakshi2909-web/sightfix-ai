from typing import List, Dict, Any, Optional
from app.services.code_indexer import ChunkMetadata
from app.schemas.analysis import Suspect, SuspectEvidence
from app.config import settings


def compute_rrf(rank: int, k: int = 60) -> float:
    return 1.0 / (k + rank)


class FusionRanker:
    def rank_candidates(
        self,
        chunks: List[ChunkMetadata],
        retrieval_results: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None,
        top_k: int = 10,
    ) -> List[Suspect]:
        if not chunks:
            return []

        w = weights or {
            "w_dense": settings.W_DENSE,
            "w_lex": settings.W_LEX,
            "w_stack": settings.W_STACK,
            "w_ui": settings.W_UI,
            "w_git": settings.W_GIT,
            "w_graph": settings.W_GRAPH,
        }

        dense_ranked = retrieval_results.get("dense_ranked", [])
        bm25_ranked = retrieval_results.get("bm25_ranked", [])
        stack_hits = retrieval_results.get("stack_hits", {})
        ui_label_hits = retrieval_results.get("ui_label_hits", {})
        git_hits = retrieval_results.get("git_hits", {})

        # Compute RRF maps
        rrf_dense: Dict[int, float] = {}
        for rank, (idx, _) in enumerate(dense_ranked[:50]):
            rrf_dense[idx] = compute_rrf(rank + 1)

        rrf_lex: Dict[int, float] = {}
        for rank, (idx, _) in enumerate(bm25_ranked[:50]):
            rrf_lex[idx] = compute_rrf(rank + 1)

        raw_scores: Dict[int, float] = {}
        evidence_map: Dict[int, List[SuspectEvidence]] = {}

        for idx, chunk in enumerate(chunks):
            ev_list: List[SuspectEvidence] = []
            score = 0.0

            # Dense component
            d_rrf = rrf_dense.get(idx, 0.0)
            score += w.get("w_dense", 0.25) * d_rrf
            if d_rrf > compute_rrf(15):
                ev_list.append(
                    SuspectEvidence(type="semantic", detail="High semantic relevance with issue symptom and UI findings")
                )

            # Lexical BM25 component
            l_rrf = rrf_lex.get(idx, 0.0)
            score += w.get("w_lex", 0.20) * l_rrf
            if l_rrf > compute_rrf(15):
                ev_list.append(
                    SuspectEvidence(type="lexical", detail="Code matches key error tokens and component keywords")
                )

            # Stack frame direct hit
            if idx in stack_hits:
                score += w.get("w_stack", 0.30) * 1.0
                ev_list.append(SuspectEvidence(type="stack_frame", detail=stack_hits[idx]))

            # UI label match
            if idx in ui_label_hits:
                score += w.get("w_ui", 0.15) * 1.0
                ev_list.append(SuspectEvidence(type="ui_label", detail=ui_label_hits[idx]))

            # Git recency
            if idx in git_hits:
                g_val = git_hits[idx]
                score += w.get("w_git", 0.05) * g_val
                ev_list.append(
                    SuspectEvidence(type="git_recent", detail=f"High churn recency score ({g_val:.2f}) in recent commits")
                )

            raw_scores[idx] = score
            evidence_map[idx] = ev_list

        # Normalize relative rank score to (0.0 .. 1.0)
        max_score = max(raw_scores.values()) if raw_scores else 1.0
        if max_score <= 0.0:
            max_score = 1.0

        sorted_indices = sorted(raw_scores.keys(), key=lambda i: raw_scores[i], reverse=True)

        suspects: List[Suspect] = []
        seen_symbols = set()

        for idx in sorted_indices:
            chunk = chunks[idx]
            sym_key = f"{chunk.file_path}:{chunk.symbol_name}"
            if sym_key in seen_symbols:
                continue
            seen_symbols.add(sym_key)

            # Honest relative rank score calculation
            relative_score = round(raw_scores[idx] / max_score, 2)
            ev = evidence_map.get(idx, [])
            if not ev:
                ev.append(SuspectEvidence(type="semantic", detail="Lexical & structural proximity to module context"))

            suspects.append(
                Suspect(
                    file_path=chunk.file_path,
                    symbol=chunk.symbol_name,
                    lines=[chunk.start_line, chunk.end_line],
                    score=relative_score,
                    evidence=ev,
                )
            )
            if len(suspects) >= top_k:
                break

        return suspects


fusion_ranker = FusionRanker()
