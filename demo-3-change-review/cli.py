"""
Change Review CLI

Usage:
  python cli.py review                # review current branch changes
  python cli.py review --range HEAD~1..HEAD  # review specific range
"""
import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from approval_orchestrator import ApprovalOrchestrator
from improve_orchestrator import ImprovementOrchestrator
from models.schemas import FinalReport
from orchestrator import Orchestrator

console = Console()

AGENT_COLORS = {
    "Analyzer": "blue",
    "Categorizer": "purple",
    "RiskAssessor": "green",
    "DecisionMaker": "yellow",
    "Orchestrator": "white",
}

AGENT_ICONS = {
    "Analyzer": "◎",
    "Categorizer": "◎",
    "RiskAssessor": "◎",
    "DecisionMaker": "◎",
    "Orchestrator": "·",
}

# Tracks which agent is currently active
_current_agent: dict = {"name": None}


def _emit(agent: str, message: str) -> None:
    color = AGENT_COLORS.get(agent, "white")

    # Print a section header rule when a new pipeline agent starts
    if agent in ("Analyzer", "Categorizer", "RiskAssessor", "DecisionMaker"):
        if agent != _current_agent["name"]:
            _current_agent["name"] = agent
            console.print()
            console.rule(
                f"[bold {color}] {agent} [/]",
                style=color,
                align="left",
            )
            console.print()

    if agent == "Orchestrator":
        console.print(f"  [dim]{message}[/]")
    else:
        console.print(f"  [{color}]▸[/] {message}")


@click.group()
def cli():
    """Change Review — LLM Agent Orchestration Demo"""


@cli.command()
@click.option(
    "--range", "commit_range",
    help="Commit range for diff, e.g., HEAD~1..HEAD. If not provided, uses current branch changes.",
)
@click.option(
    "--draft", type=click.Choice(["issue", "pr"]),
    help="Draft an issue or PR after analysis.",
)
@click.option(
    "--instruction", type=str,
    help="Explicit instruction for PR drafting, e.g., 'Create a PR to refactor duplicated pricing logic.'",
)
@click.option(
    "--output", type=click.Choice(["rich", "json"]), default="rich",
    help="Output format.",
)
def review(commit_range: str, draft: str, instruction: str, output: str) -> None:
    """Run the change review pipeline and optionally draft issues/PRs."""
    _current_agent["name"] = None  # reset between runs

    console.print()
    console.print(
        Panel.fit(
            "[bold white]Change Review[/]\n"
            "[dim]LLM Agent Orchestration Demo — CS 5001[/]",
            border_style="bright_blue",
        )
    )
    console.print()

    range_label = commit_range or "current branch changes"
    console.print(f"  Range:  [bold]{range_label}[/]")
    if draft:
        console.print(f"  Draft:  [bold cyan]{draft.upper()}[/]")
    if instruction:
        console.print(f"  Instruction: [bold]{instruction[:50]}...[/]")
    console.print(f"  Model:  [dim]llama3.2:3b via Ollama[/]")
    console.print()
    console.rule("Pipeline", style="dim")

    try:
        report = Orchestrator().run(
            commit_range,
            emit=_emit,
            draft_type=draft,
            instruction=instruction,
            interactive=False,  # Changed: don't prompt interactively, save drafts instead
        )
    except RuntimeError as exc:
        console.print(f"\n[bold red]Error:[/] {exc}")
        sys.exit(1)

    console.print()
    console.print()
    console.rule("Report", style="bright_blue")
    console.print()

    if output == "json":
        import json
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
        console.print_json(json.dumps(report_dict, indent=2))
    else:
        _print_report(report)


