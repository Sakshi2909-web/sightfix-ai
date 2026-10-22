from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Analysis, Patch, Repo, BugReport, AnalysisFeedback
from app.schemas.patch import PatchResponse, PatchRegenerateRequest
from app.schemas.analysis import AnalysisFeedbackCreate, Suspect
from app.services.patcher import Patcher
from app.services.sandbox import sandbox_verifier
from app.providers.factory import get_llm_provider
from app.config import settings

router = APIRouter(prefix="/api/analyses", tags=["patches"])


@router.get("/{id}/patch", response_model=PatchResponse)
def get_latest_patch(id: str, db: Session = Depends(get_db)):
    patch = (
        db.query(Patch)
        .filter(Patch.analysis_id == id)
        .order_by(Patch.created_at.desc())
        .first()
    )
    if not patch:
        raise HTTPException(status_code=404, detail="No patch found for this analysis.")
    return patch


@router.post("/{id}/patch/regenerate", response_model=PatchResponse)
async def regenerate_patch(
    id: str,
    req: PatchRegenerateRequest,
    db: Session = Depends(get_db),
):
    analysis = db.query(Analysis).filter(Analysis.id == id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    report = db.query(BugReport).filter(BugReport.id == analysis.report_id).first()
    repo = db.query(Repo).filter(Repo.id == report.repo_id).first()
    repo_dir = Path(repo.local_path).resolve()

    llm = get_llm_provider()
    patcher = Patcher(repo_dir=repo_dir, llm=llm)

    suspect_objs = [Suspect(**s) for s in (analysis.suspects or [])]
    patch_res = await patcher.generate_patch(
        root_cause_hypothesis=analysis.root_cause_hypothesis or "Bug repair",
        suspects=suspect_objs,
        feedback=req.feedback,
    )

    # Sandbox verify the regenerated patch
    v_status, v_output, v_meta = sandbox_verifier.verify_patch(
        repo_dir=repo_dir,
        diff_text=patch_res.diff_text,
        timeout_sec=settings.SANDBOX_TIMEOUT_SEC,
    )

    new_patch = Patch(
        analysis_id=analysis.id,
        target_files=patch_res.target_files,
        diff_text=patch_res.diff_text,
        rationale=f"[Regenerated with user feedback: '{req.feedback}'] {patch_res.rationale}",
        verification_status=v_status,
        test_output=v_output,
        sandbox_meta=v_meta,
        suggested_tests=patch_res.suggested_tests,
    )
    db.add(new_patch)
    db.commit()
    db.refresh(new_patch)
    return new_patch


@router.post("/{id}/feedback", status_code=status.HTTP_201_CREATED)
def submit_feedback(
    id: str,
    feedback: AnalysisFeedbackCreate,
    db: Session = Depends(get_db),
):
    analysis = db.query(Analysis).filter(Analysis.id == id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    fb = AnalysisFeedback(
        analysis_id=id,
        suspect_rank_correct=feedback.suspect_rank_correct,
        correct_file=feedback.correct_file,
    )
    db.add(fb)
    db.commit()
    return {"status": "ok", "message": "Feedback recorded."}
