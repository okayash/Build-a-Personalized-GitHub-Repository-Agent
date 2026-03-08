"""
Draft storage — temporarily store drafts for later approval and creation.
"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from models.schemas import IssueDraft, PRDraft, FinalReport

DRAFTS_DIR = Path(__file__).parent / "drafts"
DRAFTS_DIR.mkdir(exist_ok=True)


class DraftStorage:
    """Manages temporary storage of drafts pending approval."""

    @staticmethod
    def save_draft(draft_id: str, report: FinalReport) -> str:
        """
        Save a draft report for later approval.

        Args:
            draft_id: Unique identifier for the draft
            report: The final report with drafts

        Returns:
            Path to the saved draft file
        """
        draft_file = DRAFTS_DIR / f"{draft_id}.json"

        # Convert dataclasses to dicts for JSON serialization
        draft_data = {
            "draft_id": draft_id,
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
            draft_data["issue_draft"] = {
                "title": report.issue_draft.title,
                "problem_description": report.issue_draft.problem_description,
                "evidence": report.issue_draft.evidence,
                "acceptance_criteria": report.issue_draft.acceptance_criteria,
                "risk_level": report.issue_draft.risk_level,
                "source": report.issue_draft.source,
                "instruction": report.issue_draft.instruction,
            }

        if report.pr_draft:
            draft_data["pr_draft"] = {
                "title": report.pr_draft.title,
                "summary": report.pr_draft.summary,
                "files_affected": report.pr_draft.files_affected,
                "behavior_change": report.pr_draft.behavior_change,
                "test_plan": report.pr_draft.test_plan,
                "risk_level": report.pr_draft.risk_level,
                "source": report.pr_draft.source,
                "instruction": report.pr_draft.instruction,
            }

        with open(draft_file, 'w') as f:
            json.dump(draft_data, f, indent=2)

        return str(draft_file)

    @staticmethod
    def load_draft(draft_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a saved draft.

        Args:
            draft_id: The draft identifier

        Returns:
            Draft data dict or None if not found
        """
        draft_file = DRAFTS_DIR / f"{draft_id}.json"
        if not draft_file.exists():
            return None

        with open(draft_file, 'r') as f:
            return json.load(f)

    @staticmethod
    def list_drafts() -> list[str]:
        """List all saved draft IDs."""
        return [f.stem for f in DRAFTS_DIR.glob("*.json")]

    @staticmethod
    def delete_draft(draft_id: str) -> bool:
        """
        Delete a saved draft.

        Args:
            draft_id: The draft identifier

        Returns:
            True if deleted, False if not found
        """
        draft_file = DRAFTS_DIR / f"{draft_id}.json"
        if draft_file.exists():
            draft_file.unlink()
            return True
        return False