def _print_report(report: FinalReport) -> None:
    console.print(
        Panel(
            f"[bold]Summary:[/] {report.analysis.summary}",
            title="[bold]Analysis[/]",
            border_style="blue",
        )
    )
    console.print()

    if report.analysis.issues:
        console.print("[bold red]Issues[/]")
        for issue in report.analysis.issues:
            console.print(f"  [red]●[/] {issue}")
        console.print()

    if report.analysis.improvements:
        console.print("[bold green]Improvements[/]")
        for imp in report.analysis.improvements:
            console.print(f"  [green]●[/] {imp}")
        console.print()

    console.print(
        Panel(
            f"[bold]Type:[/] {report.categorization.change_type}\n"
            f"[bold]Reasoning:[/] {report.categorization.reasoning}",
            title="[bold]Categorization[/]",
            border_style="purple",
        )
    )
    console.print()

    risk_color = {"low": "green", "medium": "yellow", "high": "red"}.get(report.risk.risk_level, "white")
    console.print(
        Panel(
            f"[{risk_color}]{report.risk.risk_level.upper()}[/]\n\n{report.risk.reasoning}",
            title="[bold]Risk Assessment[/]",
            border_style=risk_color,
        )
    )
    console.print()

    console.print(
        Panel(
            f"[bold]{report.decision.action}[/]\n\n{report.decision.reasoning}",
            title="[bold]Decision[/]",
            border_style="yellow",
        )
    )
    console.print()

    # Show draft if present
    if report.issue_draft:
        approve_color = "green" if report.approval_status == "approved" else "red" if report.approval_status == "rejected" else "yellow"
        console.print(
            Panel(
                f"[bold]Title:[/] {report.issue_draft.title}\n\n"
                f"[bold]Problem:[/]\n{report.issue_draft.problem_description}\n\n"
                f"[bold]Evidence:[/]\n{report.issue_draft.evidence}\n\n"
                f"[bold]Acceptance Criteria:[/]\n"
                + "\n".join(f"  • {c}" for c in report.issue_draft.acceptance_criteria) + f"\n\n"
                f"[bold]Risk Level:[/] {report.issue_draft.risk_level}\n\n"
                f"[{approve_color}][bold]Status:[/] {report.approval_status.upper()}[/]",
                title="[bold yellow]Issue Draft[/]",
                border_style="yellow",
            )
        )
        console.print()

    if report.pr_draft:
        approve_color = "green" if report.approval_status == "approved" else "red" if report.approval_status == "rejected" else "yellow"
        console.print(
            Panel(
                f"[bold]Title:[/] {report.pr_draft.title}\n\n"
                f"[bold]Summary:[/]\n{report.pr_draft.summary}\n\n"
                f"[bold]Files Affected:[/]\n"
                + "\n".join(f"  • {f}" for f in report.pr_draft.files_affected) + f"\n\n"
                f"[bold]Behavior Change:[/]\n{report.pr_draft.behavior_change}\n\n"
                f"[bold]Test Plan:[/]\n{report.pr_draft.test_plan}\n\n"
                f"[bold]Risk Level:[/] {report.pr_draft.risk_level}\n\n"
                f"[{approve_color}][bold]Status:[/] {report.approval_status.upper()}[/]",
                title="[bold cyan]PR Draft[/]",
                border_style="cyan",
            )
        )
        console.print()


# ── improve command ────────────────────────────────────────────

@cli.command()
@click.option(
    "--issue", type=str,
    help="Issue ID to improve (e.g., 'test-issue-1' for demo).",
)
@click.option(
    "--pr", type=str,
    help="PR ID to improve (e.g., 'test-pr-1' for demo).",
)
@click.option(
    "--output", type=click.Choice(["rich", "json"]), default="rich",
    help="Output format.",
)
def improve(issue: Optional[str], pr: Optional[str], output: str) -> None:
    """Improve an existing GitHub issue or PR."""
    if not issue and not pr:
        console.print("[bold red]Error:[/] Provide either --issue or --pr")
        sys.exit(1)

    if issue and pr:
        console.print("[bold red]Error:[/] Provide only one of --issue or --pr")
        sys.exit(1)

    console.print()
    console.print(
        Panel.fit(
            "[bold white]Improvement Analysis[/]\n"
            "[dim]Multi-agent critique & improvement pipeline[/]",
            border_style="bright_blue",
        )
    )
    console.print()

    target_label = f"Issue #{issue}" if issue else f"PR #{pr}"
    console.print(f"  Target: [bold]{target_label}[/]")
    console.print(f"  Model:  [dim]llama3.2:3b via Ollama[/]")
    console.print()
    console.rule("Pipeline", style="dim")

    try:
        orchestrator = ImprovementOrchestrator()
        
        if issue:
            report = orchestrator.improve_issue(issue, emit=_emit_improvement, interactive=True)
        else:
            report = orchestrator.improve_pr(pr, emit=_emit_improvement, interactive=True)
    except RuntimeError as exc:
        console.print(f"\n[bold red]Error:[/] {exc}")
        sys.exit(1)
    except ValueError as exc:
        console.print(f"\n[bold red]Error:[/] {exc}")
        sys.exit(1)

    console.print()
    console.print()
    console.rule("Report", style="bright_blue")
    console.print()

    if output == "json":
        import json
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
        console.print_json(json.dumps(report_dict, indent=2))
    else:
        _print_improvement_report(report)


