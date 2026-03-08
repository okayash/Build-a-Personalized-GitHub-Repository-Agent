"""
ImproverAgent — Drafts improved versions of issues/PRs based on plan.

Multi-agent pattern: takes output from Planner and Writer role.
"""
from typing import Callable, Optional

from agents.base import BaseAgent
from models.improvements import (
    ImprovedIssue,
    ImprovedPR,
    ImprovementPlan,
    IssueCritique,
    PRCritique,
)


class ImproverAgent(BaseAgent):
    name = "Improver"
    system_prompt = """\
You are the Improver — draft an improved version of a GitHub issue or PR.

This must be a STRUCTURED improvement that:
1. Fixes all identified issues from the critique
2. Adds missing information (acceptance criteria, test plan, etc.)
3. Uses clear, specific language (no vague terms)
4. Includes evidence and references where needed
5. Documents risk level and breaking changes (for PRs)

Respond with ONLY a valid JSON object matching this exact schema (for issues):

{
  "new_title": "clear, specific title (max 60 chars)",
  "new_description": "detailed, well-structured description",
  "improved_acceptance_criteria": ["criterion 1", "criterion 2", ...],
  "risk_level": "low|medium|high",
  "clear_evidence": "code snippet, test case, or reference supporting the issue",
  "policy_compliance": "statement of compliance with relevant policies"
}

Or for PRs:

{
  "new_title": "clear title",
  "new_description": "detailed description of changes",
  "improved_behavior_change": "specific, measurable behavior change",
  "improved_test_plan": "detailed testing strategy",
  "risk_level": "low|medium|high",
  "breaking_changes_documented": true/false
}
"""

    def improve_issue(
        self,
        critique: IssueCritique,
        plan: ImprovementPlan,
        emit: Optional[Callable[[str, str], None]] = None,
    ) -> ImprovedIssue:
        """
        Draft an improved version of an issue.

        Args:
            critique: from ReviewerAgent
            plan: from PlannerAgent
            emit: optional callback

        Returns:
            ImprovedIssue
        """
        content = f"""Original Issue:
Title: {critique.title}
Body: {critique.current_body}

Critique Summary: {critique.summary}
Quality Score: {critique.overall_quality}/100

Improvement Plan:
{plan.planning_rationale}

Prioritized Improvements:
{chr(10).join(f"  • {imp}" for imp in plan.prioritized_improvements)}
"""

        messages = [
            {
                "role": "user",
                "content": f"Improve this GitHub issue based on the critique and plan:\n\n{content}",
            }
        ]

        response_text = self.chat(messages, emit)
        parsed = self._parse_json(response_text)

        return ImprovedIssue(
            original_id=critique.issue_id,
            new_title=parsed.get("new_title", critique.title),
            new_description=parsed.get("new_description", critique.current_body),
            improved_acceptance_criteria=parsed.get("improved_acceptance_criteria", []),
            risk_level=parsed.get("risk_level", "medium"),
            clear_evidence=parsed.get("clear_evidence", ""),
            policy_compliance=parsed.get("policy_compliance", "Complies with standard practices"),
            critique_summary=critique.summary,
        )

    def improve_pr(
        self,
        critique: PRCritique,
        plan: ImprovementPlan,
        emit: Optional[Callable[[str, str], None]] = None,
    ) -> ImprovedPR:
        """
        Draft an improved version of a PR.

        Args:
            critique: from ReviewerAgent
            plan: from PlannerAgent
            emit: optional callback

        Returns:
            ImprovedPR
        """
        content = f"""Original PR:
Title: {critique.title}
Branch: {critique.branch}
Body: {critique.current_body}

Critique Summary: {critique.summary}
Quality Score: {critique.overall_quality}/100

Improvement Plan:
{plan.planning_rationale}

Prioritized Improvements:
{chr(10).join(f"  • {imp}" for imp in plan.prioritized_improvements)}
"""

        messages = [
            {
                "role": "user",
                "content": f"Improve this GitHub PR based on the critique and plan:\n\n{content}",
            }
        ]

        response_text = self.chat(messages, emit)
        parsed = self._parse_json(response_text)

        return ImprovedPR(
            original_id=critique.pr_id,
            new_title=parsed.get("new_title", critique.title),
            new_description=parsed.get("new_description", critique.current_body),
            improved_behavior_change=parsed.get("improved_behavior_change", ""),
            improved_test_plan=parsed.get("improved_test_plan", ""),
            risk_level=parsed.get("risk_level", "medium"),
            breaking_changes_documented=parsed.get("breaking_changes_documented", False),
            critique_summary=critique.summary,
        )