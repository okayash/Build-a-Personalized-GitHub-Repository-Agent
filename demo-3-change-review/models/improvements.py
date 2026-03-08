"""
Data models for issue/PR improvement — critiques, plans, and improvements.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CritiqueItem:
    """A single critique point."""
    category: str  # "unclear", "vague", "missing_info", "policy", "evidence"
    severity: str  # "low", "medium", "high"
    finding: str
    line_reference: Optional[int] = None


@dataclass
class IssueCritique:
    """Critique of an existing GitHub issue."""
    issue_id: str
    title: str
    current_body: str
    critiques: List[CritiqueItem]
    overall_quality: int  # 0-100
    summary: str


@dataclass
class PRCritique:
    """Critique of an existing GitHub PR."""
    pr_id: str
    title: str
    current_body: str
    branch: str
    critiques: List[CritiqueItem]
    overall_quality: int  # 0-100
    summary: str


@dataclass
class ImprovementPlan:
    """Structured plan for improving an issue or PR."""
    target_type: str  # "issue" or "pr"
    target_id: str
    planning_rationale: str
    prioritized_improvements: List[str]  # ordered by importance
    estimated_effort: str  # "low", "medium", "high"
    dependencies: List[str]  # other issues/PRs to reference


@dataclass
class ImprovedIssue:
    """Improved version of an issue."""
    original_id: str
    new_title: str
    new_description: str
    improved_acceptance_criteria: List[str]
    risk_level: str
    clear_evidence: str
    policy_compliance: str
    critique_summary: str


@dataclass
class ImprovedPR:
    """Improved version of a PR."""
    original_id: str
    new_title: str
    new_description: str
    improved_behavior_change: str
    improved_test_plan: str
    risk_level: str
    breaking_changes_documented: bool
    critique_summary: str


@dataclass
class ImprovementReport:
    """Final report on improvements to an issue or PR."""
    critique: Optional[IssueCritique] = None  # if issue
    plan: ImprovementPlan = None
    improved_issue: Optional[ImprovedIssue] = None
    improved_pr: Optional[ImprovedPR] = None
    approval_status: str = "pending"  # "pending", "approved", "rejected"