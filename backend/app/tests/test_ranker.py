from app.services.code_indexer import ChunkMetadata
from app.services.ranker import fusion_ranker, compute_rrf


def test_rrf_math():
    r1 = compute_rrf(1)
    r2 = compute_rrf(2)
    assert r1 > r2
    assert r1 == 1.0 / 61.0


def test_fusion_ranker_evidence_and_boost():
    chunks = [
        ChunkMetadata(
            file_path="src/auth/LoginForm.jsx",
            symbol_name="handleSubmit",
            symbol_type="function",
            start_line=15,
            end_line=30,
            language="JavaScript (React)",
            content="const handleSubmit = (e) => { ... }",
            content_hash="abc1",
        ),
        ChunkMetadata(
            file_path="src/utils/format.js",
            symbol_name="formatDate",
            symbol_type="function",
            start_line=1,
            end_line=10,
            language="JavaScript",
            content="export function formatDate() { ... }",
            content_hash="abc2",
        ),
    ]

    retrieval_results = {
        "dense_ranked": [(0, 0.95), (1, 0.10)],
        "bm25_ranked": [(0, 4.2), (1, 0.5)],
        "stack_hits": {0: "Appears in stack trace at line 24"},
        "ui_label_hits": {0: "Contains button text 'Sign in' seen in screenshot"},
        "git_hits": {0: 0.9},
    }

    suspects = fusion_ranker.rank_candidates(chunks, retrieval_results)

    assert len(suspects) == 2
    top = suspects[0]
    assert top.file_path == "src/auth/LoginForm.jsx"
    assert top.symbol == "handleSubmit"
    assert top.score == 1.0  # Normalized relative rank score top is 1.0

    ev_types = [e.type for e in top.evidence]
    assert "stack_frame" in ev_types
    assert "ui_label" in ev_types
    assert "git_recent" in ev_types
