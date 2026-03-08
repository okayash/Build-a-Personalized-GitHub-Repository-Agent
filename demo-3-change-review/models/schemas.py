"""
Data models for agent results — typed dataclasses passed between pipeline stages.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AnalysisResult:
    """Result from analyzing the git diff."""
    issues: List[str]
    improvements: List[str]
    summary: str


@dataclass
class CategorizationResult:
    """Categorization of the change."""
    change_type: str  # e.g., "feature", "bugfix", "refactor", etc.
    reasoning: str


@dataclass
class RiskResult:
    """Risk assessment."""
    risk_level: str  # "low", "medium", "high"
    reasoning: str


@dataclass
class DecisionResult:
    """Decision on action."""
    action: str  # "Create Issue", "Create PR", "No action required"
    reasoning: str


@dataclass
class IssueDraft:
    """Draft for a GitHub issue."""
    title: str
    problem_description: str
    evidence: str  # code snippet or reference
    acceptance_criteria: List[str]
    risk_level: str
    source: str  # "review" or "instruction"
    instruction: Optional[str] = None  # if source == "instruction"


@dataclass
class PRDraft:
    """Draft for a GitHub pull request."""
    title: str
    summary: str
    files_affected: List[str]
    behavior_change: str
    test_plan: str
    risk_level: str
    source: str  # "review" or "instruction"
    instruction: Optional[str] = None  # if source == "instruction"


@dataclass
class FinalReport:
    """Combined final report."""
    analysis: AnalysisResult
    categorization: CategorizationResult
    risk: RiskResult
    decision: DecisionResult
    issue_draft: Optional[IssueDraft] = None
    pr_draft: Optional[PRDraft] = None
    approval_status: str = "pending"  # "pending", "approved", "rejected"
    github_issue: Optional[dict] = None  # created GitHub issue details
    github_pr: Optional[dict] = None  # created GitHub PR details