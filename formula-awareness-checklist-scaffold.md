# Formula Awareness — Checklist & Scaffolding (Google Sheets focus)

## Purpose
Concise checklist and starter scaffolding to implement formula-awareness for BuildBridge-MCP (Google Sheets). Do not implement — this file is a plan + skeletons to guide implementation.

---

## Current Progress (Prep — 2025-09-27)
- [x] Created feature branch `feature/formula-awareness-phase1` for dedicated development.
- [x] Added scaffolding modules (`src/connectors/enhanced_google_sheets_connector.py`, `src/models/formula_context.py`, `src/ai/formula_aware_ai_service.py`).
- [x] Stubbed validation helpers in `src/schema_discovery.py` and placeholder tests/metrics/docs.
- [x] Declared `networkx` dependency for upcoming graph work.
- [x] Completed Phase 1 extraction logic (formula context builder, cache persistence, metrics instrumentation, tests).

## Quick Executive Checklist (Phase-driven)

Phase 1 — Core Formula Extraction (Week 1)
- [x] Create EnhancedGoogleSheetsConnector (fetch formulas + values)
- [x] Extract sheet metadata, data validation, conditional formatting
- [x] Build dependency graph (networkx)
- [x] Persist normalized cache entries: {value, formula, dependencies, last_updated, provenance}
- [x] Add basic Prometheus metrics: formula_extraction_success_rate, formula_extraction_duration
- Exit criteria: extraction success rate ≥ 95% on pilot sheets; normalized cache present

Phase 2 — Business Logic Analysis (Week 2)
- [ ] Classify formulas into business rule categories
- [ ] Detect circular references and broken refs; add remediation guidance
- [ ] Implement basic visualization/export of dependency graph
- Exit criteria: dependency graph accuracy > 90% on pilot set

Phase 3 — AI Integration & What-if (Week 3)
- [ ] Integrate formula context into AIService prompts (FormulaAwareAIService)
- [ ] Implement template for "what-if" simulation using formula graph
- [ ] Add formula-aware tests to gold dataset
- Exit criteria: AI accuracy uplift for formula queries ≥ target (start target 25%)

Phase 4 — Monitoring, CI, Hardening (Week 4)
- [ ] Add alerting rules for formula failures and circular refs
- [ ] Add CI tests for formula extraction and AI gold tests
- [ ] Document operational runbook and rollback plan
- Exit criteria: CI gate passing; alerts wired to Slack/pager

---

## Minimal Success Metrics (to track)
- formula_extraction_success_rate >= 0.95
- dependency_graph_accuracy >= 0.90
- circular_reference_false_positive_rate == 0
- AI formula-query accuracy uplift >= 0.25 (25%)

---

## Files to scaffold (skeletons included below)
- buildbridge/connectors/enhanced_google_sheets.py
- buildbridge/schema/schema_discovery.py (extensions)
- buildbridge/models/formula_context.py
- buildbridge/ai/formula_aware_ai_service.py
- tests/test_formula_extraction.py
- deployment/prometheus/formula-metrics.yml (metrics names)
- docs/runbook/formula-awareness.md

---

## Scaffolds (starter code)

```python
# filepath: /home/egk/buildbridge-MCP/BuildBridge-MCP/buildbridge/connectors/enhanced_google_sheets.py
from typing import Dict, Any, List
import logging

class EnhancedGoogleSheetsConnector:
    """Formula-aware Google Sheets connector (skeleton)."""

    def __init__(self, gcp_client, config: Dict[str, Any]):
        self.client = gcp_client
        self.config = config
        self.logger = logging.getLogger("EnhancedGoogleSheetsConnector")

    def get_comprehensive_sheet_context(self, sheet_id: str, range_name: str = None) -> Dict[str, Any]:
        """
        Return dict with keys:
        - raw_values
        - formulas
        - dependencies (adj-list or graph)
        - data_validation
        - conditional_formatting
        - metadata (last_updated, owner)
        """
        # TODO: implement calls to Sheets API with includeGridData or valueRenderOption=FORMULA
        return {
            "raw_values": None,
            "formulas": None,
            "dependencies": None,
            "data_validation": None,
            "conditional_formatting": None,
            "metadata": None
        }

    def _extract_formulas(self, api_response) -> List[List[str]]:
        # TODO: parse cell.formula values from API response
        return []

    def _build_dependency_graph(self, formulas: List[List[str]]):
        # TODO: parse references and return networkx DiGraph or adjacency
        return {}
```

```python
# filepath: /home/egk/buildbridge-MCP/BuildBridge-MCP/buildbridge/models/formula_context.py
from dataclasses import dataclass
from typing import Any, List

@dataclass
class FormulaContext:
    formula: str
    cell_address: str
    dependencies: List[str]
    description: str = ""
    business_rule: str = ""
    calculated_value: Any = None
    last_updated: str = ""
```

```python
# filepath: /home/egk/buildbridge-MCP/BuildBridge-MCP/buildbridge/schema/schema_discovery.py
# ... existing code ...
# Add stubs to validate formulas and dependencies

def detect_circular_references(dependencies_graph) -> List[List[str]]:
    """
    Return list of cycles found (each cycle is a list of node addresses).
    """
    # TODO: use networkx.simple_cycles
    return []

def validate_dependencies_exist(dependencies_graph, known_cells) -> List[str]:
    """
    Return list of missing dependency addresses.
    """
    # TODO: simple set difference
    return []
# ... existing code ...
```

```python
# filepath: /home/egk/buildbridge-MCP/BuildBridge-MCP/buildbridge/ai/formula_aware_ai_service.py
# Minimal skeleton showing integration point

class FormulaAwareAIService:
    def __init__(self, base_ai_service):
        self.base = base_ai_service

    def process_with_formula_context(self, query: str, sheet_context: dict) -> str:
        """
        Construct enhanced prompt containing:
        - brief normalized raw data
        - summarized business rules (formulas)
        - dependency hints
        - instructions for what-if simulation
        """
        # TODO: implement prompt builder and call self.base.process_request(...)
        return self.base.process_request("TODO: composed prompt")
```

```python
# filepath: /home/egk/buildbridge-MCP/BuildBridge-MCP/tests/test_formula_extraction.py
import pytest

def test_extract_formulas_sample():
    # TODO: add fixtures representing a small google sheet with formulas
    assert True
```

```yaml
# filepath: /home/egk/buildbridge-MCP/BuildBridge-MCP/deployment/prometheus/formula-metrics.yml
# Example metric names to export/collect
metrics:
  - formula_extraction_success_rate
  - formula_extraction_duration_seconds
  - circular_reference_count
  - formula_change_frequency
```

```md
<!-- filepath: /home/egk/buildbridge-MCP/BuildBridge-MCP/docs/runbook/formula-awareness.md -->
# Formula Awareness Runbook (operational notes)
- How to run extraction for a sheet (pilot)
- How to interpret circular_reference_count
- How to rollback formula parsing changes
- Contact list and escalation
```

---

## Recommended immediate next actions (non-implementation)
1. Review checklist & scaffold file and confirm Phase 1 pilot sheet(s.
2. Add Google service account credentials path to config (do not commit secrets).
3. Create a Git issue/kanban card for each checklist item and assign owners.

---

End of file.
