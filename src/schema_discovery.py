"""
Schema Discovery Module for BuildBridge-MCP

Automatically discovers and maps data schemas from various sources
(Excel, Google Sheets, SharePoint) to enable flexible data integration.
"""

import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import re

from connectors.excel_connector import ExcelConnector
from connectors.google_sheets_connector import GoogleSheetsConnector
from connectors.sharepoint_connector import SharePointConnector


class SchemaDiscovery:
    """Handles automatic schema discovery and mapping for construction data"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize schema discovery with configuration

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.cache_dir = Path(__file__).parent.parent / "cache" / "schemas"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Schema cache with TTL
        self.schema_cache = {}
        self.cache_ttl = timedelta(hours=1)  # Cache schemas for 1 hour

        # Standard field mappings for construction data
        self.standard_mappings = self._load_standard_mappings()

        # Data type inference rules
        self.type_inference_rules = self._load_type_inference_rules()

    def _load_standard_mappings(self) -> Dict[str, Dict[str, List[str]]]:
        """Load standard field name mappings for construction data types"""
        return {
            'projects': {
                'id': ['projectid', 'id', 'project_id', 'project', 'proj_id', 'number'],
                'name': ['projectname', 'name', 'project_name', 'title', 'description'],
                'status': ['status', 'state', 'phase', 'stage'],
                'manager': ['manager', 'projectmanager', 'pm', 'project_manager'],
                'budget': ['budget', 'total_budget', 'allocated_budget', 'budget_allocated'],
                'start_date': ['startdate', 'start_date', 'planned_start', 'begin_date'],
                'end_date': ['enddate', 'end_date', 'planned_end', 'completion_date'],
                'progress': ['progress', 'percent_complete', 'completion', '%_complete']
            },
            'budgets': {
                'project_id': ['projectid', 'project_id', 'proj_id', 'project'],
                'allocated': ['allocated', 'budget_allocated', 'total_budget', 'budget'],
                'spent': ['spent', 'actual_spent', 'expended', 'cost_to_date'],
                'remaining': ['remaining', 'budget_remaining', 'leftover'],
                'variance': ['variance', 'budget_variance', 'over_under']
            },
            'schedules': {
                'project_id': ['projectid', 'project_id', 'proj_id', 'project'],
                'task': ['task', 'activity', 'work_package', 'description'],
                'start_date': ['startdate', 'start_date', 'planned_start', 'begin'],
                'end_date': ['enddate', 'end_date', 'planned_end', 'finish'],
                'duration': ['duration', 'days', 'weeks', 'effort'],
                'predecessor': ['predecessor', 'pred', 'depends_on'],
                'resource': ['resource', 'assigned_to', 'responsible']
            },
            'resources': {
                'project_id': ['projectid', 'project_id', 'proj_id', 'project'],
                'resource_type': ['type', 'resource_type', 'category', 'role'],
                'name': ['name', 'resource_name', 'person', 'equipment'],
                'allocation': ['allocation', 'assigned', 'utilization', 'hours'],
                'rate': ['rate', 'hourly_rate', 'cost_rate', 'daily_rate']
            }
        }

    def _load_type_inference_rules(self) -> Dict[str, str]:
        """Load rules for inferring data types from column names and values"""
        return {
            # Date patterns
            r'.*(date|time).*': 'datetime',
            r'.*(start|end).*': 'datetime',
            r'.*(created|modified).*': 'datetime',

            # Numeric patterns
            r'.*(budget|cost|price|amount|total).*': 'numeric',
            r'.*(percent|percentage|rate).*': 'numeric',
            r'.*(count|quantity|number).*': 'numeric',
            r'.*(id|number)$': 'string',  # IDs are strings even if numeric

            # Boolean patterns
            r'.*(active|enabled|complete|done).*': 'boolean',
            r'.*(yes|no|true|false).*': 'boolean'
        }

    def discover_schema(self, data_source: str, data_type: str,
                       connector: Any, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Discover schema for a specific data source and type

        Args:
            data_source: Source type ('excel', 'google_sheets', 'sharepoint')
            data_type: Data type ('projects', 'budgets', etc.)
            connector: Data connector instance
            force_refresh: Force schema rediscovery

        Returns:
            Schema dictionary with field mappings and metadata
        """
        cache_key = f"{data_source}_{data_type}"
        cache_file = self.cache_dir / f"{cache_key}.json"

        # Check cache first
        if not force_refresh and self._is_cache_valid(cache_key):
            return self.schema_cache[cache_key]

        # Discover schema based on data source
        if data_source == 'excel':
            schema = self._discover_excel_schema(connector, data_type)
        elif data_source == 'google_sheets':
            schema = self._discover_google_sheets_schema(connector, data_type)
        elif data_source == 'sharepoint':
            schema = self._discover_sharepoint_schema(connector, data_type)
        else:
            raise ValueError(f"Unsupported data source: {data_source}")

        # Apply standard mappings
        schema = self._apply_standard_mappings(schema, data_type)

        # Infer data types
        schema = self._infer_data_types(schema)

        # Cache the schema
        self.schema_cache[cache_key] = schema
        self._save_schema_to_cache(cache_key, schema)

        return schema

    def _discover_excel_schema(self, connector: ExcelConnector, data_type: str) -> Dict[str, Any]:
        """Discover schema from Excel data"""
        try:
            # Get sample data to analyze schema
            if data_type == 'projects':
                df = connector.get_project_data()
            elif data_type == 'budgets':
                df = connector.get_budget_data()
            elif data_type == 'schedules':
                df = connector.get_schedule_data()
            elif data_type == 'resources':
                df = connector.get_resource_data()
            else:
                raise ValueError(f"Unknown data type: {data_type}")

            return self._analyze_dataframe_schema(df, data_type)

        except Exception as e:
            # Return minimal schema on error
            return {
                'fields': {},
                'data_type': data_type,
                'source': 'excel',
                'error': str(e)
            }

    def _discover_google_sheets_schema(self, connector: GoogleSheetsConnector, data_type: str) -> Dict[str, Any]:
        """Discover schema from Google Sheets data"""
        try:
            # Get sample data to analyze schema
            if data_type == 'projects':
                df = connector.get_project_data()
            elif data_type == 'budgets':
                df = connector.get_budget_data()
            elif data_type == 'schedules':
                df = connector.get_schedule_data()
            elif data_type == 'resources':
                df = connector.get_resource_data()
            else:
                raise ValueError(f"Unknown data type: {data_type}")

            return self._analyze_dataframe_schema(df, data_type)

        except Exception as e:
            # Return minimal schema on error
            return {
                'fields': {},
                'data_type': data_type,
                'source': 'google_sheets',
                'error': str(e)
            }

    def _discover_sharepoint_schema(self, connector: SharePointConnector, data_type: str) -> Dict[str, Any]:
        """Discover schema from SharePoint list data"""
        try:
            # Get list schema
            list_name = connector.sharepoint_lists.get(data_type, data_type.title())
            schema_info = connector.get_list_schema(list_name)

            schema = {
                'fields': {},
                'data_type': data_type,
                'source': 'sharepoint',
                'list_name': list_name
            }

            # Convert SharePoint field info to our format
            for field_name, field_info in schema_info.items():
                schema['fields'][field_name] = {
                    'original_name': field_name,
                    'data_type': self._map_sharepoint_type(field_info['type']),
                    'required': field_info['required'],
                    'description': field_info.get('description', ''),
                    'sharepoint_type': field_info['type']
                }

            return schema

        except Exception as e:
            return {
                'fields': {},
                'data_type': data_type,
                'source': 'sharepoint',
                'error': str(e)
            }

    def _analyze_dataframe_schema(self, df: pd.DataFrame, data_type: str) -> Dict[str, Any]:
        """Analyze pandas DataFrame to extract schema information"""
        schema = {
            'fields': {},
            'data_type': data_type,
            'row_count': len(df),
            'column_count': len(df.columns)
        }

        for col in df.columns:
            # Analyze column data
            sample_values = df[col].dropna().head(10).tolist()
            pandas_dtype = str(df[col].dtype)

            field_info = {
                'original_name': col,
                'pandas_dtype': pandas_dtype,
                'sample_values': sample_values[:3],  # Store first 3 sample values
                'nullable': df[col].isnull().any(),
                'unique_count': df[col].nunique()
            }

            schema['fields'][col] = field_info

        return schema

    def _apply_standard_mappings(self, schema: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """Apply standard field name mappings to discovered schema"""
        if data_type not in self.standard_mappings:
            return schema

        standard_fields = self.standard_mappings[data_type]

        # Create mapping from original names to standard names
        for standard_name, possible_names in standard_fields.items():
            for original_name in schema['fields'].keys():
                original_lower = original_name.lower().replace('_', '').replace(' ', '')

                # Check if original name matches any possible standard names
                for possible in possible_names:
                    possible_clean = possible.lower().replace('_', '').replace(' ', '')

                    if original_lower == possible_clean or possible_clean in original_lower:
                        schema['fields'][original_name]['standard_name'] = standard_name
                        schema['fields'][original_name]['mapped'] = True
                        break

        return schema

    def _infer_data_types(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Infer data types for fields based on names and sample values"""
        for field_name, field_info in schema['fields'].items():
            inferred_type = self._infer_field_type(field_name, field_info)
            field_info['inferred_type'] = inferred_type

        return schema

    def _infer_field_type(self, field_name: str, field_info: Dict[str, Any]) -> str:
        """Infer data type for a single field"""
        field_name_lower = field_name.lower()

        # Check against type inference rules
        for pattern, data_type in self.type_inference_rules.items():
            if re.search(pattern, field_name_lower, re.IGNORECASE):
                return data_type

        # Check sample values for additional clues
        sample_values = field_info.get('sample_values', [])
        if sample_values:
            # Check if all values are numeric
            try:
                float_values = [float(str(v)) for v in sample_values if str(v).strip()]
                if len(float_values) == len(sample_values):
                    return 'numeric'
            except (ValueError, TypeError):
                pass

            # Check if values look like dates
            date_patterns = [
                r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
                r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
                r'\w{3}\s+\d{1,2},?\s+\d{4}'
            ]
            for pattern in date_patterns:
                if any(re.search(pattern, str(v)) for v in sample_values):
                    return 'datetime'

            # Check for boolean-like values
            bool_values = {'yes', 'no', 'true', 'false', '1', '0', 'on', 'off'}
            if all(str(v).lower() in bool_values for v in sample_values):
                return 'boolean'

        # Default to string
        return 'string'

    def _map_sharepoint_type(self, sp_type: int) -> str:
        """Map SharePoint field type numbers to our type system"""
        type_mapping = {
            2: 'string',      # Text
            3: 'string',      # Note (multi-line text)
            4: 'numeric',     # Number
            5: 'numeric',     # Currency
            6: 'datetime',    # DateTime
            7: 'boolean',     # Yes/No
            9: 'numeric',     # Percent
        }
        return type_mapping.get(sp_type, 'string')

    def get_field_mapping(self, data_source: str, data_type: str,
                         field_name: str) -> Optional[str]:
        """
        Get the standard field name mapping for a field

        Args:
            data_source: Data source type
            data_type: Data type (projects, budgets, etc.)
            field_name: Original field name

        Returns:
            Standard field name or None if not mapped
        """
        schema = self.discover_schema(data_source, data_type, None)
        field_info = schema['fields'].get(field_name, {})
        return field_info.get('standard_name')

    def validate_data_against_schema(self, data: Dict[str, Any],
                                   schema: Dict[str, Any]) -> List[str]:
        """
        Validate data against discovered schema

        Args:
            data: Data dictionary to validate
            schema: Schema to validate against

        Returns:
            List of validation errors
        """
        errors = []

        for field_name, field_info in schema['fields'].items():
            if field_info.get('required', False) and field_name not in data:
                errors.append(f"Required field '{field_name}' is missing")

            if field_name in data:
                value = data[field_name]
                expected_type = field_info.get('inferred_type', 'string')

                # Basic type validation
                if expected_type == 'numeric' and not isinstance(value, (int, float)):
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        errors.append(f"Field '{field_name}' should be numeric")

                elif expected_type == 'datetime':
                    # Could add datetime validation here
                    pass

                elif expected_type == 'boolean' and not isinstance(value, bool):
                    # Could add boolean validation here
                    pass

        return errors

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached schema is still valid"""
        if cache_key not in self.schema_cache:
            return False

        # For now, always consider cache valid (implement TTL later)
        return True


# --- Formula awareness scaffolding -------------------------------------------------

def detect_circular_references(dependencies_graph: Dict[str, List[str]]) -> List[List[str]]:
    """Return lists of nodes that participate in cycles (stub)."""
    # TODO: replace placeholder with networkx.simple_cycles logic in Phase 2.
    return []


def validate_dependencies_exist(
    dependencies_graph: Dict[str, List[str]],
    known_cells: Set[str],
) -> List[str]:
    """Return missing cell references detected in dependency graph (stub)."""
    # TODO: replace placeholder with set comparisons in Phase 2.
    return []

    def _save_schema_to_cache(self, cache_key: str, schema: Dict[str, Any]):
        """Save schema to file cache"""
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'schema': schema,
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0'
                }, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Failed to save schema cache: {e}")

    def clear_cache(self):
        """Clear all cached schemas"""
        self.schema_cache.clear()

        # Clear file cache
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
            except Exception as e:
                print(f"Warning: Failed to delete cache file {cache_file}: {e}")

    def get_schema_summary(self, data_source: str, data_type: str) -> Dict[str, Any]:
        """
        Get a summary of the discovered schema

        Args:
            data_source: Data source type
            data_type: Data type

        Returns:
            Schema summary with key statistics
        """
        schema = self.discover_schema(data_source, data_type, None)

        summary = {
            'data_type': data_type,
            'data_source': data_source,
            'total_fields': len(schema['fields']),
            'mapped_fields': sum(1 for f in schema['fields'].values() if f.get('mapped')),
            'data_types': {}
        }

        # Count data types
        for field_info in schema['fields'].values():
            data_type_count = field_info.get('inferred_type', 'unknown')
            summary['data_types'][data_type_count] = summary['data_types'].get(data_type_count, 0) + 1

        return summary