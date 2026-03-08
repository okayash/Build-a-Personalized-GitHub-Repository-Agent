"""
ReviewerAgent — Analyzes existing GitHub issues/PRs for problems and gaps.

This is the first agent in the improvement pipeline, responsible for critique.
"""
from typing import Callable, Optional

from agents.base import BaseAgent
from models.improvements import CritiqueItem, IssueCritique, PRCritique


class ReviewerAgent(BaseAgent):
    name = "Reviewer"
    system_prompt = """\
You are the Reviewer — analyze existing GitHub issues or PRs for quality issues.

Identify:
1. Unclear language or vague descriptions
2. Missing information (acceptance criteria, test plan, etc.)
3. Unsupported claims (without evidence)
4. Missing test coverage references
5. Policy violations (if applicable)

Respond with ONLY a valid JSON object matching this exact schema:

{
  "critiques": [
    {
      "category": "unclear|vague|missing_info|policy|evidence",
      "severity": "low|medium|high",
      "finding": "specific finding",
      "line_reference": 10 (optional, null if not applicable)
    }
  ],
  "overall_quality": 0-100,
  "summary": "one sentence summary of key issues"
}

Be specific and constructive. Look for real problems, not nitpicks.
"""

    def critique_issue(
        self,
        issue_id: str,
        title: str,
        body: str,
        emit: Optional[Callable[[str, str], None]] = None,
    ) -> IssueCritique:
        """
        Critique an existing GitHub issue.

        Args:
            issue_id: GitHub issue ID or URL
            title: issue title
            body: issue description
            emit: optional callback

        Returns:
            IssueCritique
        """
        content = f"Title: {title}\n\nBody:\n{body}"

        messages = [
            {
                "role": "user",
                "content": f"Critique this GitHub issue for clarity, completeness, and quality:\n\n{content}",
            }
        ]

        response_text = self.chat(messages, emit)
        parsed = self._parse_json(response_text)

        critiques = [
            CritiqueItem(
                category=c.get("category", "other"),
                severity=c.get("severity", "low"),
                finding=c.get("finding", ""),
                line_reference=c.get("line_reference"),
            )
            for c in parsed.get("critiques", [])
        ]

        return IssueCritique(
            issue_id=issue_id,
            title=title,
            current_body=body,
            critiques=critiques,
            overall_quality=parsed.get("overall_quality", 50),
            summary=parsed.get("summary", ""),
        )

    def critique_pr(
        self,
        pr_id: str,
        title: str,
        body: str,
        branch: str,
        emit: Optional[Callable[[str, str], None]] = None,
    ) -> PRCritique:
        """
        Critique an existing GitHub PR.

        Args:
            pr_id: GitHub PR ID
            title: PR title
            body: PR description
            branch: branch name
            emit: optional callback

        Returns:
            PRCritique
        """
        content = f"Branch: {branch}\nTitle: {title}\n\nBody:\n{body}"

        messages = [
            {
                "role": "user",
                "content": f"Critique this GitHub PR for clarity, completeness, and quality:\n\n{content}",
            }
        ]

        response_text = self.chat(messages, emit)
        parsed = self._parse_json(response_text)

        critiques = [
            CritiqueItem(
                category=c.get("category", "other"),
                severity=c.get("severity", "low"),
                finding=c.get("finding", ""),
                line_reference=c.get("line_reference"),
            )
            for c in parsed.get("critiques", [])
        ]

        return PRCritique(
            pr_id=pr_id,
            title=title,
            current_body=body,
            branch=branch,
            critiques=critiques,
            overall_quality=parsed.get("overall_quality", 50),
            summary=parsed.get("summary", ""),
        )