import os
import shutil
import uuid
from pathlib import Path
from app.db.session import SessionLocal
from app.db.base import Base
from app.db.session import engine
from app.db.models import Repo, BugReport, Attachment
from app.services.repo_ingest import calculate_language_stats
from app.config import settings


def seed_demo_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    project_root = Path(__file__).resolve().parent.parent.parent
    demo_source = project_root / "sample_data" / "demo_repo_login_bug"
    sample_ss = project_root / "sample_data" / "screenshots" / "login_unresponsive.png"
    sample_log = project_root / "sample_data" / "logs" / "console.log"

    print("Checking existing demo repo...")
    existing = db.query(Repo).filter(Repo.name == "demo_repo_login_bug").first()
    if existing:
        print(f"Demo repo already seeded with id: {existing.id}")
        db.close()
        return existing.id

    repo_id = str(uuid.uuid4())
    repo_dest = settings.storage_path / "repos" / repo_id / "source"
    repo_dest.mkdir(parents=True, exist_ok=True)
    shutil.copytree(demo_source, repo_dest, dirs_exist_ok=True)

    lang_stats = calculate_language_stats(repo_dest)

    repo = Repo(
        id=repo_id,
        name="demo_repo_login_bug",
        source_type="zip",
        local_path=str(repo_dest),
        default_branch="main",
        language_stats=lang_stats,
        index_status="ready",
    )
    db.add(repo)
    db.commit()

    # Create pre-loaded demo report
    report_id = str(uuid.uuid4())
    report = BugReport(
        id=report_id,
        repo_id=repo_id,
        title="Sign in button unresponsive when submitting login form",
        description="Clicking 'Sign in' does nothing when credentials are entered. The button stays active or disabled without any loading state or transition, and console shows TypeError.",
        platform="web",
    )
    db.add(report)

    # Attach screenshot if exists
    if sample_ss.exists():
        att_ss_path = settings.storage_path / "screenshots"
        att_ss_path.mkdir(parents=True, exist_ok=True)
        dest_ss = att_ss_path / f"{uuid.uuid4()}.png"
        shutil.copyfile(sample_ss, dest_ss)
        att = Attachment(
            report_id=report_id,
            kind="screenshot",
            storage_path=str(dest_ss),
            mime="image/png",
            meta_info={"filename": "login_unresponsive.png"},
        )
        db.add(att)

    # Attach log
    if sample_log.exists():
        att_log_path = settings.storage_path / "logs"
        att_log_path.mkdir(parents=True, exist_ok=True)
        dest_log = att_log_path / f"{uuid.uuid4()}.log"
        shutil.copyfile(sample_log, dest_log)
        att = Attachment(
            report_id=report_id,
            kind="log",
            storage_path=str(dest_log),
            mime="text/plain",
            meta_info={"filename": "console.log"},
        )
        db.add(att)

    db.commit()
    print(f"Successfully seeded demo repo '{repo.name}' (ID: {repo.id}) and report (ID: {report.id})")
    db.close()
    return repo.id


if __name__ == "__main__":
    seed_demo_data()
