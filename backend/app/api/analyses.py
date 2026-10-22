import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Response, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Analysis, BugReport, Repo, Attachment, Patch
from app.schemas.analysis import AnalysisResponse, AnalysisRerunRequest
from app.services.storage import storage_service
from app.workers.tasks import launch_analysis_job

router = APIRouter(prefix="/api/analyses", tags=["analyses"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_analysis(
    repo_id: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    platform: str = Form("web"),
    screenshots: List[UploadFile] = File(default=[]),
    video: Optional[UploadFile] = File(default=None),
    logs_file: Optional[UploadFile] = File(default=None),
    logs_text: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    repo = db.query(Repo).filter(Repo.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")

    report_id = str(uuid.uuid4())
    report = BugReport(
        id=report_id,
        repo_id=repo_id,
        title=title,
        description=description,
        platform=platform,
    )
    db.add(report)

    # Save screenshots
    for ss in screenshots:
        if ss.filename:
            content = await ss.read()
            s_path = storage_service.save_file(content, ss.filename, subfolder="screenshots")
            att = Attachment(
                report_id=report_id,
                kind="screenshot",
                storage_path=s_path,
                mime=ss.content_type or "image/png",
                meta_info={"filename": ss.filename, "size": len(content)},
            )
            db.add(att)

    # Save video
    if video and video.filename:
        content = await video.read()
        v_path = storage_service.save_file(content, video.filename, subfolder="videos")
        att = Attachment(
            report_id=report_id,
            kind="video",
            storage_path=v_path,
            mime=video.content_type or "video/mp4",
            meta_info={"filename": video.filename, "size": len(content)},
        )
        db.add(att)

    # Save logs file
    if logs_file and logs_file.filename:
        content = await logs_file.read()
        l_path = storage_service.save_file(content, logs_file.filename, subfolder="logs")
        att = Attachment(
            report_id=report_id,
            kind="log",
            storage_path=l_path,
            mime="text/plain",
            meta_info={"filename": logs_file.filename, "size": len(content)},
        )
        db.add(att)

    # Save pasted logs
    if logs_text and logs_text.strip():
        l_bytes = logs_text.encode("utf-8")
        l_path = storage_service.save_file(l_bytes, "pasted_console.log", subfolder="logs")
        att = Attachment(
            report_id=report_id,
            kind="log",
            storage_path=l_path,
            mime="text/plain",
            meta_info={"source": "pasted_text", "size": len(l_bytes)},
        )
        db.add(att)

    # Create Analysis record
    analysis_id = str(uuid.uuid4())
    analysis = Analysis(
        id=analysis_id,
        report_id=report_id,
        status="queued",
        stage="Queued",
        progress=0,
    )
    db.add(analysis)
    db.commit()

    # Trigger background worker / async task
    launch_analysis_job(analysis_id)

    return {
        "analysis_id": analysis_id,
        "report_id": report_id,
        "status": "queued",
        "message": "Analysis initiated.",
    }


@router.get("", response_model=List[AnalysisResponse])
def list_analyses(
    repo_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Analysis).join(BugReport)
    if repo_id:
        query = query.filter(BugReport.repo_id == repo_id)
    if status:
        query = query.filter(Analysis.status == status)

    return query.order_by(Analysis.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{id}", response_model=AnalysisResponse)
def get_analysis(id: str, db: Session = Depends(get_db)):
    analysis = db.query(Analysis).filter(Analysis.id == id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.post("/{id}/rerun", status_code=status.HTTP_200_OK)
def rerun_analysis(
    id: str,
    req: AnalysisRerunRequest,
    db: Session = Depends(get_db),
):
    analysis = db.query(Analysis).filter(Analysis.id == id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis.status = "queued"
    analysis.stage = "Queued"
    analysis.progress = 0
    analysis.error = None
    db.commit()

    custom_weights = {k: v for k, v in req.model_dump().items() if v is not None}
    launch_analysis_job(id, custom_weights=custom_weights)

    return {"status": "queued", "message": "Analysis rerun initiated."}


@router.get("/{id}/export")
def export_analysis_report(
    id: str,
    format: str = Query("md", regex="^(md|json)$"),
    db: Session = Depends(get_db),
):
    analysis = db.query(Analysis).filter(Analysis.id == id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    report = db.query(BugReport).filter(BugReport.id == analysis.report_id).first()
    repo = db.query(Repo).filter(Repo.id == report.repo_id).first()
    patch = (
        db.query(Patch)
        .filter(Patch.analysis_id == id)
        .order_by(Patch.created_at.desc())
        .first()
    )

    if format == "json":
        return AnalysisResponse.model_validate(analysis)

    # Markdown export
    suspects_md = ""
    for idx, s in enumerate(analysis.suspects or [], 1):
        evs = "\n".join([f"    - **{e.get('type')}**: {e.get('detail')}" for e in s.get("evidence", [])])
        suspects_md += f"{idx}. `{s.get('file_path')}` (lines {s.get('lines', [1,1])[0]}-{s.get('lines', [1,1])[1]}) — **Score: {s.get('score')}** (Relative Rank)\n{evs}\n\n"

    diff_block = f"```diff\n{patch.diff_text}\n```" if patch else "No patch generated."
    v_badge = patch.verification_status if patch else "unverified"

    markdown_content = f"""# SightFix AI Analysis Report
**Report Title**: {report.title}
**Repository**: {repo.name} ({repo.default_branch})
**Date**: {analysis.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
**Status**: {analysis.status.upper()} | **Verification**: {v_badge.upper()}

---

## 1. Problem Description
{report.description}

## 2. Visual Findings
- **Summary**: {analysis.visual_findings.get('summary', 'None')}
- **Image Quality**: {analysis.visual_findings.get('image_quality', 'unknown')}

## 3. Log Insights
- **Error Signatures**: {len(analysis.log_findings.get('error_signatures', []))}
- **Stack Frames**: {len(analysis.log_findings.get('stack_frames', []))}

## 4. Root Cause Hypothesis
> {analysis.root_cause_hypothesis or 'Investigation in progress'}

## 5. Top Ranked Suspects
{suspects_md or 'No suspects identified.'}

## 6. Generated Patch ({v_badge.upper()})
{diff_block}

### Rationale
{patch.rationale if patch else 'N/A'}
"""
    return Response(
        content=markdown_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=sightfix-report-{id[:8]}.md"},
    )