def _print_improvement_report(report) -> None:
    """Print improvement report with Rich formatting."""
    if report.critique:
        quality = report.critique.overall_quality
        quality_color = "green" if quality >= 70 else "yellow" if quality >= 50 else "red"
        
        console.print(
            Panel(
                f"[{quality_color}]Quality Score: {quality}/100[/]\n\n[bold]Summary:[/] {report.critique.summary}",
                title="[bold]Critique[/]",
                border_style="red",
            )
        )
        console.print()

        if report.critique.critiques:
            console.print("[bold red]Issues Found:[/]")
            for item in report.critique.critiques:
                severity_color = {"high": "bright_red", "medium": "yellow", "low": "dim"}.get(
                    item.severity, "white"
                )
                console.print(
                    f"  [{severity_color}][{item.severity}][/] {item.category}: {item.finding}"
                )
            console.print()

    if report.plan:
        console.print(
            Panel(
                f"[bold]Rationale:[/] {report.plan.planning_rationale}\n\n"
                f"[bold]Prioritized Improvements:[/]\n"
                + "\n".join(f"  • {imp}" for imp in report.plan.prioritized_improvements)
                + f"\n\n[bold]Estimated Effort:[/] {report.plan.estimated_effort}",
                title="[bold]Improvement Plan[/]",
                border_style="blue",
            )
        )
        console.print()

    if report.improved_issue:
        approve_color = (
            "green"
            if report.approval_status == "approved"
            else "red"
            if report.approval_status == "rejected"
            else "yellow"
        )
        console.print(
            Panel(
                f"[bold]Title:[/] {report.improved_issue.new_title}\n\n"
                f"[bold]Description:[/]\n{report.improved_issue.new_description}\n\n"
                f"[bold]Acceptance Criteria:[/]\n"
                + "\n".join(f"  • {c}" for c in report.improved_issue.improved_acceptance_criteria)
                + f"\n\n"
                f"[bold]Evidence:[/]\n{report.improved_issue.clear_evidence}\n\n"
                f"[bold]Risk Level:[/] {report.improved_issue.risk_level}\n\n"
                f"[bold]Policy Compliance:[/] {report.improved_issue.policy_compliance}\n\n"
                f"[{approve_color}][bold]Status:[/] {report.approval_status.upper()}[/]",
                title="[bold cyan]Improved Issue[/]",
                border_style="cyan",
            )
        )
        console.print()

    if report.improved_pr:
        approve_color = (
            "green"
            if report.approval_status == "approved"
            else "red"
            if report.approval_status == "rejected"
            else "yellow"
        )
        console.print(
            Panel(
                f"[bold]Title:[/] {report.improved_pr.new_title}\n\n"
                f"[bold]Description:[/]\n{report.improved_pr.new_description}\n\n"
                f"[bold]Behavior Change:[/]\n{report.improved_pr.improved_behavior_change}\n\n"
                f"[bold]Test Plan:[/]\n{report.improved_pr.improved_test_plan}\n\n"
                f"[bold]Risk Level:[/] {report.improved_pr.risk_level}\n\n"
                f"[bold]Breaking Changes Documented:[/] {report.improved_pr.breaking_changes_documented}\n\n"
                f"[{approve_color}][bold]Status:[/] {report.approval_status.upper()}[/]",
                title="[bold cyan]Improved PR[/]",
                border_style="cyan",
            )
        )
        console.print()


