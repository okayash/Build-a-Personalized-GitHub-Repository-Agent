"""
Orchestrator — manages the 5-stage change review pipeline with optional drafting.

Sequential mode:
  Analyzer → Categorizer → RiskAssessor → DecisionMaker → Draft (optional)
"""
import asyncio
from typing import Callable, Optional, Tuple
import uuid

import config
from agents.analyzer import AnalyzerAgent
from agents.categorizer import CategorizerAgent
from agents.decision_maker import DecisionMakerAgent
from agents.issue_drafter import IssueDraftAgent
from agents.pr_drafter import PRDraftAgent
from agents.risk_assessor import RiskAssessorAgent
from approval import ApprovalManager
from draft_storage import DraftStorage
from models.schemas import (
    AnalysisResult,
    CategorizationResult,
    DecisionResult,
    FinalReport,
    IssueDraft,
    PRDraft,
    RiskResult,
)


class Orchestrator:
    """Runs the change review pipeline."""

    def run(
        self,
        commit_range: Optional[str] = None,
        emit: Optional[Callable[[str, str], None]] = None,
        draft_type: Optional[str] = None,  # "issue", "pr", or None
        instruction: Optional[str] = None,  # for explicit instruction drafting
        interactive: bool = True,  # show approval prompts
    ) -> FinalReport:
        """
        Run the pipeline synchronously.

        Args:
            commit_range: optional commit range for diff
            emit: optional callback(agent_name, message)
            draft_type: "issue", "pr", or None
            instruction: optional explicit instruction for drafting
            interactive: if True, prompt for approval; if False, auto-approve

        Returns:
            FinalReport
        """
        # For instruction-based drafts, skip git analysis
        if instruction and not commit_range:
            return self._run_instruction_draft(draft_type, instruction, emit)

        analyzer = AnalyzerAgent()
        categorizer = CategorizerAgent()
        risk_assessor = RiskAssessorAgent()
        decision_maker = DecisionMakerAgent()

        # Step 1: Analyze
        analysis = analyzer.analyze(commit_range, emit)

        # Step 2: Categorize
        categorization = categorizer.categorize(analysis, emit)

        # Step 3: Assess risk
        risk = risk_assessor.assess_risk(analysis, emit)

        # Step 4: Decide
        decision = decision_maker.decide(analysis, categorization, risk, emit)

        # Step 5: Optionally draft issue or PR
        issue_draft = None
        pr_draft = None
        approval_status = "pending"
        draft_id = None

        if draft_type == "issue":
            if emit:
                emit("Orchestrator", "Drafting issue...")
            issue_drafter = IssueDraftAgent()
            issue_draft = issue_drafter.draft_from_review(analysis, categorization, risk, emit)
            
            # Save draft for later approval
            draft_id = str(uuid.uuid4())[:8]
            report = FinalReport(
                analysis=analysis,
                categorization=categorization,
                risk=risk,
                decision=decision,
                issue_draft=issue_draft,
                pr_draft=None,
                approval_status="pending",
            )
            DraftStorage.save_draft(draft_id, report)
            
            if emit:
                emit("Orchestrator", f"Draft saved with ID: {draft_id}")
                emit("Orchestrator", "Use 'agent approve <id>' to approve and create")

        elif draft_type == "pr":
            if emit:
                emit("Orchestrator", "Drafting PR...")
            pr_drafter = PRDraftAgent()
            if instruction:
                pr_draft = pr_drafter.draft_from_instruction(instruction, emit)
            else:
                pr_draft = pr_drafter.draft_from_review(analysis, categorization, risk, emit)
            
            # Save draft for later approval
            draft_id = str(uuid.uuid4())[:8]
            report = FinalReport(
                analysis=analysis,
                categorization=categorization,
                risk=risk,
                decision=decision,
                issue_draft=None,
                pr_draft=pr_draft,
                approval_status="pending",
            )
            DraftStorage.save_draft(draft_id, report)
            
            if emit:
                emit("Orchestrator", f"Draft saved with ID: {draft_id}")
                emit("Orchestrator", "Use 'agent approve <id>' to approve and create")

        return FinalReport(
            analysis=analysis,
            categorization=categorization,
            risk=risk,
            decision=decision,
            issue_draft=issue_draft,
            pr_draft=pr_draft,
            approval_status=approval_status,
        )

    async def run_async(
        self,
        commit_range: Optional[str] = None,
        emit: Optional[Callable[[str, str], None]] = None,
        draft_type: Optional[str] = None,
        instruction: Optional[str] = None,
        interactive: bool = False,  # web UI typically doesn't do interactive prompts
    ) -> FinalReport:
        """
        Run the pipeline asynchronously (for web UI).

        Args:
            commit_range: optional commit range for diff
            emit: optional callback
            draft_type: "issue", "pr", or None
            instruction: optional explicit instruction for drafting
            interactive: if True, prompt for approval; if False, auto-approve

        Returns:
            FinalReport
        """
        loop = asyncio.get_event_loop()

        def sync_run():
            return self.run(commit_range, emit, draft_type, instruction, interactive)

        return await loop.run_in_executor(None, sync_run)

    def _run_instruction_draft(
        self,
        draft_type: str,
        instruction: str,
        emit: Optional[Callable[[str, str], None]] = None,
    ) -> FinalReport:
        """
        Run drafting pipeline for instruction-based drafts (no git analysis).

        Args:
            draft_type: "issue" or "pr"
            instruction: The drafting instruction
            emit: optional callback

        Returns:
            FinalReport with draft
        """
        # Create empty analysis results for instruction-based drafts
        from models.schemas import AnalysisResult, CategorizationResult, RiskResult, DecisionResult

        analysis = AnalysisResult(
            issues=[],
            improvements=[],
            summary=f"Instruction-based {draft_type} draft: {instruction[:50]}..."
        )
        categorization = CategorizationResult(
            change_type="instruction",
            reasoning="Draft created from explicit instruction, no code changes analyzed"
        )
        risk = RiskResult(
            risk_level="medium",
            reasoning="Risk assessment not performed for instruction-based drafts"
        )
        decision = DecisionResult(
            action=f"Create {draft_type.upper()}",
            reasoning=f"User requested {draft_type} creation via instruction"
        )

        issue_draft = None
        pr_draft = None

        if draft_type == "issue":
            if emit:
                emit("Orchestrator", "Drafting issue from instruction...")
            issue_drafter = IssueDraftAgent()
            issue_draft = issue_drafter.draft_from_instruction(instruction, emit)

        elif draft_type == "pr":
            if emit:
                emit("Orchestrator", "Drafting PR from instruction...")
            pr_drafter = PRDraftAgent()
            pr_draft = pr_drafter.draft_from_instruction(instruction, emit)

        # Save draft for later approval
        draft_id = str(uuid.uuid4())[:8]
        report = FinalReport(
            analysis=analysis,
            categorization=categorization,
            risk=risk,
            decision=decision,
            issue_draft=issue_draft,
            pr_draft=pr_draft,
            approval_status="pending",
        )
        DraftStorage.save_draft(draft_id, report)

        if emit:
            emit("Orchestrator", f"Draft saved with ID: {draft_id}")
            emit("Orchestrator", "Use 'agent approve <id>' to approve and create")

        return report