"""Formula-aware AI service for enhanced spreadsheet analysis.

Integrates formula context, business logic analysis, and what-if simulation
capabilities into the AI service layer for construction management queries.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import asdict

from ai_service import AIService
from schema_discovery import FormulaClassifier, analyze_dependency_graph
from models.formula_context import FormulaContext
from utils.what_if_simulator import WhatIfSimulator, create_what_if_template

logger = logging.getLogger(__name__)


class FormulaAwareAIService:
    """
    Enhanced AI service that incorporates spreadsheet formula context and business logic
    for more accurate construction management analysis.
    """

    def __init__(self, base_ai_service: AIService):
        self.base = base_ai_service
        self.formula_classifier = FormulaClassifier()
        self.logger = logging.getLogger(__name__)

    async def process_with_formula_context(
        self,
        query: str,
        sheet_context: Dict[str, Any],
        query_type: str = "general"
    ) -> Any:
        """
        Process query with enhanced formula context and business logic understanding.

        Args:
            query: User's natural language query
            sheet_context: Context from EnhancedGoogleSheetsConnector.get_comprehensive_sheet_context()
            query_type: Type of construction query (budget, schedule, etc.)

        Returns:
            AIResponse with formula-aware analysis
        """

        # Extract and analyze formula context
        formula_context = self._extract_formula_context(sheet_context)

        # Enhance data context with formula insights
        enhanced_data_context = self._build_enhanced_data_context(sheet_context, formula_context)

        # Check if this is a what-if scenario
        if self._is_what_if_query(query):
            return await self._handle_what_if_simulation(query, sheet_context, formula_context, query_type)

        # Build enhanced prompt with formula awareness
        enhanced_query = self._enhance_query_with_formula_context(query, formula_context)

        # Process with base AI service using enhanced context
        return await self.base.process_construction_query(
            query=enhanced_query,
            context=self._build_formula_context_string(formula_context),
            data_context=enhanced_data_context,
            query_type=query_type
        )

    def _extract_formula_context(self, sheet_context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and analyze formula-related information from sheet context."""

        formulas = sheet_context.get('formulas', {})
        dependencies = sheet_context.get('dependencies', {})
        business_rules = sheet_context.get('business_rules', {})

        # Classify all formulas
        formula_classifications = self.formula_classifier.classify_formulas_batch(formulas)

        # Analyze dependency graph
        dependency_analysis = analyze_dependency_graph(dependencies)

        # Extract formula contexts
        formula_contexts = sheet_context.get('formula_contexts', [])

        return {
            'formulas': formulas,
            'classifications': formula_classifications,
            'dependencies': dependencies,
            'dependency_analysis': dependency_analysis,
            'business_rules': business_rules,
            'formula_contexts': formula_contexts,
            'summary': self._generate_formula_summary(formula_classifications, dependency_analysis)
        }

    def _build_enhanced_data_context(self, sheet_context: Dict[str, Any],
                                   formula_context: Dict[str, Any]) -> Dict[str, Any]:
        """Build enhanced data context with formula insights."""

        base_data_context = sheet_context.get('raw_values', {})

        # Add formula insights
        enhanced_context = {
            'spreadsheet_data': base_data_context,
            'formula_insights': {
                'total_formulas': len(formula_context['formulas']),
                'formula_categories': self._count_categories(formula_context['classifications']),
                'dependency_complexity': formula_context['dependency_analysis']['num_edges'],
                'has_cycles': len(formula_context['dependency_analysis']['cycles']) > 0,
                'business_rules_summary': formula_context['summary']
            },
            'key_formulas': self._extract_key_formulas(formula_context),
            'data_validation_rules': sheet_context.get('data_validation', {}),
            'conditional_formats': sheet_context.get('conditional_formatting', {})
        }

        return enhanced_context

    def _enhance_query_with_formula_context(self, query: str, formula_context: Dict[str, Any]) -> str:
        """Enhance user query with formula context hints."""

        enhancements = []

        # Add formula category hints
        categories = self._count_categories(formula_context['classifications'])
        if categories:
            top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
            enhancements.append(f"Spreadsheet contains formulas in categories: {', '.join(f'{cat} ({count})' for cat, count in top_categories)}")

        # Add dependency complexity hint
        dep_analysis = formula_context['dependency_analysis']
        if dep_analysis['num_edges'] > 50:
            enhancements.append("Complex dependency network detected - consider formula relationships in analysis")

        # Add cycle warning
        if dep_analysis['cycles']:
            enhancements.append(f"Warning: {len(dep_analysis['cycles'])} circular reference(s) detected")

        if enhancements:
            enhanced_query = f"{query}\n\nFormula Context:\n" + "\n".join(f"- {enh}" for enh in enhancements)
            return enhanced_query

        return query

    def _build_formula_context_string(self, formula_context: Dict[str, Any]) -> str:
        """Build detailed formula context string for AI prompts."""

        context_parts = []

        # Business rules summary
        summary = formula_context['summary']
        context_parts.append(f"Spreadsheet Analysis: {summary}")

        # Key formulas
        key_formulas = self._extract_key_formulas(formula_context)
        if key_formulas:
            context_parts.append("\nKey Formulas:")
            for formula_info in key_formulas[:5]:  # Limit to top 5
                context_parts.append(f"- {formula_info['cell']}: {formula_info['formula']} ({formula_info['category']})")

        # Dependency insights
        dep_analysis = formula_context['dependency_analysis']
        context_parts.append(f"\nDependency Network: {dep_analysis['num_nodes']} cells, {dep_analysis['num_edges']} relationships")
        if dep_analysis['cycles']:
            context_parts.append(f"⚠️  {len(dep_analysis['cycles'])} circular reference(s) detected")

        return "\n".join(context_parts)

    async def _handle_what_if_simulation(self, query: str, sheet_context: Dict[str, Any],
                                       formula_context: Dict[str, Any], query_type: str) -> Any:
        """Handle what-if scenario analysis using formula dependency graph."""

        # Parse what-if parameters from query
        what_if_params = self._parse_what_if_parameters(query)

        # Create simulator with dependency graph and formula contexts
        dependency_graph = formula_context['dependencies']
        formula_contexts = formula_context['formula_contexts']

        simulator = WhatIfSimulator(dependency_graph, formula_contexts)

        # Simulate changes through dependency graph
        simulation_results = self._simulate_formula_changes(
            what_if_params, simulator, sheet_context
        )

        # Build what-if prompt
        what_if_prompt = self._build_what_if_prompt(query, what_if_params, simulation_results, formula_context)

        # Process with enhanced context
        return await self.base.process_construction_query(
            query=what_if_prompt,
            context=self._build_formula_context_string(formula_context),
            data_context={
                'simulation_results': simulation_results,
                'original_values': sheet_context.get('raw_values', {}),
                'what_if_parameters': what_if_params
            },
            query_type=f"what_if_{query_type}"
        )

    def _parse_what_if_parameters(self, query: str) -> Dict[str, Any]:
        """Parse what-if parameters from natural language query."""

        import re

        params = {
            'changes': [],
            'target_cells': [],
            'assumptions': [],
            'scenario_type': 'value_change'
        }

        query_lower = query.lower()

        # Look for cell references (e.g., A1, B2:C10, Sheet1!A1)
        cell_pattern = r'([A-Za-z]+\d+(?::[A-Za-z]+\d+)?|[\w\s]+![A-Za-z]+\d+)'
        cells_found = re.findall(cell_pattern, query)

        # Look for value changes (numbers, percentages)
        value_pattern = r'(\d+(?:\.\d+)?%?|\$\d+(?:,\d{3})*(?:\.\d{2})?)'
        values_found = re.findall(value_pattern, query)

        # Simple heuristic: if we find cells and values, assume value changes
        if cells_found and values_found:
            # Pair cells with values (simplified - assumes order corresponds)
            num_pairs = min(len(cells_found), len(values_found))
            for i in range(num_pairs):
                cell = cells_found[i].strip()
                value = values_found[i]

                # Convert percentage strings to decimal if needed
                if '%' in value:
                    try:
                        numeric_value = float(value.rstrip('%')) / 100
                    except ValueError:
                        numeric_value = value
                else:
                    try:
                        numeric_value = float(value.replace('$', '').replace(',', ''))
                    except ValueError:
                        numeric_value = value

                params['changes'].append((cell, numeric_value))
                params['target_cells'].append(cell)

        # Look for scenario keywords
        if any(word in query_lower for word in ['budget', 'cost', 'price']):
            params['scenario_type'] = 'budget_change'
        elif any(word in query_lower for word in ['schedule', 'timeline', 'date', 'delay']):
            params['scenario_type'] = 'timeline_shift'
        elif any(word in query_lower for word in ['resource', 'staff', 'team']):
            params['scenario_type'] = 'resource_change'

        # Extract assumptions from query
        if 'assuming' in query_lower or 'assume' in query_lower:
            # Simple extraction - could be enhanced
            assumption_part = query_lower.split('assuming')[1].split('.')[0] if 'assuming' in query_lower else ''
            if assumption_part:
                params['assumptions'].append(assumption_part.strip())

        return params

    def _simulate_formula_changes(self, what_if_params: Dict[str, Any],
                                simulator: WhatIfSimulator,
                                sheet_context: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate the impact of formula changes through dependency graph."""

        # Extract changes from parameters
        changes = what_if_params.get('changes', [])
        original_values = sheet_context.get('raw_values', {})

        if not changes:
            # No specific changes defined, return basic simulation structure
            return {
                'affected_cells': [],
                'impact_chain': [],
                'confidence_level': 'low',
                'assumptions': ['No specific changes defined in query'],
                'simulation_report': 'No changes to simulate'
            }

        # Run simulation
        try:
            simulation_result = simulator.simulate_value_change(changes, original_values)

            # Convert to dictionary format for AI processing
            return {
                'affected_cells': list(simulation_result.affected_cells),
                'impact_chain': simulation_result.impact_chain,
                'confidence_level': 'high' if simulation_result.confidence_score > 0.8 else 'medium',
                'confidence_score': simulation_result.confidence_score,
                'assumptions': simulation_result.assumptions,
                'warnings': simulation_result.warnings,
                'simulation_report': simulator.generate_simulation_report(simulation_result),
                'original_values': simulation_result.original_values,
                'changed_values': simulation_result.changed_values
            }

        except Exception as e:
            self.logger.error(f"Simulation failed: {e}")
            return {
                'affected_cells': [],
                'impact_chain': [],
                'confidence_level': 'low',
                'assumptions': [f'Simulation failed: {str(e)}'],
                'warnings': ['Unable to complete simulation due to error'],
                'simulation_report': f'Error during simulation: {str(e)}'
            }

    def _build_what_if_prompt(self, original_query: str, what_if_params: Dict[str, Any],
                            simulation_results: Dict[str, Any], formula_context: Dict[str, Any]) -> str:
        """Build enhanced prompt for what-if analysis."""

        prompt_parts = [
            f"WHAT-IF ANALYSIS REQUEST: {original_query}",
            "",
            "FORMULA DEPENDENCY CONTEXT:",
            f"- Total formulas: {len(formula_context['formulas'])}",
            f"- Dependency relationships: {formula_context['dependency_analysis']['num_edges']}",
            f"- Affected cells in simulation: {len(simulation_results['affected_cells'])}",
            "",
            "ASSUMPTIONS:",
        ]

        for assumption in simulation_results['assumptions']:
            prompt_parts.append(f"- {assumption}")

        prompt_parts.extend([
            "",
            "INSTRUCTIONS:",
            "1. Analyze how the proposed changes would propagate through the formula network",
            "2. Identify potential risks and downstream impacts",
            "3. Suggest mitigation strategies for identified risks",
            "4. Provide confidence level in the simulation results",
            "",
            "Please provide a comprehensive what-if analysis considering the formula dependencies and business logic."
        ])

        return "\n".join(prompt_parts)

    def _is_what_if_query(self, query: str) -> bool:
        """Determine if query is asking for what-if analysis."""

        what_if_indicators = [
            'what if', 'what-if', 'if i change', 'if we modify',
            'suppose', 'assuming', 'scenario', 'impact of',
            'effect of', 'consequence of'
        ]

        query_lower = query.lower()
        return any(indicator in query_lower for indicator in what_if_indicators)

    def _count_categories(self, classifications: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
        """Count formulas by category."""

        counts = {}
        for classification in classifications.values():
            category = classification['category']
            counts[category] = counts.get(category, 0) + 1

        return counts

    def _extract_key_formulas(self, formula_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract most important formulas for context."""

        formulas = formula_context['formulas']
        classifications = formula_context['classifications']

        # Score formulas by importance
        scored_formulas = []
        for cell, formula in formulas.items():
            classification = classifications.get(cell, {})
            category = classification.get('category', 'unknown')

            # Scoring logic (simplified)
            score = 0
            if category in ['aggregation', 'financial', 'logical']:
                score += 2
            if len(formula_context['dependencies'].get(cell, [])) > 5:  # High dependency count
                score += 1

            scored_formulas.append({
                'cell': cell,
                'formula': formula,
                'category': category,
                'score': score,
                'dependencies': len(formula_context['dependencies'].get(cell, []))
            })

        # Return top formulas by score
        return sorted(scored_formulas, key=lambda x: x['score'], reverse=True)[:10]

    def _generate_formula_summary(self, classifications: Dict[str, Dict[str, Any]],
                                dependency_analysis: Dict[str, Any]) -> str:
        """Generate human-readable summary of formula analysis."""

        total_formulas = len(classifications)
        categories = self._count_categories(classifications)

        summary_parts = [f"{total_formulas} formulas analyzed"]

        if categories:
            top_category = max(categories.items(), key=lambda x: x[1])
            summary_parts.append(f"primarily {top_category[0]} functions")

        if dependency_analysis['cycles']:
            summary_parts.append(f"⚠️ {len(dependency_analysis['cycles'])} circular references")

        return ", ".join(summary_parts)
