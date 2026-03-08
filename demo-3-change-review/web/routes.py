"""
API routes for Change Review web UI.

Endpoints:
  POST /api/review           — start a pipeline run, returns {job_id}
  POST /api/improve          — start an improvement analysis, returns {job_id}
  GET  /api/stream/{id}      — SSE stream of pipeline events for a job
"""
import asyncio
import json
from typing import AsyncGenerator, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

import sys
sys.path.insert(0, str(__file__).replace("web/routes.py", ""))

from improve_orchestrator import ImprovementOrchestrator
from orchestrator import Orchestrator
from web.jobs import create_job, emit, get_queue, remove_job

router = APIRouter()

# ── Request / response models ──────────────────────────────────

class ReviewRequest(BaseModel):
    commit_range: Optional[str] = None
    draft_type: Optional[str] = None  # "issue", "pr", or None
    instruction: Optional[str] = None


class ImproveRequest(BaseModel):
    issue_id: Optional[str] = None
    pr_id: Optional[str] = None


# ── POST /api/review ───────────────────────────────────────────

@router.post("/review")
async def start_review(req: ReviewRequest):
    job_id = create_job()
    asyncio.create_task(_run_pipeline(job_id, req.commit_range, req.draft_type, req.instruction))
    return {"job_id": job_id}


# ── POST /api/improve ──────────────────────────────────────────

@router.post("/improve")
async def start_improve(req: ImproveRequest):
    if not req.issue_id and not req.pr_id:
        return JSONResponse({"error": "Provide either issue_id or pr_id"}, status_code=400)
    if req.issue_id and req.pr_id:
        return JSONResponse({"error": "Provide only one of issue_id or pr_id"}, status_code=400)

    job_id = create_job()
    asyncio.create_task(_run_improvement(job_id, req.issue_id, req.pr_id))
    return {"job_id": job_id}


async def _run_pipeline(
    job_id: str,
    commit_range: Optional[str],
    draft_type: Optional[str],
    instruction: Optional[str],
) -> None:
    loop = asyncio.get_event_loop()
    current_agent_state: dict = {"current": None}

    def tracked_emit(agent: str, message: str) -> None:
        agent_order = ["Analyzer", "Categorizer", "RiskAssessor", "DecisionMaker", "IssueDrafter", "PRDrafter", "Orchestrator"]
        if agent != current_agent_state["current"] and agent in agent_order:
            asyncio.run_coroutine_threadsafe(
                emit(job_id, {"type": "agent_start", "agent": agent}),
                loop,
            )
            current_agent_state["current"] = agent

        asyncio.run_coroutine_threadsafe(
            emit(job_id, {
                "type": "log",
                "agent": agent,
                "message": message,
                "is_tool": False,
            }),
            loop,
        )

    try:
        orchestrator = Orchestrator()
        report = await orchestrator.run_async(
            commit_range,
            emit=tracked_emit,
            draft_type=draft_type,
            instruction=instruction,
            interactive=False,  # web UI doesn't do interactive approval
        )
        await emit(job_id, {"type": "agent_done", "agent": "DecisionMaker"})
        
        # Build response
        report_dict = {
            "analysis": {
                "issues": report.analysis.issues,
                "improvements": report.analysis.improvements,
                "summary": report.analysis.summary,
            },
            "categorization": {
                "change_type": report.categorization.change_type,
                "reasoning": report.categorization.reasoning,
            },
            "risk": {
                "risk_level": report.risk.risk_level,
                "reasoning": report.risk.reasoning,
            },
            "decision": {
                "action": report.decision.action,
                "reasoning": report.decision.reasoning,
            },
            "approval_status": report.approval_status,
        }

        if report.issue_draft:
            report_dict["issue_draft"] = {
                "title": report.issue_draft.title,
                "problem_description": report.issue_draft.problem_description,
                "evidence": report.issue_draft.evidence,
                "acceptance_criteria": report.issue_draft.acceptance_criteria,
                "risk_level": report.issue_draft.risk_level,
                "source": report.issue_draft.source,
            }

        if report.pr_draft:
            report_dict["pr_draft"] = {
                "title": report.pr_draft.title,
                "summary": report.pr_draft.summary,
                "files_affected": report.pr_draft.files_affected,
                "behavior_change": report.pr_draft.behavior_change,
                "test_plan": report.pr_draft.test_plan,
                "risk_level": report.pr_draft.risk_level,
                "source": report.pr_draft.source,
            }

        await emit(job_id, {"type": "done", "report": report_dict})
    except Exception as exc:
        await emit(job_id, {"type": "error", "message": str(exc)})


