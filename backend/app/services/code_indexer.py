import os
import re
import hashlib
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi
from app.db.models import CodeChunk, Repo
from app.services.repo_ingest import IGNORED_DIRS, EXTENSION_TO_LANG

# Regex patterns for JavaScript/TypeScript functions, components, and classes
JS_FUNCTION_PATTERNS = [
    # export function myFunc( ... ) or function myFunc( ... )
    re.compile(r'(?:export\s+)?(?:default\s+)?function\s+(?P<name>[a-zA-Z0-9_$]+)\s*\('),
    # export const MyComponent = ( ... ) => or const myFunc = function( ... )
    re.compile(r'(?:export\s+)?(?:const|let|var)\s+(?P<name>[a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[a-zA-Z0-9_$]+)\s*=>'),
    re.compile(r'(?:export\s+)?(?:const|let|var)\s+(?P<name>[a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?function'),
    # class MyClass { ... }
    re.compile(r'(?:export\s+)?class\s+(?P<name>[a-zA-Z0-9_$]+)'),
    # object method: myMethod( ... ) {
    re.compile(r'^\s*(?:async\s+)?(?P<name>[a-zA-Z0-9_$]+)\s*\([^)]*\)\s*\{'),
]

# Regex patterns for Python
PY_FUNCTION_PATTERNS = [
    re.compile(r'^\s*(?:async\s+)?def\s+(?P<name>[a-zA-Z0-9_]+)\s*\('),
    re.compile(r'^\s*class\s+(?P<name>[a-zA-Z0-9_]+)(?:\([^)]*\))?:'),
]

# Regex for imports to build dependency graph
JS_IMPORT_REGEX = re.compile(r'(?:import|from)\s+[\'"](?P<import_path>[^\'"]+)[\'"]')
PY_IMPORT_REGEX = re.compile(r'(?:from\s+(?P<mod>[a-zA-Z0-9_.]+)\s+import|import\s+(?P<mod2>[a-zA-Z0-9_.]+))')


class ChunkMetadata:
    def __init__(
        self,
        file_path: str,
        symbol_name: str,
        symbol_type: str,
        start_line: int,
        end_line: int,
        language: str,
        content: str,
        content_hash: str,
    ):
        self.file_path = file_path
        self.symbol_name = symbol_name
        self.symbol_type = symbol_type
        self.start_line = start_line
        self.end_line = end_line
        self.language = language
        self.content = content
        self.content_hash = content_hash


def compute_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def parse_symbols(file_path: str, lines: List[str], language: str) -> List[ChunkMetadata]:
    """Extracts symbols with context line ranges from a file's lines."""
    chunks: List[ChunkMetadata] = []
    total_lines = len(lines)
    if total_lines == 0:
        return chunks

    patterns = JS_FUNCTION_PATTERNS if "Script" in language else PY_FUNCTION_PATTERNS

    detected_starts: List[Tuple[int, str, str]] = []  # (line_no, symbol_name, symbol_type)

    for i, line in enumerate(lines):
        line_num = i + 1
        for p in patterns:
            m = p.search(line)
            if m:
                sname = m.group("name")
                stype = "class" if "class" in line else ("component" if sname[0].isupper() else "function")
                detected_starts.append((line_num, sname, stype))
                break

    # If no symbols detected, chunk the whole file as a module
    if not detected_starts:
        full_content = "".join(lines)
        chunks.append(
            ChunkMetadata(
                file_path=file_path,
                symbol_name=Path(file_path).stem,
                symbol_type="module",
                start_line=1,
                end_line=total_lines,
                language=language,
                content=full_content[:4000],
                content_hash=compute_content_hash(full_content),
            )
        )
        return chunks

    # Calculate end lines based on next symbol or EOF
    for idx, (s_line, sname, stype) in enumerate(detected_starts):
        e_line = detected_starts[idx + 1][0] - 1 if idx + 1 < len(detected_starts) else total_lines
        # Add ±2 context lines where possible
        ctx_start = max(1, s_line - 2)
        ctx_end = min(total_lines, e_line + 2)
        chunk_text = "".join(lines[ctx_start - 1 : ctx_end])

        chunks.append(
            ChunkMetadata(
                file_path=file_path,
                symbol_name=sname,
                symbol_type=stype,
                start_line=s_line,
                end_line=e_line,
                language=language,
                content=chunk_text,
                content_hash=compute_content_hash(chunk_text),
            )
        )

    return chunks


class CodeIndexer:
    def index_repository(self, repo_dir: Path) -> Tuple[List[ChunkMetadata], Dict[str, List[str]], BM25Okapi]:
        """Indexes code files, builds chunks, import graph, and BM25 index."""
        all_chunks: List[ChunkMetadata] = []
        import_graph: Dict[str, List[str]] = {}
        bm25_corpus: List[List[str]] = []

        repo_dir = repo_dir.resolve()

        for root, dirs, files in os.walk(repo_dir):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]

            for file in files:
                ext = Path(file).suffix.lower()
                if ext not in EXTENSION_TO_LANG:
                    continue

                full_path = Path(root) / file
                rel_path = str(full_path.relative_to(repo_dir)).replace("\\", "/")
                language = EXTENSION_TO_LANG[ext]

                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                except Exception:
                    continue

                # Build import graph
                imports: List[str] = []
                for line in lines[:50]:
                    if "Script" in language:
                        for m in JS_IMPORT_REGEX.finditer(line):
                            imports.append(m.group("import_path"))
                    elif "Python" in language:
                        for m in PY_IMPORT_REGEX.finditer(line):
                            mod = m.group("mod") or m.group("mod2")
                            if mod:
                                imports.append(mod)
                import_graph[rel_path] = imports

                # Symbol chunking
                chunks = parse_symbols(rel_path, lines, language)
                for chunk in chunks:
                    all_chunks.append(chunk)
                    tokens = [t.lower() for t in re.findall(r'[a-zA-Z0-9_$]+', chunk.content)]
                    bm25_corpus.append(tokens)

        # Build BM25 index
        if not bm25_corpus:
            bm25_corpus = [["empty"]]
        bm25_index = BM25Okapi(bm25_corpus)

        return all_chunks, import_graph, bm25_index


code_indexer = CodeIndexer()
