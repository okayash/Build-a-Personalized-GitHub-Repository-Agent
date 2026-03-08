"""
AnalyzerAgent — Analyzes the git diff for issues and improvements.
"""
from typing import Callable, Optional

from agents.base import BaseAgent
from models.schemas import AnalysisResult
import git_tools


class AnalyzerAgent(BaseAgent):
    name = "Analyzer"
    system_prompt = """\
You are the Analyzer — the first agent in a change review pipeline.

You will be given a git diff output. Your job is to analyze it for potential issues and improvements.

Respond with ONLY a valid JSON object matching this exact schema:

{
  "issues": ["list of potential issues found in the diff"],
  "improvements": ["list of suggested improvements"],
  "summary": "One sentence summarizing the changes."
}
"""

    def analyze(
        self,
        commit_range: Optional[str] = None,
        emit: Optional[Callable[[str, str], None]] = None,
    ) -> AnalysisResult:
        """
        Analyze the git diff.

        Args:
            commit_range: optional commit range for diff
            emit: optional callback

        Returns:
            AnalysisResult
        """
        diff = git_tools.get_git_diff(commit_range)
        if emit:
            emit(self.name, f"Retrieved git diff ({len(diff)} chars)")

        messages = [
            {
                "role": "user",
                "content": f"Here is the git diff:\n\n{diff}\n\nAnalyze for issues and improvements.",
            }
        ]

        response_text = self.chat(messages, emit)
        parsed = self._parse_json(response_text)

        return AnalysisResult(
            issues=parsed.get("issues", []),
            improvements=parsed.get("improvements", []),
            summary=parsed.get("summary", ""),
        )