async def _run_improvement(
    job_id: str,
    issue_id: Optional[str],
    pr_id: Optional[str],
) -> None:
    loop = asyncio.get_event_loop()
    current_agent_state: dict = {"current": None}

    def tracked_emit(agent: str, message: str) -> None:
        agent_order = ["Reviewer", "Planner", "Improver", "Gatekeeper", "Orchestrator"]
        if agent != current_agent_state["current"] and agent in agent_order:
            asyncio.run_coroutine_threadsafe(
                emit(job_id, {"type": "agent_start", "agent": agent}),
                loop,
            )
            current_agent_state["current"] = agent

        asyncio.run_coroutine_threadsafe(
            emit(job_id, {
                "type": "log",
                "agent": agent,
                "message": message,
                "is_tool": False,
            }),
            loop,
        )

    try:
        orchestrator = ImprovementOrchestrator()
        
        if issue_id:
            report = await orchestrator.improve_issue_async(issue_id, emit=tracked_emit, interactive=False)
        else:
            report = await orchestrator.improve_pr_async(pr_id, emit=tracked_emit, interactive=False)

        # Build response
        report_dict = {
            "approval_status": report.approval_status,
        }

        if report.critique:
            report_dict["critique"] = {
                "overall_quality": report.critique.overall_quality,
                "summary": report.critique.summary,
                "critiques": [
                    {
                        "category": c.category,
                        "severity": c.severity,
                        "finding": c.finding,
                    }
                    for c in report.critique.critiques
                ],
            }

        if report.plan:
            report_dict["plan"] = {
                "planning_rationale": report.plan.planning_rationale,
                "prioritized_improvements": report.plan.prioritized_improvements,
                "estimated_effort": report.plan.estimated_effort,
                "dependencies": report.plan.dependencies,
            }

        if report.improved_issue:
            report_dict["improved_issue"] = {
                "new_title": report.improved_issue.new_title,
                "new_description": report.improved_issue.new_description,
                "improved_acceptance_criteria": report.improved_issue.improved_acceptance_criteria,
                "risk_level": report.improved_issue.risk_level,
                "evidence": report.improved_issue.clear_evidence,
                "policy_compliance": report.improved_issue.policy_compliance,
            }

        if report.improved_pr:
            report_dict["improved_pr"] = {
                "new_title": report.improved_pr.new_title,
                "new_description": report.improved_pr.new_description,
                "improved_behavior_change": report.improved_pr.improved_behavior_change,
                "improved_test_plan": report.improved_pr.improved_test_plan,
                "risk_level": report.improved_pr.risk_level,
                "breaking_changes_documented": report.improved_pr.breaking_changes_documented,
            }

        await emit(job_id, {"type": "done", "report": report_dict})
    except Exception as exc:
        await emit(job_id, {"type": "error", "message": str(exc)})


# ── GET /api/stream/{job_id} ───────────────────────────────────

@router.get("/stream/{job_id}")
async def stream(job_id: str):
    return StreamingResponse(
        _event_generator(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


async def _event_generator(job_id: str) -> AsyncGenerator[str, None]:
    q = get_queue(job_id)
    if q is None:
        yield f"data: {json.dumps({'type': 'error', 'message': 'Job not found'})}\n\n"
        return
    while True:
        try:
            event = await asyncio.wait_for(q.get(), timeout=180.0)
        except asyncio.TimeoutError:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Timeout'})}\n\n"
            break
        yield f"data: {json.dumps(event)}\n\n"
        if event.get("type") in ("done", "error"):
            remove_job(job_id)
            break