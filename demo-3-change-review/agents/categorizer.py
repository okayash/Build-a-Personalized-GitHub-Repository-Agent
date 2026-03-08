"""
CategorizerAgent — Categorizes the change type.
"""
from typing import Callable, Optional

from agents.base import BaseAgent
from models.schemas import AnalysisResult, CategorizationResult


class CategorizerAgent(BaseAgent):
    name = "Categorizer"
    system_prompt = """\
You are the Categorizer — categorize the type of change based on the analysis.

Possible categories: feature, bugfix, refactor, documentation, test, style, performance, security, other.

Respond with ONLY a valid JSON object matching this exact schema:

{
  "change_type": "one of the categories",
  "reasoning": "brief explanation"
}
"""

    def categorize(
        self,
        analysis: AnalysisResult,
        emit: Optional[Callable[[str, str], None]] = None,
    ) -> CategorizationResult:
        """
        Categorize the change.

        Args:
            analysis: from previous agent
            emit: optional callback

        Returns:
            CategorizationResult
        """
        content = f"Analysis summary: {analysis.summary}\nIssues: {analysis.issues}\nImprovements: {analysis.improvements}"

        messages = [
            {
                "role": "user",
                "content": f"Based on this analysis, categorize the change:\n\n{content}",
            }
        ]

        response_text = self.chat(messages, emit)
        parsed = self._parse_json(response_text)

        return CategorizationResult(
            change_type=parsed.get("change_type", "other"),
            reasoning=parsed.get("reasoning", ""),
        )