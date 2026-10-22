import asyncio
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import Analysis, BugReport, Repo, Attachment, Patch, CodeChunk
from app.schemas.analysis import VisualFindings, LogFindings, Suspect
from app.services.broadcaster import broadcaster
from app.services.video_frames import video_frame_extractor
from app.services.vision import vision_service
from app.services.log_parser import log_parser
from app.services.code_indexer import code_indexer
from app.services.git_signals import git_signals
from app.services.retriever import retriever
from app.services.ranker import fusion_ranker
from app.services.investigator import Investigator
from app.services.patcher import Patcher
from app.services.sandbox import sandbox_verifier
from app.providers.factory import get_llm_provider
from app.config import settings


async def run_analysis_pipeline(analysis_id: str, custom_weights: Optional[Dict[str, float]] = None):
    """Executes the full 9-stage multimodal analysis pipeline."""
    db: Session = SessionLocal()
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            return

        report = db.query(BugReport).filter(BugReport.id == analysis.report_id).first()
        if not report:
            analysis.status = "failed"
            analysis.error = "Associated bug report not found."
            db.commit()
            return

        repo = db.query(Repo).filter(Repo.id == report.repo_id).first()
        if not repo:
            analysis.status = "failed"
            analysis.error = "Associated repository not found."
            db.commit()
            return

        repo_dir = Path(repo.local_path).resolve()

        async def update_stage(stage_name: str, progress: int, partial_data: Optional[Dict[str, Any]] = None):
            analysis.stage = stage_name
            analysis.progress = progress
            db.commit()
            await broadcaster.emit(
                analysis_id,
                "progress",
                {
                    "analysis_id": analysis_id,
                    "stage": stage_name,
                    "progress": progress,
                    "partial": partial_data or {},
                },
            )

        analysis.status = "running"
        db.commit()

        # ==========================================
        # Stage 1: Ingest (0 - 10%)
        # ==========================================
        await update_stage("Ingest", 5)

        attachments = db.query(Attachment).filter(Attachment.report_id == report.id).all()
        image_bytes_list: List[bytes] = []
        logs_text: str = ""

        for att in attachments:
            p = Path(att.storage_path)
            if not p.exists():
                continue
            if att.kind == "screenshot":
                image_bytes_list.append(p.read_bytes())
            elif att.kind == "video":
                v_frames = video_frame_extractor.extract_keyframes(p, max_frames=6)
                image_bytes_list.extend(v_frames)
            elif att.kind == "log":
                try:
                    logs_text += "\n" + p.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    pass

        # Validate max images
        image_bytes_list = image_bytes_list[:6]
        await update_stage("Ingest", 10)

        # ==========================================
        # Stage 2: Visual Understanding (10 - 30%)
        # ==========================================
        await update_stage("Visual Understanding", 15)
        visual_findings = VisualFindings()
        try:
            if image_bytes_list:
                v_findings, img_embeddings = await vision_service.analyze_visual_evidence(
                    image_bytes_list, report.description
                )
                visual_findings = v_findings
            else:
                visual_findings = VisualFindings(
                    summary="No visual assets attached; proceeding with text & log analysis.",
                    image_quality="irrelevant",
                )
        except Exception as e:
            # Graceful partial failure
            visual_findings = VisualFindings(
                summary=f"Visual analysis partial warning: {str(e)}",
                image_quality="low",
            )

        analysis.visual_findings = visual_findings.model_dump()
        db.commit()
        await update_stage("Visual Understanding", 30, {"visual_findings": analysis.visual_findings})

        # ==========================================
        # Stage 3: Log Analysis (30 - 40%)
        # ==========================================
        await update_stage("Log Analysis", 32)
        parsed_logs = log_parser.parse(logs_text)
        analysis.log_findings = parsed_logs.model_dump()
        db.commit()
        await update_stage("Log Analysis", 40, {"log_findings": analysis.log_findings})

        # ==========================================
        # Stage 4: Repo Index (40 - 55%)
        # ==========================================
        await update_stage("Repo Indexing", 45)
        chunks, import_graph, bm25_index = code_indexer.index_repository(repo_dir)

        # Update repo status and chunk cache if pending
        if repo.index_status != "ready":
            repo.index_status = "ready"
            db.query(CodeChunk).filter(CodeChunk.repo_id == repo.id).delete()
            for c in chunks:
                chunk_rec = CodeChunk(
                    repo_id=repo.id,
                    file_path=c.file_path,
                    symbol_name=c.symbol_name,
                    symbol_type=c.symbol_type,
                    start_line=c.start_line,
                    end_line=c.end_line,
                    language=c.language,
                    content_hash=c.content_hash,
                    content=c.content,
                )
                db.add(chunk_rec)
            db.commit()

        await update_stage("Repo Indexing", 55)

        # ==========================================
        # Stage 5: Hybrid Retrieval (55 - 70%)
        # ==========================================
        await update_stage("Hybrid Retrieval", 60)
        churn_scores = git_signals.get_recent_churn(repo_dir)

        retrieval_results = await retriever.retrieve_candidates(
            chunks=chunks,
            bm25_index=bm25_index,
            description=report.description,
            visual_findings=visual_findings,
            log_findings=parsed_logs,
            churn_scores=churn_scores,
            import_graph=import_graph,
        )
        await update_stage("Hybrid Retrieval", 70)

        # ==========================================
        # Stage 6: Fusion Ranking (70 - 80%)
        # ==========================================
        await update_stage("Fusion Ranking", 72)
        suspects = fusion_ranker.rank_candidates(
            chunks=chunks,
            retrieval_results=retrieval_results,
            weights=custom_weights,
            top_k=10,
        )
        analysis.suspects = [s.model_dump() for s in suspects]
        db.commit()
        await update_stage("Fusion Ranking", 80, {"suspects": analysis.suspects})

        # ==========================================
        # Stage 7: Agentic Investigation (80 - 90%)
        # ==========================================
        await update_stage("Agentic Investigation", 82)
        llm = get_llm_provider()
        investigator = Investigator(repo_dir=repo_dir, llm=llm)

        reordered_suspects, root_cause_hyp, trace = await investigator.run_investigation(
            suspects=suspects,
            visual_findings=visual_findings,
            log_findings=parsed_logs,
            description=report.description,
        )

        analysis.suspects = [s.model_dump() for s in reordered_suspects]
        analysis.root_cause_hypothesis = root_cause_hyp
        analysis.investigation_trace = [t.model_dump() for t in trace]
        db.commit()
        await update_stage(
            "Agentic Investigation",
            90,
            {
                "root_cause_hypothesis": root_cause_hyp,
                "investigation_trace": analysis.investigation_trace,
            },
        )

        # ==========================================
        # Stage 8: Patch Generation (90 - 95%)
        # ==========================================
        await update_stage("Patch Generation", 92)
        patcher = Patcher(repo_dir=repo_dir, llm=llm)
        patch_res = await patcher.generate_patch(
            root_cause_hypothesis=root_cause_hyp,
            suspects=reordered_suspects,
        )

        patch_rec = Patch(
            analysis_id=analysis.id,
            target_files=patch_res.target_files,
            diff_text=patch_res.diff_text,
            rationale=patch_res.rationale,
            verification_status="unverified",
            suggested_tests=patch_res.suggested_tests,
        )
        db.add(patch_rec)
        db.commit()
        db.refresh(patch_rec)
        await update_stage("Patch Generation", 95, {"patch_id": patch_rec.id})

        # ==========================================
        # Stage 9: Sandbox Verification (95 - 100%)
        # ==========================================
        await update_stage("Sandbox Verification", 96)
        v_status, v_output, v_meta = sandbox_verifier.verify_patch(
            repo_dir=repo_dir,
            diff_text=patch_res.diff_text,
            timeout_sec=settings.SANDBOX_TIMEOUT_SEC,
        )

        patch_rec.verification_status = v_status
        patch_rec.test_output = v_output
        patch_rec.sandbox_meta = v_meta

        analysis.status = "completed"
        analysis.progress = 100
        analysis.stage = "Completed"
        analysis.finished_at = datetime.now(timezone.utc)
        db.commit()

        await broadcaster.emit(
            analysis_id,
            "completed",
            {
                "analysis_id": analysis_id,
                "status": "completed",
                "progress": 100,
                "verification_status": v_status,
            },
        )

    except Exception as e:
        analysis.status = "failed"
        analysis.error = str(e)
        analysis.stage = "Failed"
        db.commit()
        await broadcaster.emit(
            analysis_id,
            "error",
            {"analysis_id": analysis_id, "error": str(e)},
        )
    finally:
        db.close()


def launch_analysis_job(analysis_id: str, custom_weights: Optional[Dict[str, float]] = None):
    """Launches analysis job asynchronously."""
    asyncio.create_task(run_analysis_pipeline(analysis_id, custom_weights))
