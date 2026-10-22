import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import BugReport, Attachment, Repo
from app.schemas.report import BugReportResponse
from app.services.storage import storage_service

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("", response_model=BugReportResponse, status_code=status.HTTP_201_CREATED)
async def create_bug_report(
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
    db.commit()

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

    db.commit()
    db.refresh(report)
    return report


@router.get("/{id}", response_model=BugReportResponse)
def get_bug_report(id: str, db: Session = Depends(get_db)):
    report = db.query(BugReport).filter(BugReport.id == id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Bug report not found.")
    return report
