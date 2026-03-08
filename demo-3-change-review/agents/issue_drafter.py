"""
IssueDraftAgent — Drafts GitHub issues based on review findings.
"""
from typing import Callable, Optional

from agents.base import BaseAgent
from models.schemas import (
    AnalysisResult,
    CategorizationResult,
    IssueDraft,
    RiskResult,
)


class IssueDraftAgent(BaseAgent):
    name = "IssueDrafter"
    system_prompt = """\
You are the Issue Drafter — create a draft GitHub issue based on detected problems.

Respond with ONLY a valid JSON object matching this exact schema:

{
  "title": "concise issue title (max 60 chars)",
  "problem_description": "detailed description of the problem",
  "evidence": "code snippet or reference showing the issue",
  "acceptance_criteria": ["criterion 1", "criterion 2", ...],
  "risk_level": "the risk level from assessment"
}

The issue should be actionable and clear. Reference the specific problems found.
"""

    def draft_from_review(
        self,
        analysis: AnalysisResult,
        categorization: CategorizationResult,
        risk: RiskResult,
        emit: Optional[Callable[[str, str], None]] = None,
    ) -> IssueDraft:
        """
        Draft an issue based on review findings.

        Args:
            analysis, categorization, risk: from previous agents
            emit: optional callback

        Returns:
            IssueDraft
        """
        content = f"""Summary: {analysis.summary}
Change Type: {categorization.change_type}
Issues: {analysis.issues}
Improvements: {analysis.improvements}
Risk Level: {risk.risk_level}"""

        messages = [
            {
                "role": "user",
                "content": f"Based on this code review, draft a GitHub issue:\n\n{content}",
            }
        ]

        response_text = self.chat(messages, emit)
        parsed = self._parse_json(response_text)

        return IssueDraft(
            title=parsed.get("title", "Code improvement needed"),
            problem_description=parsed.get("problem_description", ""),
            evidence=parsed.get("evidence", ""),
            acceptance_criteria=parsed.get("acceptance_criteria", []),
            risk_level=risk.risk_level,
            source="review",
        )

    def draft_from_instruction(
        self,
        instruction: str,
        emit: Optional[Callable[[str, str], None]] = None,
    ) -> IssueDraft:
        """
        Draft an issue based on explicit user instruction.

        Args:
            instruction: user's explicit instruction for the issue
            emit: optional callback

        Returns:
            IssueDraft
        """
        messages = [
            {
                "role": "user",
                "content": f"Draft a GitHub issue based on this instruction:\n\n{instruction}",
            }
        ]

        response_text = self.chat(messages, emit)
        parsed = self._parse_json(response_text)

        return IssueDraft(
            title=parsed.get("title", "Issue"),
            problem_description=parsed.get("problem_description", ""),
            evidence=parsed.get("evidence", ""),
            acceptance_criteria=parsed.get("acceptance_criteria", []),
            risk_level=parsed.get("risk_level", "medium"),
            source="instruction",
            instruction=instruction,
        )