"""
GatekeeperAgent — Verifies improvements and enforces human approval before creation.

Multi-agent pattern: final safety check and approval gate.
"""
from typing import Callable, Optional, Tuple

from agents.base import BaseAgent
from models.improvements import ImprovedIssue, ImprovedPR


class GatekeeperAgent(BaseAgent):
    name = "Gatekeeper"
    system_prompt = """\
You are the Gatekeeper — verify that suggested improvements are safe and ready.

Check for:
1. No breaking changes not documented (PRs)
2. Policy compliance
3. Realistic and actionable improvements
4. No fabricated evidence or claims
5. Clear improvement over original

Respond with ONLY a valid JSON object matching this exact schema:

{
  "verification_passed": true/false,
  "issues_found": ["list of any safety issues"],
  "recommendation": "APPROVE|REVIEW_CHANGES|BLOCK",
  "reason": "explanation"
}

APPROVE = ready for user review and creation
REVIEW_CHANGES = user should review the improvements again
BLOCK = do not present to user due to safety concerns
"""

    def verify_issue_improvement(
        self,
        improved: ImprovedIssue,
        emit: Optional[Callable[[str, str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Verify an improved issue is safe and ready.

        Args:
            improved: from ImproverAgent
            emit: optional callback

        Returns:
            (safe: bool, reason: str)
        """
        content = f"""Improved Issue:
Title: {improved.new_title}
Description: {improved.new_description}
Acceptance Criteria: {chr(10).join(f"  • {c}" for c in improved.improved_acceptance_criteria)}
Evidence: {improved.clear_evidence}
Policy Compliance: {improved.policy_compliance}
Risk Level: {improved.risk_level}
"""

        messages = [
            {
                "role": "user",
                "content": f"Verify this improved issue is safe, realistic, and ready:\n\n{content}",
            }
        ]

        response_text = self.chat(messages, emit)
        parsed = self._parse_json(response_text)

        recommendation = parsed.get("recommendation", "REVIEW_CHANGES")
        safe = recommendation == "APPROVE"
        reason = parsed.get("reason", "")

        if not safe and emit:
            emit(self.name, f"Verification: {reason}")

        return safe, reason

    def verify_pr_improvement(
        self,
        improved: ImprovedPR,
        emit: Optional[Callable[[str, str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Verify an improved PR is safe and ready.

        Args:
            improved: from ImproverAgent
            emit: optional callback

        Returns:
            (safe: bool, reason: str)
        """
        content = f"""Improved PR:
Title: {improved.new_title}
Description: {improved.new_description}
Behavior Change: {improved.improved_behavior_change}
Test Plan: {improved.improved_test_plan}
Risk Level: {improved.risk_level}
Breaking Changes Documented: {improved.breaking_changes_documented}
"""

        messages = [
            {
                "role": "user",
                "content": f"Verify this improved PR is safe, realistic, and ready:\n\n{content}",
            }
        ]

        response_text = self.chat(messages, emit)
        parsed = self._parse_json(response_text)

        recommendation = parsed.get("recommendation", "REVIEW_CHANGES")
        safe = recommendation == "APPROVE"
        reason = parsed.get("reason", "")

        if not safe and emit:
            emit(self.name, f"Verification: {reason}")

        return safe, reason