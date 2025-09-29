"""Dataclasses representing formula context artifacts.

This scaffolding follows the formula awareness plan and will be
expanded once the extraction pipeline is implemented.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class FormulaContext:
    """Rich context about a single formula and its business logic."""

    formula: Optional[str]
    cell_address: str
    dependencies: List[str] = field(default_factory=list)
    description: str = ""
    business_rule: str = ""
    calculated_value: Any = None
    last_updated: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize context with consistent ordering."""

        payload = asdict(self)
        payload["dependencies"] = sorted(set(payload.get("dependencies", [])))
        return payload
