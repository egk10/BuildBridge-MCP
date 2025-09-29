"""Formula-aware AI service scaffolding.

Wraps the existing AI service with prompt composition hooks that
incorporate spreadsheet business logic. Implementation will follow
Phase 3 of the formula awareness roadmap.
"""

from __future__ import annotations

from typing import Any, Dict

from ai_service import AIService


class FormulaAwareAIService:
    """Decorator-style wrapper that injects formula context into prompts."""

    def __init__(self, base_ai_service: AIService):
        self.base = base_ai_service

    def process_with_formula_context(self, query: str, sheet_context: Dict[str, Any]) -> str:
        """Compose an enhanced prompt that includes formula business logic."""

        # TODO: Implement prompt synthesis leveraging FormulaContext data.
        prompt = self._build_prompt(query, sheet_context)
        return self.base.process_request(prompt)

    def _build_prompt(self, query: str, sheet_context: Dict[str, Any]) -> str:
        """Placeholder prompt builder for formula-aware responses."""

        # TODO: Summarize business rules, dependencies, and validation signals.
        # Keeping implementation minimal for scaffolding purposes.
        return (
            "You are analyzing a construction project spreadsheet.\n"
            f"User query: {query}\n"
            "Formula context is not yet implemented. Provide a generic response."
        )
