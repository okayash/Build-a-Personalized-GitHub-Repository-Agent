"""
PRDraftAgent — Drafts GitHub pull requests based on review findings or instructions.
"""
from typing import Callable, Optional

from agents.base import BaseAgent
from models.schemas import (
    AnalysisResult,
    CategorizationResult,
    PRDraft,
    RiskResult,
)


class PRDraftAgent(BaseAgent):
    name = "PRDrafter"
    system_prompt = """\
You are the PR Drafter — create a draft GitHub pull request.

Respond with ONLY a valid JSON object matching this exact schema:

{
  "title": "concise PR title (max 60 chars)",
  "summary": "detailed description of changes",
  "files_affected": ["file1.py", "file2.py", ...],
  "behavior_change": "description of what changed and why",
  "test_plan": "how to test this PR",
  "risk_level": "the assessed risk level"
}

The PR should be clear, actionable, and include sufficient context for review.
"""

    def draft_from_review(
        self,
        analysis: AnalysisResult,
        categorization: CategorizationResult,
        risk: RiskResult,
        emit: Optional[Callable[[str, str], None]] = None,
    ) -> PRDraft:
        """
        Draft a PR based on review findings.

        Args:
            analysis, categorization, risk: from previous agents
            emit: optional callback

        Returns:
            PRDraft
        """
        content = f"""Summary: {analysis.summary}
Change Type: {categorization.change_type}
Improvements: {analysis.improvements}
Risk Level: {risk.risk_level}"""

        messages = [
            {
                "role": "user",
                "content": f"Based on this code review, draft a GitHub pull request:\n\n{content}",
            }
        ]

        response_text = self.chat(messages, emit)
        parsed = self._parse_json(response_text)

        return PRDraft(
            title=parsed.get("title", "Code improvements"),
            summary=parsed.get("summary", ""),
            files_affected=parsed.get("files_affected", []),
            behavior_change=parsed.get("behavior_change", ""),
            test_plan=parsed.get("test_plan", ""),
            risk_level=risk.risk_level,
            source="review",
        )

    def draft_from_instruction(
        self,
        instruction: str,
        emit: Optional[Callable[[str, str], None]] = None,
    ) -> PRDraft:
        """
        Draft a PR based on explicit user instruction.

        Args:
            instruction: user's explicit instruction for the PR
            emit: optional callback

        Returns:
            PRDraft
        """
        messages = [
            {
                "role": "user",
                "content": f"Draft a GitHub pull request based on this instruction:\n\n{instruction}",
            }
        ]

        response_text = self.chat(messages, emit)
        parsed = self._parse_json(response_text)

        return PRDraft(
            title=parsed.get("title", "Code improvements"),
            summary=parsed.get("summary", ""),
            files_affected=parsed.get("files_affected", []),
            behavior_change=parsed.get("behavior_change", ""),
            test_plan=parsed.get("test_plan", ""),
            risk_level=parsed.get("risk_level", "medium"),
            source="instruction",
            instruction=instruction,
        )