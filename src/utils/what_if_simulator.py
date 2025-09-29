"""What-if simulation engine for spreadsheet formula analysis.

Provides capabilities to simulate changes to spreadsheet values and analyze
their impact through formula dependency networks.
"""

from __future__ import annotations

import copy
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SimulationType(Enum):
    VALUE_CHANGE = "value_change"
    FORMULA_MODIFICATION = "formula_modification"
    RANGE_EXPANSION = "range_expansion"
    CONDITIONAL_CHANGE = "conditional_change"


@dataclass
class SimulationChange:
    """Represents a single change in the simulation."""
    cell_address: str
    old_value: Any
    new_value: Any
    change_type: str
    description: str


@dataclass
class SimulationResult:
    """Result of a what-if simulation."""
    original_values: Dict[str, Any]
    changed_values: Dict[str, Any]
    affected_cells: Set[str]
    impact_chain: List[str]
    confidence_score: float
    assumptions: List[str]
    warnings: List[str]


class WhatIfSimulator:
    """
    Simulates the impact of changes on spreadsheet formulas and values
    through dependency graph analysis.
    """

    def __init__(self, dependency_graph: Dict[str, List[str]],
                 formula_contexts: List[Dict[str, Any]]):
        """
        Initialize simulator with dependency graph and formula contexts.

        Args:
            dependency_graph: Adjacency list of cell dependencies
            formula_contexts: List of formula context dictionaries
        """
        self.dependency_graph = dependency_graph
        self.formula_contexts = {ctx['cell_address']: ctx for ctx in formula_contexts}
        self.reverse_dependencies = self._build_reverse_dependencies()

    def _build_reverse_dependencies(self) -> Dict[str, List[str]]:
        """Build reverse dependency graph (who depends on whom)."""
        reverse_deps = {}

        for cell, dependencies in self.dependency_graph.items():
            for dep in dependencies:
                if dep not in reverse_deps:
                    reverse_deps[dep] = []
                reverse_deps[dep].append(cell)

        return reverse_deps

    def simulate_value_change(self, changes: List[Tuple[str, Any]],
                            original_values: Dict[str, Any]) -> SimulationResult:
        """
        Simulate the impact of changing cell values.

        Args:
            changes: List of (cell_address, new_value) tuples
            original_values: Original spreadsheet values

        Returns:
            SimulationResult with impact analysis
        """

        # Create working copy of values
        working_values = copy.deepcopy(original_values)

        # Apply changes
        applied_changes = []
        affected_cells = set()

        for cell_address, new_value in changes:
            if cell_address in working_values:
                old_value = working_values[cell_address]
                applied_changes.append(SimulationChange(
                    cell_address=cell_address,
                    old_value=old_value,
                    new_value=new_value,
                    change_type="value_change",
                    description=f"Changed {cell_address} from {old_value} to {new_value}"
                ))

                # Mark cell as changed
                working_values[cell_address] = new_value
                affected_cells.add(cell_address)

        # Propagate changes through dependency graph
        impact_chain = self._propagate_changes(affected_cells, working_values)

        # Calculate confidence score
        confidence_score = self._calculate_simulation_confidence(applied_changes, impact_chain)

        return SimulationResult(
            original_values=original_values,
            changed_values=working_values,
            affected_cells=affected_cells.union(impact_chain),
            impact_chain=list(impact_chain),
            confidence_score=confidence_score,
            assumptions=[
                "Linear propagation through direct dependencies only",
                "No complex formula evaluation performed",
                "Conditional logic impacts not fully simulated",
                "Array formulas and complex references simplified"
            ],
            warnings=self._generate_warnings(applied_changes, impact_chain)
        )

    def _propagate_changes(self, changed_cells: Set[str],
                          working_values: Dict[str, Any]) -> Set[str]:
        """
        Propagate changes through the dependency graph to find affected cells.
        """

        affected = set()
        visited = set()

        def dfs(cell: str):
            if cell in visited:
                return
            visited.add(cell)

            # If this cell depends on changed cells, it's affected
            dependencies = self.dependency_graph.get(cell, [])
            if any(dep in changed_cells for dep in dependencies):
                affected.add(cell)

                # Continue to cells that depend on this cell
                dependents = self.reverse_dependencies.get(cell, [])
                for dependent in dependents:
                    dfs(dependent)

        # Start DFS from all changed cells
        for cell in changed_cells:
            dependents = self.reverse_dependencies.get(cell, [])
            for dependent in dependents:
                dfs(dependent)

        return affected

    def _calculate_simulation_confidence(self, changes: List[SimulationChange],
                                       impact_chain: Set[str]) -> float:
        """Calculate confidence score for the simulation."""

        base_confidence = 0.7  # Base confidence for simple value changes

        # Reduce confidence for complex formulas
        complex_categories = {'financial', 'logical', 'lookup_reference', 'construction_specific'}
        complex_formulas = 0

        for change in changes:
            formula_ctx = self.formula_contexts.get(change.cell_address)
            if formula_ctx and formula_ctx.get('business_rule', '').lower() in complex_categories:
                complex_formulas += 1

        # Penalty for complex formulas
        if complex_formulas > 0:
            base_confidence -= min(complex_formulas * 0.1, 0.3)

        # Reduce confidence for large impact chains
        if len(impact_chain) > 20:
            base_confidence -= 0.1

        return max(0.1, min(1.0, base_confidence))

    def _generate_warnings(self, changes: List[SimulationChange],
                          impact_chain: Set[str]) -> List[str]:
        """Generate warnings about simulation limitations."""

        warnings = []

        # Check for circular dependencies
        # This would need access to cycle detection results

        # Check for large impact chains
        if len(impact_chain) > 50:
            warnings.append(f"Large impact chain detected ({len(impact_chain)} cells) - results may be incomplete")

        # Check for complex formula changes
        complex_changes = []
        for change in changes:
            formula_ctx = self.formula_contexts.get(change.cell_address)
            if formula_ctx:
                category = formula_ctx.get('business_rule', '').lower()
                if category in ['financial', 'logical', 'array_formula']:
                    complex_changes.append(change.cell_address)

        if complex_changes:
            warnings.append(f"Complex formulas in changed cells {complex_changes} - simulation accuracy reduced")

        # Check for missing dependencies
        missing_deps = []
        for change in changes:
            if change.cell_address not in self.dependency_graph:
                missing_deps.append(change.cell_address)

        if missing_deps:
            warnings.append(f"Cells {missing_deps} have unknown dependencies - impact may be underestimated")

        return warnings

    def generate_simulation_report(self, result: SimulationResult) -> str:
        """Generate a human-readable simulation report."""

        report_parts = [
            "# What-If Simulation Report",
            "",
            "## Changes Applied",
        ]

        # This would need to be enhanced to show actual changes
        report_parts.extend([
            f"- {len(result.affected_cells)} cells potentially affected",
            f"- Impact chain length: {len(result.impact_chain)}",
            f"- Confidence score: {result.confidence_score:.2f}",
            "",
            "## Assumptions",
        ])

        for assumption in result.assumptions:
            report_parts.append(f"- {assumption}")

        if result.warnings:
            report_parts.extend([
                "",
                "## Warnings",
            ])
            for warning in result.warnings:
                report_parts.append(f"- ⚠️ {warning}")

        report_parts.extend([
            "",
            "## Recommendations",
            "- Review affected cells for business logic impacts",
            "- Validate critical calculations manually",
            "- Consider testing with actual spreadsheet software",
            "- Document assumptions for future reference"
        ])

        return "\n".join(report_parts)


