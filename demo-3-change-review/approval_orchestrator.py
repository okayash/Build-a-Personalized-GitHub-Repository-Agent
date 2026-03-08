"""
Approval Orchestrator — handles approval and creation of GitHub issues/PRs.
"""
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel

from draft_storage import DraftStorage
from tools.gh_tools import create_github_issue, create_github_pr
from models.schemas import FinalReport, IssueDraft, PRDraft

console = Console()


class ApprovalOrchestrator:
    """Handles approval and creation of drafts."""

    @staticmethod
    def approve_draft(draft_id: str, yes: bool = True) -> Optional[FinalReport]:
        """
        Approve or reject a draft and create GitHub items if approved.

        Args:
            draft_id: The draft identifier
            yes: True to approve, False to reject

        Returns:
            Updated FinalReport or None if draft not found
        """
        draft_data = DraftStorage.load_draft(draft_id)
        if not draft_data:
            console.print(f"[bold red]Error:[/] Draft '{draft_id}' not found")
            return None

        # Reconstruct the report from stored data
        report = ApprovalOrchestrator._reconstruct_report(draft_data)

        if not yes:
            # Reject the draft
            report.approval_status = "rejected"
            DraftStorage.delete_draft(draft_id)
            console.print(f"[bold red]Draft {draft_id} rejected.[/] No changes made.")
            return report

        # Approve and create
        report.approval_status = "approved"

        # Create GitHub issue if present
        if report.issue_draft:
            console.print("[bold green]Creating GitHub issue...[/]")
            github_issue = create_github_issue(
                title=report.issue_draft.title,
                body=ApprovalOrchestrator._format_issue_body(report.issue_draft),
                labels=[f"risk:{report.issue_draft.risk_level}"]
            )
            if github_issue:
                report.github_issue = github_issue
                console.print(f"[bold green]✓ Issue created:[/] {github_issue['url']}")
            else:
                console.print("[bold red]✗ Failed to create GitHub issue[/]")
                report.approval_status = "failed"

        # Create GitHub PR if present
        if report.pr_draft:
            console.print("[bold green]Creating GitHub PR...[/]")
            # For PRs, we need a branch name. Use a default or extract from instruction
            branch_name = ApprovalOrchestrator._extract_branch_name(report.pr_draft)
            github_pr = create_github_pr(
                title=report.pr_draft.title,
                body=ApprovalOrchestrator._format_pr_body(report.pr_draft),
                head=branch_name,
                base="main",
                draft=True
            )
            if github_pr:
                report.github_pr = github_pr
                console.print(f"[bold green]✓ PR created:[/] {github_pr['url']}")
            else:
                console.print("[bold red]✗ Failed to create GitHub PR[/]")
                report.approval_status = "failed"

        # Clean up the draft
        DraftStorage.delete_draft(draft_id)

        return report

    @staticmethod
    def show_draft(draft_id: str) -> bool:
        """
        Display a draft for review.

        Args:
            draft_id: The draft identifier

        Returns:
            True if draft exists and was shown, False otherwise
        """
        draft_data = DraftStorage.load_draft(draft_id)
        if not draft_data:
            console.print(f"[bold red]Error:[/] Draft '{draft_id}' not found")
            return False

        report = ApprovalOrchestrator._reconstruct_report(draft_data)

        console.print()
        console.print(
            Panel.fit(
                "[bold white]Draft Review[/]\n"
                f"[dim]Draft ID: {draft_id}[/]",
                border_style="bright_blue",
            )
        )
        console.print()

        if report.issue_draft:
            console.print(
                Panel(
                    f"[bold]Title:[/] {report.issue_draft.title}\n\n"
                    f"[bold]Problem:[/]\n{report.issue_draft.problem_description}\n\n"
                    f"[bold]Evidence:[/]\n{report.issue_draft.evidence}\n\n"
                    f"[bold]Acceptance Criteria:[/]\n"
                    + "\n".join(f"  • {c}" for c in report.issue_draft.acceptance_criteria) + f"\n\n"
                    f"[bold]Risk Level:[/] {report.issue_draft.risk_level}",
                    title="[bold yellow]Issue Draft[/]",
                    border_style="yellow",
                )
            )

        if report.pr_draft:
            console.print(
                Panel(
                    f"[bold]Title:[/] {report.pr_draft.title}\n\n"
                    f"[bold]Summary:[/]\n{report.pr_draft.summary}\n\n"
                    f"[bold]Files Affected:[/]\n"
                    + "\n".join(f"  • {f}" for f in report.pr_draft.files_affected) + f"\n\n"
                    f"[bold]Behavior Change:[/]\n{report.pr_draft.behavior_change}\n\n"
                    f"[bold]Test Plan:[/]\n{report.pr_draft.test_plan}\n\n"
                    f"[bold]Risk Level:[/] {report.pr_draft.risk_level}",
                    title="[bold cyan]PR Draft[/]",
                    border_style="cyan",
                )
            )

        console.print()
        console.print("[bold]Use 'agent approve <id> --yes' to approve and create, or 'agent approve <id> --no' to reject.[/]")
        return True

    @staticmethod
    def list_pending_drafts():
        """List all pending drafts."""
        drafts = DraftStorage.list_drafts()
        if not drafts:
            console.print("[dim]No pending drafts.[/]")
            return

        console.print("[bold]Pending Drafts:[/]")
        for draft_id in drafts:
            draft_data = DraftStorage.load_draft(draft_id)
            if draft_data:
                draft_type = "Issue" if "issue_draft" in draft_data else "PR"
                title = ""
                if "issue_draft" in draft_data:
                    title = draft_data["issue_draft"]["title"]
                elif "pr_draft" in draft_data:
                    title = draft_data["pr_draft"]["title"]
                
                console.print(f"  [cyan]{draft_id}[/] - {draft_type}: {title[:50]}...")

    @staticmethod
    def _reconstruct_report(draft_data: Dict[str, Any]) -> FinalReport:
        """Reconstruct a FinalReport from stored draft data."""
        from models.schemas import AnalysisResult, CategorizationResult, RiskResult, DecisionResult

        analysis = AnalysisResult(**draft_data["analysis"])
        categorization = CategorizationResult(**draft_data["categorization"])
        risk = RiskResult(**draft_data["risk"])
        decision = DecisionResult(**draft_data["decision"])

        issue_draft = None
        if "issue_draft" in draft_data:
            issue_draft = IssueDraft(**draft_data["issue_draft"])

        pr_draft = None
        if "pr_draft" in draft_data:
            pr_draft = PRDraft(**draft_data["pr_draft"])

        return FinalReport(
            analysis=analysis,
            categorization=categorization,
            risk=risk,
            decision=decision,
            issue_draft=issue_draft,
            pr_draft=pr_draft,
            approval_status=draft_data.get("approval_status", "pending"),
        )

    @staticmethod
    def _format_issue_body(issue_draft: IssueDraft) -> str:
        """Format issue draft into GitHub issue body."""
        body = f"## Problem Description\n\n{issue_draft.problem_description}\n\n"
        body += f"## Evidence\n\n{issue_draft.evidence}\n\n"
        body += f"## Acceptance Criteria\n\n"
        for criteria in issue_draft.acceptance_criteria:
            body += f"- {criteria}\n"
        body += f"\n## Risk Level\n\n{issue_draft.risk_level}\n\n"
        body += f"---\n*Generated by AI agent*"
        return body

    @staticmethod
    def _format_pr_body(pr_draft: PRDraft) -> str:
        """Format PR draft into GitHub PR body."""
        body = f"## Summary\n\n{pr_draft.summary}\n\n"
        body += f"## Files Affected\n\n"
        for file in pr_draft.files_affected:
            body += f"- `{file}`\n"
        body += f"\n## Behavior Change\n\n{pr_draft.behavior_change}\n\n"
        body += f"## Test Plan\n\n{pr_draft.test_plan}\n\n"
        body += f"## Risk Level\n\n{pr_draft.risk_level}\n\n"
        body += f"---\n*Generated by AI agent*"
        return body

    @staticmethod
    def _extract_branch_name(pr_draft: PRDraft) -> str:
        """Extract or generate a branch name for PR."""
        # Try to extract from instruction if present
        if pr_draft.instruction:
            # Simple heuristic: look for branch-like patterns
            instruction_lower = pr_draft.instruction.lower()
            if "branch" in instruction_lower:
                # This is a simple extraction - could be improved
                words = pr_draft.instruction.split()
                for i, word in enumerate(words):
                    if word.lower() == "branch" and i + 1 < len(words):
                        return words[i + 1].strip(".,")

        # Default branch name based on title
        title_slug = pr_draft.title.lower().replace(" ", "-").replace(":", "").replace("?", "")
        return f"feature/{title_slug}"