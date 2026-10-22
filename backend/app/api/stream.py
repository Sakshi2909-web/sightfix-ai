import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Analysis
from app.services.broadcaster import broadcaster

router = APIRouter(prefix="/api/analyses", tags=["analyses"])


@router.get("/{id}/stream")
async def stream_analysis(id: str, db: Session = Depends(get_db)):
    analysis = db.query(Analysis).filter(Analysis.id == id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    async def event_generator():
        q = broadcaster.subscribe(id)
        try:
            # Emit current snapshot
            init_payload = {
                "event": "snapshot",
                "data": {
                    "analysis_id": analysis.id,
                    "status": analysis.status,
                    "stage": analysis.stage,
                    "progress": analysis.progress,
                    "visual_findings": analysis.visual_findings,
                    "log_findings": analysis.log_findings,
                    "suspects": analysis.suspects,
                    "investigation_trace": analysis.investigation_trace,
                    "root_cause_hypothesis": analysis.root_cause_hypothesis,
                },
            }
            yield f"event: {init_payload['event']}\ndata: {json.dumps(init_payload['data'])}\n\n"

            # If already completed or failed, close after snapshot
            if analysis.status in ["completed", "failed"]:
                return

            while True:
                # Wait for next event or heartbeat
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=15.0)
                    evt = msg.get("event", "message")
                    data = msg.get("data", {})
                    yield f"event: {evt}\ndata: {json.dumps(data)}\n\n"
                    if evt in ["completed", "error"]:
                        break
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat
                    yield ": ping\n\n"
        finally:
            broadcaster.unsubscribe(id, q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
