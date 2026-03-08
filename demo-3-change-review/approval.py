"""
Approval module — handles user approval of generated drafts.
"""
from models.schemas import IssueDraft, PRDraft


class ApprovalManager:
    """Manages approval workflows for drafts."""

    @staticmethod
    def prompt_approval_cli(
        issue_draft: IssueDraft = None,
        pr_draft: PRDraft = None,
    ) -> tuple[bool, str]:
        """
        Interactively prompt user for approval via CLI.

        Args:
            issue_draft: optional issue draft to approve
            pr_draft: optional PR draft to approve

        Returns:
            (approved: bool, notes: str)
        """
        from rich.console import Console
        from rich.panel import Panel

        console = Console()

        if issue_draft:
            console.print()
            console.print(
                Panel(
                    f"[bold]Title:[/] {issue_draft.title}\n\n"
                    f"[bold]Problem:[/]\n{issue_draft.problem_description}\n\n"
                    f"[bold]Evidence:[/]\n{issue_draft.evidence}\n\n"
                    f"[bold]Acceptance Criteria:[/]\n"
                    + "\n".join(f"  • {c}" for c in issue_draft.acceptance_criteria) + f"\n\n"
                    f"[bold]Risk Level:[/] {issue_draft.risk_level}",
                    title="[bold yellow]Issue Draft[/]",
                    border_style="yellow",
                )
            )

        if pr_draft:
            console.print()
            console.print(
                Panel(
                    f"[bold]Title:[/] {pr_draft.title}\n\n"
                    f"[bold]Summary:[/]\n{pr_draft.summary}\n\n"
                    f"[bold]Files Affected:[/]\n"
                    + "\n".join(f"  • {f}" for f in pr_draft.files_affected) + f"\n\n"
                    f"[bold]Behavior Change:[/]\n{pr_draft.behavior_change}\n\n"
                    f"[bold]Test Plan:[/]\n{pr_draft.test_plan}\n\n"
                    f"[bold]Risk Level:[/] {pr_draft.risk_level}",
                    title="[bold cyan]PR Draft[/]",
                    border_style="cyan",
                )
            )

        console.print()
        console.print("[bold]Review the draft above.[/]")
        console.print()
        response = input("[bold green]Approve? (y/n/notes):[/] ").strip().lower()

        if response == "y":
            return True, ""
        elif response == "n":
            return False, ""
        else:
            # Assume it's notes
            return None, response  # None means "ask again with notes"