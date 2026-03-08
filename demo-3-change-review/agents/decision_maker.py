"""
DecisionMakerAgent — Decides on the action.
"""
from typing import Callable, Optional

from agents.base import BaseAgent
from models.schemas import AnalysisResult, CategorizationResult, DecisionResult, RiskResult


class DecisionMakerAgent(BaseAgent):
    name = "DecisionMaker"
    system_prompt = """\
You are the Decision Maker — decide what action to take based on the analysis, categorization, and risk.

Possible actions: "Create Issue", "Create PR", "No action required".

Respond with ONLY a valid JSON object matching this exact schema:

{
  "action": "one of the actions",
  "reasoning": "brief explanation"
}
"""

    def decide(
        self,
        analysis: AnalysisResult,
        categorization: CategorizationResult,
        risk: RiskResult,
        emit: Optional[Callable[[str, str], None]] = None,
    ) -> DecisionResult:
        """
        Decide action.

        Args:
            analysis, categorization, risk: from previous agents
            emit: optional callback

        Returns:
            DecisionResult
        """
        content = f"""Analysis: {analysis.summary}
Issues: {analysis.issues}
Improvements: {analysis.improvements}
Change type: {categorization.change_type} - {categorization.reasoning}
Risk: {risk.risk_level} - {risk.reasoning}"""

        messages = [
            {
                "role": "user",
                "content": f"Decide on action based on this:\n\n{content}",
            }
        ]

        response_text = self.chat(messages, emit)
        parsed = self._parse_json(response_text)

        return DecisionResult(
            action=parsed.get("action", "No action required"),
            reasoning=parsed.get("reasoning", ""),
        )