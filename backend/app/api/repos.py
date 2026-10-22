import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Repo, CodeChunk
from app.schemas.repo import RepoResponse, RepoDetailResponse, RepoCreateGit
from app.services.repo_ingest import safe_extract_zip, clone_git_repo, calculate_language_stats, get_commit_sha
from app.config import settings

router = APIRouter(prefix="/api/repos", tags=["repos"])


@router.post("", response_model=RepoResponse, status_code=status.HTTP_201_CREATED)
async def create_repo(
    git_url: Optional[str] = Form(None),
    branch: Optional[str] = Form("main"),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    repo_id = str(uuid.uuid4())
    repos_storage = settings.storage_path / "repos" / repo_id
    repos_storage.mkdir(parents=True, exist_ok=True)

    if file and file.filename:
        # ZIP Upload
        if not file.filename.endswith(".zip"):
            raise HTTPException(status_code=400, detail="Only .zip archives are supported.")

        temp_zip = repos_storage / "upload.zip"
        try:
            with open(temp_zip, "wb") as f:
                shutil.copyfileobj(file.file, f)

            extract_target = repos_storage / "source"
            safe_extract_zip(temp_zip, extract_target)
            temp_zip.unlink(missing_ok=True)

            # If zip contained a single root directory, adjust path
            extracted_items = list(extract_target.iterdir())
            if len(extracted_items) == 1 and extracted_items[0].is_dir():
                actual_source = extracted_items[0]
            else:
                actual_source = extract_target

            repo_name = Path(file.filename).stem
            lang_stats = calculate_language_stats(actual_source)
            commit_sha = get_commit_sha(actual_source)

            repo = Repo(
                id=repo_id,
                name=repo_name,
                source_type="zip",
                source_url=None,
                local_path=str(actual_source),
                default_branch="main",
                language_stats=lang_stats,
                index_status="pending",
                commit_sha=commit_sha,
            )
            db.add(repo)
            db.commit()
            db.refresh(repo)
            return repo
        except Exception as e:
            shutil.rmtree(repos_storage, ignore_errors=True)
            raise HTTPException(status_code=400, detail=f"Failed to ingest zip archive: {str(e)}")

    elif git_url:
        try:
            extract_target = repos_storage / "source"
            commit_sha = clone_git_repo(git_url, branch or "main", extract_target)
            repo_name = git_url.rstrip("/").split("/")[-1].replace(".git", "")
            lang_stats = calculate_language_stats(extract_target)

            repo = Repo(
                id=repo_id,
                name=repo_name,
                source_type="git",
                source_url=git_url,
                local_path=str(extract_target),
                default_branch=branch or "main",
                language_stats=lang_stats,
                index_status="pending",
                commit_sha=commit_sha,
            )
            db.add(repo)
            db.commit()
            db.refresh(repo)
            return repo
        except Exception as e:
            shutil.rmtree(repos_storage, ignore_errors=True)
            raise HTTPException(status_code=400, detail=f"Failed to clone git repository: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Either a zip file or git_url must be provided.")


@router.get("", response_model=List[RepoResponse])
def list_repos(db: Session = Depends(get_db)):
    return db.query(Repo).order_by(Repo.created_at.desc()).all()


@router.get("/{id}", response_model=RepoDetailResponse)
def get_repo(id: str, db: Session = Depends(get_db)):
    repo = db.query(Repo).filter(Repo.id == id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    chunk_count = db.query(CodeChunk).filter(CodeChunk.repo_id == id).count()
    return RepoDetailResponse(
        id=repo.id,
        name=repo.name,
        source_type=repo.source_type,
        source_url=repo.source_url,
        default_branch=repo.default_branch,
        language_stats=repo.language_stats,
        index_status=repo.index_status,
        commit_sha=repo.commit_sha,
        created_at=repo.created_at,
        total_chunks=chunk_count,
        total_reports=len(repo.reports),
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repo(id: str, db: Session = Depends(get_db)):
    repo = db.query(Repo).filter(Repo.id == id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Clean local disk files
    try:
        repo_storage = Path(repo.local_path).parent
        if repo_storage.exists() and "repos" in str(repo_storage):
            shutil.rmtree(repo_storage, ignore_errors=True)
    except Exception:
        pass

    db.delete(repo)
    db.commit()
    return None


@router.get("/{id}/file")
def get_repo_file(
    id: str,
    path: str = Query(..., description="Relative file path inside the repo"),
    start: Optional[int] = Query(None, description="Start line (1-indexed)"),
    end: Optional[int] = Query(None, description="End line (inclusive)"),
    db: Session = Depends(get_db),
):
    repo = db.query(Repo).filter(Repo.id == id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    repo_root = Path(repo.local_path).resolve()
    target_file = (repo_root / path).resolve()

    # Path traversal protection
    if not str(target_file).startswith(str(repo_root)):
        raise HTTPException(status_code=400, detail="Invalid file path.")

    if not target_file.is_file():
        raise HTTPException(status_code=404, detail="File does not exist.")

    try:
        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total_lines = len(lines)
        if start is not None and end is not None:
            s = max(1, start) - 1
            e = min(total_lines, end)
            selected_lines = lines[s:e]
            content = "".join(selected_lines)
        else:
            content = "".join(lines)

        return {
            "path": path,
            "total_lines": total_lines,
            "start": start or 1,
            "end": end or total_lines,
            "content": content,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")
