"""
PlannerAgent — Creates a structured improvement plan based on critique.

Multi-agent pattern: takes output from Reviewer and plans improvements.
"""
from typing import Callable, Optional

from agents.base import BaseAgent
from models.improvements import IssueCritique, ImprovementPlan, PRCritique


class PlannerAgent(BaseAgent):
    name = "Planner"
    system_prompt = """\
You are the Planner — create a structured improvement plan based on critique findings.

Given a critique, produce a prioritized list of improvements and estimated effort.

Respond with ONLY a valid JSON object matching this exact schema:

{
  "planning_rationale": "brief explanation of the overall approach",
  "prioritized_improvements": [
    "improvement 1 (critical)",
    "improvement 2 (high)",
    "improvement 3 (medium)"
  ],
  "estimated_effort": "low|medium|high",
  "dependencies": ["reference to related issue #123", ...]
}

Prioritize by severity and impact. Estimate realistic effort.
"""

    def plan_issue_improvement(
        self,
        critique: IssueCritique,
        emit: Optional[Callable[[str, str], None]] = None,
    ) -> ImprovementPlan:
        """
        Plan improvements for an issue based on critique.

        Args:
            critique: from ReviewerAgent
            emit: optional callback

        Returns:
            ImprovementPlan
        """
        critique_summary = f"Quality score: {critique.overall_quality}/100\n"
        critique_summary += f"Summary: {critique.summary}\n"
        critique_summary += "Critiques:\n"
        for item in critique.critiques:
            critique_summary += f"  [{item.severity}] {item.category}: {item.finding}\n"

        messages = [
            {
                "role": "user",
                "content": f"Create a prioritized improvement plan for this issue:\n\n{critique_summary}",
            }
        ]

        response_text = self.chat(messages, emit)
        parsed = self._parse_json(response_text)

        return ImprovementPlan(
            target_type="issue",
            target_id=critique.issue_id,
            planning_rationale=parsed.get("planning_rationale", ""),
            prioritized_improvements=parsed.get("prioritized_improvements", []),
            estimated_effort=parsed.get("estimated_effort", "medium"),
            dependencies=parsed.get("dependencies", []),
        )

    def plan_pr_improvement(
        self,
        critique: PRCritique,
        emit: Optional[Callable[[str, str], None]] = None,
    ) -> ImprovementPlan:
        """
        Plan improvements for a PR based on critique.

        Args:
            critique: from ReviewerAgent
            emit: optional callback

        Returns:
            ImprovementPlan
        """
        critique_summary = f"Quality score: {critique.overall_quality}/100\n"
        critique_summary += f"Summary: {critique.summary}\n"
        critique_summary += "Critiques:\n"
        for item in critique.critiques:
            critique_summary += f"  [{item.severity}] {item.category}: {item.finding}\n"

        messages = [
            {
                "role": "user",
                "content": f"Create a prioritized improvement plan for this PR:\n\n{critique_summary}",
            }
        ]

        response_text = self.chat(messages, emit)
        parsed = self._parse_json(response_text)

        return ImprovementPlan(
            target_type="pr",
            target_id=critique.pr_id,
            planning_rationale=parsed.get("planning_rationale", ""),
            prioritized_improvements=parsed.get("prioritized_improvements", []),
            estimated_effort=parsed.get("estimated_effort", "medium"),
            dependencies=parsed.get("dependencies", []),
        )