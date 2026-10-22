import asyncio
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import Analysis, BugReport, Repo, Attachment, Patch
from app.workers.tasks import run_analysis_pipeline


async def evaluate_benchmark():
    eval_dir = Path(__file__).resolve().parent
    dataset_file = eval_dir / "benchmark_dataset.json"
    project_root = eval_dir.parent.parent

    with open(dataset_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    samples = data.get("samples", [])
    print(f"\n=======================================================")
    print(f" SightFix AI Evaluation Suite — {data.get('benchmark_name')}")
    print(f" Total Evaluation Samples: {len(samples)}")
    print(f"=======================================================\n")

    db: Session = SessionLocal()

    ranks: List[int] = []
    function_hits: List[bool] = []
    patch_applied: List[bool] = []
    sandbox_passed: List[bool] = []

    for sample in samples:
        repo_name = sample["repo_name"]
        repo = db.query(Repo).filter(Repo.name == repo_name).first()
        if not repo:
            print(f"[SKIP] Repo '{repo_name}' not found. Run seed script first.")
            continue

        report_id = str(uuid.uuid4())
        report = BugReport(
            id=report_id,
            repo_id=repo.id,
            title=sample["title"],
            description=sample["description"],
            platform="web",
        )
        db.add(report)

        # Attach log
        log_p = project_root / sample["logs_path"]
        if log_p.exists():
            db.add(
                Attachment(
                    report_id=report_id,
                    kind="log",
                    storage_path=str(log_p),
                    mime="text/plain",
                )
            )

        # Attach screenshot
        ss_p = project_root / sample["screenshot_path"]
        if ss_p.exists():
            db.add(
                Attachment(
                    report_id=report_id,
                    kind="screenshot",
                    storage_path=str(ss_p),
                    mime="image/png",
                )
            )

        db.commit()

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

        print(f"Running analysis for: '{sample['id']}' ...")
        await run_analysis_pipeline(analysis_id)

        # Evaluate suspect rank
        db.refresh(analysis)
        suspects = analysis.suspects or []
        gold_files = [g.replace("\\", "/") for g in sample["gold_files"]]
        gold_funcs = sample["gold_functions"]

        found_rank = None
        func_hit = False

        for rank_idx, suspect in enumerate(suspects, 1):
            s_file = suspect.get("file_path", "").replace("\\", "/")
            if any(s_file.endswith(g) or g.endswith(s_file) for g in gold_files):
                if found_rank is None:
                    found_rank = rank_idx
                if suspect.get("symbol") in gold_funcs:
                    func_hit = True

        ranks.append(found_rank if found_rank is not None else 999)
        function_hits.append(func_hit)

        # Check patch & sandbox verification
        patch = (
            db.query(Patch)
            .filter(Patch.analysis_id == analysis_id)
            .order_by(Patch.created_at.desc())
            .first()
        )
        if patch:
            patch_applied.append(patch.verification_status != "error")
            sandbox_passed.append(patch.verification_status == "passed")
        else:
            patch_applied.append(False)
            sandbox_passed.append(False)

        print(
            f"  Result -> Gold File Rank: {found_rank} | Func Hit: {func_hit} | Sandbox: {patch.verification_status if patch else 'none'}"
        )

    db.close()

    total = len(ranks)
    if total == 0:
        print("No samples evaluated.")
        return

    acc1 = sum(1 for r in ranks if r == 1) / total
    acc3 = sum(1 for r in ranks if r <= 3) / total
    acc5 = sum(1 for r in ranks if r <= 5) / total
    mrr = sum(1.0 / r for r in ranks) / total
    func_acc = sum(1 for h in function_hits if h) / total
    apply_rate = sum(1 for a in patch_applied if a) / total
    pass_rate = sum(1 for p in sandbox_passed if p) / total

    print(f"\n=======================================================")
    print(f" EVALUATION SUMMARY METRICS")
    print(f"=======================================================")
    print(f" Acc@1 (File level):       {acc1 * 100:.1f}%")
    print(f" Acc@3 (File level):       {acc3 * 100:.1f}%")
    print(f" Acc@5 (File level):       {acc5 * 100:.1f}%")
    print(f" MRR (Mean Reciprocal):    {mrr:.3f}")
    print(f" Function-level Hit Rate:  {func_acc * 100:.1f}%")
    print(f" Patch Apply Rate:         {apply_rate * 100:.1f}%")
    print(f" Sandbox Pass Rate:        {pass_rate * 100:.1f}%")
    print(f"=======================================================\n")


if __name__ == "__main__":
    asyncio.run(evaluate_benchmark())