# ── draft command ────────────────────────────────────────────

@cli.command()
@click.argument("item_type", type=click.Choice(["issue", "pr"]))
@click.option(
    "--instruction", required=True,
    help="Instruction for drafting the issue or PR",
)
def draft(item_type: str, instruction: str) -> None:
    """Draft an issue or PR from explicit instruction."""
    _current_agent["name"] = None  # reset between runs

    console.print()
    console.print(
        Panel.fit(
            "[bold white]Draft Creation[/]\n"
            "[dim]Creating draft from instruction[/]",
            border_style="bright_blue",
        )
    )
    console.print()

    console.print(f"  Type:  [bold]{item_type.upper()}[/]")
    console.print(f"  Instruction: [bold]{instruction[:50]}...[/]")
    console.print(f"  Model:  [dim]llama3.2:3b via Ollama[/]")
    console.print()
    console.rule("Pipeline", style="dim")

    try:
        report = Orchestrator().run(
            commit_range=None,  # No git analysis for instruction-based drafts
            emit=_emit,
            draft_type=item_type,
            instruction=instruction,
            interactive=False,
        )
    except RuntimeError as exc:
        console.print(f"\n[bold red]Error:[/] {exc}")
        sys.exit(1)

    console.print()
    console.print()
    console.rule("Draft Created", style="bright_blue")
    console.print()

    if report.issue_draft:
        console.print(
            Panel(
                f"[bold]Title:[/] {report.issue_draft.title}\n\n"
                f"[bold]Problem:[/]\n{report.issue_draft.problem_description}\n\n"
                f"[bold]Evidence:[/]\n{report.issue_draft.evidence}\n\n"
                f"[bold]Acceptance Criteria:[/]\n"
                + "\n".join(f"  • {c}" for c in report.issue_draft.acceptance_criteria) + f"\n\n"
                f"[bold]Risk Level:[/] {report.issue_draft.risk_level}\n\n"
                f"[yellow]Draft saved. Use 'agent approve <id>' to review and create.[/]",
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
                f"[bold]Risk Level:[/] {report.pr_draft.risk_level}\n\n"
                f"[yellow]Draft saved. Use 'agent approve <id>' to review and create.[/]",
                title="[bold cyan]PR Draft[/]",
                border_style="cyan",
            )
        )

    console.print()


# ── approve command ────────────────────────────────────────────

@cli.command()
@click.argument("draft_id", required=False)
@click.option("--yes", "approve", flag_value=True, help="Approve the draft")
@click.option("--no", "approve", flag_value=False, help="Reject the draft")
@click.option("--list", "list_drafts", is_flag=True, help="List all pending drafts")
def approve(draft_id: str, approve: bool, list_drafts: bool) -> None:
    """Approve or reject a draft, or list pending drafts."""
    if list_drafts:
        ApprovalOrchestrator.list_pending_drafts()
        return

    if not draft_id:
        console.print("[bold red]Error:[/] Provide a draft ID or use --list")
        console.print("Usage: agent approve <draft_id> --yes|--no")
        console.print("       agent approve --list")
        sys.exit(1)

    if approve is None:
        # Just show the draft
        ApprovalOrchestrator.show_draft(draft_id)
        return

    # Approve or reject
    report = ApprovalOrchestrator.approve_draft(draft_id, approve)
    if report:
        console.print(f"[bold green]Draft {draft_id} processed successfully.[/]")
    else:
        sys.exit(1)


def _emit_improvement(agent: str, message: str) -> None:
    """Emit callback for improvement pipeline."""
    agent_colors = {
        "Reviewer": "red",
        "Planner": "blue",
        "Improver": "green",
        "Gatekeeper": "yellow",
        "Orchestrator": "white",
    }
    color = agent_colors.get(agent, "white")
    console.print(f"  [{color}]▸[/] {agent}: {message}")


if __name__ == "__main__":
    cli()