"""
RiskAssessorAgent — Assesses the risk level.
"""
from typing import Callable, Optional

from agents.base import BaseAgent
from models.schemas import AnalysisResult, RiskResult


class RiskAssessorAgent(BaseAgent):
    name = "RiskAssessor"
    system_prompt = """\
You are the Risk Assessor — assess the risk level of the changes.

Risk levels: low, medium, high.

Consider factors like complexity, potential for breaking changes, security implications, etc.

Respond with ONLY a valid JSON object matching this exact schema:

{
  "risk_level": "low|medium|high",
  "reasoning": "brief explanation"
}
"""

    def assess_risk(
        self,
        analysis: AnalysisResult,
        emit: Optional[Callable[[str, str], None]] = None,
    ) -> RiskResult:
        """
        Assess risk.

        Args:
            analysis: from previous agent
            emit: optional callback

        Returns:
            RiskResult
        """
        content = f"Analysis summary: {analysis.summary}\nIssues: {analysis.issues}\nImprovements: {analysis.improvements}"

        messages = [
            {
                "role": "user",
                "content": f"Assess the risk of these changes:\n\n{content}",
            }
        ]

        response_text = self.chat(messages, emit)
        parsed = self._parse_json(response_text)

        return RiskResult(
            risk_level=parsed.get("risk_level", "medium"),
            reasoning=parsed.get("reasoning", ""),
        )