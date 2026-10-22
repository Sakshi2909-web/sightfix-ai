import os
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Any, Tuple
import git
from app.config import settings

IGNORED_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    ".next",
    "target",
    "bin",
    "obj",
}

EXTENSION_TO_LANG = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".java": "Java",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".dart": "Dart",
    ".go": "Go",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".c": "C",
    ".cpp": "C++",
    ".cs": "C#",
    ".html": "HTML",
    ".css": "CSS",
    ".json": "JSON",
}

MAX_EXTRACT_BYTES = 200 * 1024 * 1024  # 200 MB limit


class IngestError(Exception):
    pass


def safe_extract_zip(zip_path: Path, target_dir: Path) -> None:
    """Extracts a zip file safely, preventing zip-slip, symlinks, and excessive size."""
    target_dir = target_dir.resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    total_bytes = 0

    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            # Check for symlinks
            if member.is_dir():
                continue
            # Some zip formats store symlinks in external_attr
            if (member.external_attr >> 16) & 0o120000 == 0o120000:
                continue

            # Zip slip check
            dest_file = (target_dir / member.filename).resolve()
            if not str(dest_file).startswith(str(target_dir)):
                raise IngestError(f"Illegal zip member path (zip-slip detected): {member.filename}")

            total_bytes += member.file_size
            if total_bytes > MAX_EXTRACT_BYTES:
                raise IngestError("Extracted repository size exceeds limit (200MB).")

            dest_file.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as source, open(dest_file, "wb") as target:
                shutil.copyfileobj(source, target)


def calculate_language_stats(repo_dir: Path) -> Dict[str, int]:
    """Calculates language breakdown by total lines of code."""
    stats: Dict[str, int] = {}
    for root, dirs, files in os.walk(repo_dir):
        # Exclude ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]

        for file in files:
            ext = Path(file).suffix.lower()
            if ext in EXTENSION_TO_LANG:
                lang = EXTENSION_TO_LANG[ext]
                file_path = Path(root) / file
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = sum(1 for _ in f)
                        stats[lang] = stats.get(lang, 0) + lines
                except Exception:
                    continue
    return stats


def get_commit_sha(repo_dir: Path) -> str | None:
    """Retrieves HEAD commit SHA if valid git repo, else returns None."""
    try:
        repo = git.Repo(repo_dir)
        return repo.head.commit.hexsha
    except Exception:
        return None


def clone_git_repo(git_url: str, branch: str, target_dir: Path) -> str | None:
    """Clones a git repository into target_dir."""
    target_dir.mkdir(parents=True, exist_ok=True)
    repo = git.Repo.clone_from(git_url, str(target_dir), branch=branch, depth=50)
    return repo.head.commit.hexsha
