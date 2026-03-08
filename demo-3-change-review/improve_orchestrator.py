"""
ImprovementOrchestrator — Runs the multi-agent improvement pipeline.

Multi-agent pattern:
  Reviewer (critique) → Planner (plan) → Improver (draft) → Gatekeeper (verify + approval)
"""
import asyncio
from typing import Callable, Optional

from agents.gatekeeper import GatekeeperAgent
from agents.improver import ImproverAgent
from agents.planner import PlannerAgent
from agents.reviewer import ReviewerAgent
from approval import ApprovalManager
from models.improvements import ImprovementReport
from tools.gh_tools import fetch_github_issue, fetch_github_pr


class ImprovementOrchestrator:
    """Orchestrates the multi-agent improvement pipeline."""

    def improve_issue(
        self,
        issue_id: str,
        emit: Optional[Callable[[str, str], None]] = None,
        interactive: bool = True,
    ) -> ImprovementReport:
        """
        Run the improvement pipeline for an issue.

        Pipeline: Reviewer → Planner → Improver → Gatekeeper → Approval

        Args:
            issue_id: GitHub issue ID or test issue ID (e.g., "test-issue-1")
            emit: optional callback(agent_name, message)
            interactive: if True, prompt for approval

        Returns:
            ImprovementReport
        """
        # Step 0: Fetch the issue
        issue_data = fetch_github_issue(issue_id)
        if not issue_data:
            raise ValueError(f"Issue {issue_id} not found")

        # Step 1: Reviewer - Critique
        reviewer = ReviewerAgent()
        critique = reviewer.critique_issue(
            issue_id=issue_data["id"],
            title=issue_data["title"],
            body=issue_data["body"],
            emit=emit,
        )

        # Step 2: Planner - Plan improvements
        planner = PlannerAgent()
        plan = planner.plan_issue_improvement(critique, emit)

        # Step 3: Improver - Draft improvements
        improver = ImproverAgent()
        improved = improver.improve_issue(critique, plan, emit)

        # Step 4: Gatekeeper - Verify
        gatekeeper = GatekeeperAgent()
        safe, verification_reason = gatekeeper.verify_issue_improvement(improved, emit)

        if not safe:
            if emit:
                emit("Orchestrator", f"Verification failed: {verification_reason}")
            return ImprovementReport(
                critique=critique,
                plan=plan,
                improved_issue=None,
                approval_status="rejected",
            )

        # Step 5: Human approval
        approval_status = "pending"
        if interactive:
            approved, _ = ApprovalManager.prompt_approval_cli(issue_draft=None)
            # Note: We're reusing the approval UI for issues
            if approved:
                approval_status = "approved"
            else:
                approval_status = "rejected"
        else:
            approval_status = "approved"

        return ImprovementReport(
            critique=critique,
            plan=plan,
            improved_issue=improved if approval_status == "approved" else None,
            approval_status=approval_status,
        )

    def improve_pr(
        self,
        pr_id: str,
        emit: Optional[Callable[[str, str], None]] = None,
        interactive: bool = True,
    ) -> ImprovementReport:
        """
        Run the improvement pipeline for a PR.

        Pipeline: Reviewer → Planner → Improver → Gatekeeper → Approval

        Args:
            pr_id: GitHub PR ID or test PR ID (e.g., "test-pr-1")
            emit: optional callback(agent_name, message)
            interactive: if True, prompt for approval

        Returns:
            ImprovementReport
        """
        # Step 0: Fetch the PR
        pr_data = fetch_github_pr(pr_id)
        if not pr_data:
            raise ValueError(f"PR {pr_id} not found")

        # Step 1: Reviewer - Critique
        reviewer = ReviewerAgent()
        critique = reviewer.critique_pr(
            pr_id=pr_data["id"],
            title=pr_data["title"],
            body=pr_data["body"],
            branch=pr_data["branch"],
            emit=emit,
        )

        # Step 2: Planner - Plan improvements
        planner = PlannerAgent()
        plan = planner.plan_pr_improvement(critique, emit)

        # Step 3: Improver - Draft improvements
        improver = ImproverAgent()
        improved = improver.improve_pr(critique, plan, emit)

        # Step 4: Gatekeeper - Verify
        gatekeeper = GatekeeperAgent()
        safe, verification_reason = gatekeeper.verify_pr_improvement(improved, emit)

        if not safe:
            if emit:
                emit("Orchestrator", f"Verification failed: {verification_reason}")
            return ImprovementReport(
                critique=critique,
                plan=plan,
                improved_pr=None,
                approval_status="rejected",
            )

        # Step 5: Human approval
        approval_status = "pending"
        if interactive:
            approved, _ = ApprovalManager.prompt_approval_cli(pr_draft=None)
            # Note: We're reusing the approval UI for PRs
            if approved:
                approval_status = "approved"
            else:
                approval_status = "rejected"
        else:
            approval_status = "approved"

        return ImprovementReport(
            critique=critique,
            plan=plan,
            improved_pr=improved if approval_status == "approved" else None,
            approval_status=approval_status,
        )

    async def improve_issue_async(
        self,
        issue_id: str,
        emit: Optional[Callable[[str, str], None]] = None,
        interactive: bool = False,
    ) -> ImprovementReport:
        """Async version for web UI."""
        loop = asyncio.get_event_loop()

        def sync_run():
            return self.improve_issue(issue_id, emit, interactive)

        return await loop.run_in_executor(None, sync_run)

    async def improve_pr_async(
        self,
        pr_id: str,
        emit: Optional[Callable[[str, str], None]] = None,
        interactive: bool = False,
    ) -> ImprovementReport:
        """Async version for web UI."""
        loop = asyncio.get_event_loop()

        def sync_run():
            return self.improve_pr(pr_id, emit, interactive)

        return await loop.run_in_executor(None, sync_run)