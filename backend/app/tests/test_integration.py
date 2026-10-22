import pytest
import uuid
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Analysis, BugReport, Repo, Patch
from app.workers.tasks import run_analysis_pipeline


@pytest.mark.asyncio
async def test_end_to_end_analysis_pipeline():
    db: Session = SessionLocal()
    # Find demo repo
    repo = db.query(Repo).filter(Repo.name == "demo_repo_login_bug").first()
    assert repo is not None, "Demo repo must be seeded."

    report = db.query(BugReport).filter(BugReport.repo_id == repo.id).first()
    assert report is not None, "Demo report must be seeded."

    analysis_id = str(uuid.uuid4())
    analysis = Analysis(
        id=analysis_id,
        report_id=report.id,
        status="queued",
        stage="Queued",
        progress=0,
    )
    db.add(analysis)
    db.commit()
    db.close()

    # Execute full pipeline
    await run_analysis_pipeline(analysis_id)

    # Verify results in DB
    db = SessionLocal()
    completed = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    assert completed is not None
    assert completed.status == "completed"
    assert completed.progress == 100

    # 1. Top 3 contains LoginForm
    assert completed.suspects is not None and len(completed.suspects) > 0
    top_suspect_files = [s["file_path"] for s in completed.suspects[:3]]
    assert any("LoginForm" in f for f in top_suspect_files), f"LoginForm not in top 3: {top_suspect_files}"

    # 2. Suspect has evidence reasons
    top_suspect = completed.suspects[0]
    assert len(top_suspect["evidence"]) >= 1
    assert top_suspect["score"] > 0.0

    # 3. Root cause hypothesis is generated
    assert completed.root_cause_hypothesis is not None
    assert len(completed.root_cause_hypothesis) > 10

    # 4. Patch is generated and verified
    patch = db.query(Patch).filter(Patch.analysis_id == analysis_id).first()
    assert patch is not None
    assert "LoginForm" in patch.diff_text
    assert patch.verification_status in ["passed", "unverified"]
    if patch.verification_status == "passed":
        assert "PASSED" in (patch.test_output or "").upper() or "PASS" in (patch.test_output or "").upper()

    db.close()