def create_what_if_template(scenario_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a what-if simulation template for common scenarios.

    Args:
        scenario_type: Type of scenario (budget_change, timeline_shift, etc.)
        parameters: Scenario-specific parameters

    Returns:
        Template dictionary for simulation
    """

    templates = {
        'budget_change': {
            'description': 'Simulate budget changes and their impact on project costs',
            'required_params': ['budget_cell', 'change_percentage', 'affected_categories'],
            'simulation_steps': [
                'Identify budget-related formulas',
                'Calculate percentage impact',
                'Propagate through cost calculations',
                'Update totals and variances'
            ]
        },
        'timeline_shift': {
            'description': 'Simulate schedule changes and their impact on project timeline',
            'required_params': ['milestone_cell', 'delay_days', 'critical_path_cells'],
            'simulation_steps': [
                'Update milestone dates',
                'Recalculate dependent dates',
                'Identify critical path impacts',
                'Update completion percentages'
            ]
        },
        'resource_change': {
            'description': 'Simulate resource allocation changes',
            'required_params': ['resource_cell', 'new_allocation', 'dependent_tasks'],
            'simulation_steps': [
                'Update resource assignments',
                'Recalculate task durations',
                'Update cost calculations',
                'Check resource constraints'
            ]
        }
    }

    if scenario_type not in templates:
        raise ValueError(f"Unknown scenario type: {scenario_type}")

    template = templates[scenario_type].copy()
    template['scenario_type'] = scenario_type
    template['parameters'] = parameters

    # Validate required parameters
    required = template['required_params']
    missing = [param for param in required if param not in parameters]
    if missing:
        raise ValueError(f"Missing required parameters for {scenario_type}: {missing}")

    return template