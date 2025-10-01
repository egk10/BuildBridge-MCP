"""
Query Processor for Construction Management MCP

Natural language processing component that understands construction management 
queries and routes them to appropriate data sources (Excel files, SharePoint lists).
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd

from connectors.excel_connector import ExcelConnector
from connectors.sharepoint_connector import SharePointConnector
from connectors.document_indexer import DocumentIndexer
from connectors.google_sheets_connector import GoogleSheetsConnector
from schema_discovery import SchemaDiscovery
from construction_prompts import get_construction_prompt, enhance_query_with_construction_context


class QueryProcessor:
    """Processes natural language queries and routes to appropriate data sources"""
    
    def __init__(self, excel_connector: Optional[ExcelConnector],
                 sharepoint_connector: Optional[SharePointConnector],
                 document_indexer: Optional[DocumentIndexer],
                 google_sheets_connector: Optional[GoogleSheetsConnector],
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize query processor with data connectors
        
        Args:
            excel_connector: Excel data connector
            sharepoint_connector: SharePoint lists connector
            document_indexer: Document search and indexing
            google_sheets_connector: Google Sheets data connector
            config: Configuration dictionary
        """
        self.excel_connector = excel_connector
        self.sharepoint_connector = sharepoint_connector
        self.document_indexer = document_indexer
        self.google_sheets_connector = google_sheets_connector
        self.config = config or {}
        
        # Initialize schema discovery
        self.schema_discovery = SchemaDiscovery(self.config)
        
        # Define query patterns and keywords
        self.query_patterns = self._init_query_patterns()
        self.construction_keywords = self._init_construction_keywords()
    
    def _init_query_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize natural language query patterns"""
        return {
            'project_search': {
                'patterns': [
                    r'(show|list|find|get)\s+(.*?)projects?\s*(that|which|where)?\s*(.*?)$',
                    r'projects?\s*(that|which|where)\s+(.*?)$',
                    r'(what|which)\s+projects?\s+(.*?)$'
                ],
                'keywords': ['project', 'projects', 'show', 'list', 'find'],
                'data_source': 'excel',
                'method': 'search_projects'
            },
            'project_status': {
                'patterns': [
                    r'(status|progress)\s+of\s+(project\s+)?(.+?)$',
                    r'(what.s|how.s)\s+the\s+(status|progress)\s+of\s+(.+?)$',
                    r'project\s+(.+?)\s+(status|progress)$'
                ],
                'keywords': ['status', 'progress', 'project'],
                'data_source': 'both',
                'method': 'get_project_status'
            },
            'budget_analysis': {
                'patterns': [
                    r'(budget|cost|expense|spending)\s+(analysis|report|summary).*?$',
                    r'(show|analyze)\s+(budget|costs|expenses).*?$',
                    r'(projects?)\s*(that\s+are\s+)?(over|under)\s+budget$',
                    r'budget\s+(variance|performance).*?$'
                ],
                'keywords': ['budget', 'cost', 'expense', 'over budget', 'under budget'],
                'data_source': 'excel',
                'method': 'analyze_budget'
            },
            'schedule_query': {
                'patterns': [
                    r'(schedule|timeline|milestone|deadline).*?$',
                    r'(when|what)\s+(is|are)\s+the\s+(next|upcoming).*?$',
                    r'(delayed|behind\s+schedule|overdue).*?$'
                ],
                'keywords': ['schedule', 'timeline', 'milestone', 'deadline', 'delayed'],
                'data_source': 'both',
                'method': 'get_schedule_updates'
            },
            'safety_query': {
                'patterns': [
                    r'safety\s+(incident|report|issue).*?$',
                    r'(accident|injury|incident).*?$'
                ],
                'keywords': ['safety', 'incident', 'accident', 'injury'],
                'data_source': 'sharepoint',
                'method': 'get_safety_incidents'
            },
            'subcontractor_query': {
                'patterns': [
                    r'(subcontractor|contractor|vendor).*?$',
                    r'(who|which)\s+(is|are)\s+working\s+on.*?$'
                ],
                'keywords': ['subcontractor', 'contractor', 'vendor'],
                'data_source': 'sharepoint',
                'method': 'get_subcontractors'
            },
            'document_search': {
                'patterns': [
                    r'(document|file|drawing|spec|specification).*?$',
                    r'(find|search|locate)\s+(.*?)\s+(document|file|drawing).*?$'
                ],
                'keywords': ['document', 'file', 'drawing', 'specification'],
                'data_source': 'documents',
                'method': 'search_documents'
            }
        }
    
    def _init_construction_keywords(self) -> Dict[str, List[str]]:
        """Initialize construction management specific keywords"""
        return {
            'status_keywords': ['active', 'in progress', 'completed', 'on hold', 'delayed', 'cancelled'],
            'budget_keywords': ['over budget', 'under budget', 'on budget', 'variance', 'cost overrun'],
            'project_types': ['residential', 'commercial', 'infrastructure', 'renovation', 'new construction'],
            'roles': ['project manager', 'foreman', 'superintendent', 'engineer', 'architect'],
            'time_periods': ['this month', 'this quarter', 'this year', 'last month', 'next month']
        }
    
    def parse_query(self, query: str) -> Dict[str, Any]:
        """
        Parse natural language query to determine intent and parameters
        
        Args:
            query: Natural language query string
        
        Returns:
            Dictionary with query type, parameters, and data source
        """
        query_lower = query.lower().strip()
        
        # Enhance query with construction context
        enhanced_query = enhance_query_with_construction_context(query)
        
        # Check each query pattern
        for query_type, config in self.query_patterns.items():
            for pattern in config['patterns']:
                match = re.search(pattern, query_lower)
                if match:
                    # Extract parameters from the query
                    params = self._extract_parameters(query_lower, match)
                    
                    return {
                        'type': query_type,
                        'method': config['method'],
                        'data_source': config['data_source'],
                        'parameters': params,
                        'original_query': query,
                        'enhanced_query': enhanced_query,
                        'construction_prompt': get_construction_prompt(query_type)
                    }
        
        # Default to general search if no pattern matches
        return {
            'type': 'general_search',
            'method': 'general_search',
            'data_source': 'both',
            'parameters': {'search_term': query},
            'original_query': query,
            'enhanced_query': enhanced_query,
            'construction_prompt': get_construction_prompt('general')
        }
    
    def _extract_parameters(self, query: str, match: re.Match) -> Dict[str, Any]:
        """Extract parameters from query based on regex match"""
        params = {}
        
        # Extract project ID if mentioned
        project_id_match = re.search(r'project\s+([A-Za-z0-9-]+)', query)
        if project_id_match:
            params['project_id'] = project_id_match.group(1)
        
        # Extract status filters
        for status in self.construction_keywords['status_keywords']:
            if status in query:
                params['status'] = status
                break
        
        # Extract time periods
        for period in self.construction_keywords['time_periods']:
            if period in query:
                params['time_period'] = period
                break
        
        # Extract budget-related filters
        if 'over budget' in query:
            params['budget_filter'] = 'over'
        elif 'under budget' in query:
            params['budget_filter'] = 'under'
        
        # Extract numeric values (budgets, percentages, etc.)
        numbers = re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', query)
        if numbers:
            params['numbers'] = [float(n.replace(',', '')) for n in numbers]
        
        return params
    
    def search_projects(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for projects based on natural language query
        
        Args:
            query: Natural language query
            filters: Additional filters
        
        Returns:
            List of matching projects
        """
        parsed = self.parse_query(query)
        params = parsed['parameters']
        
        # Try multiple data sources in priority order
        all_results = []
        
        # 1. Try Excel/OneDrive
        try:
            excel_results = self._search_projects_excel(params, filters)
            if excel_results:
                all_results.extend(excel_results)
        except Exception as e:
            print(f"Warning: Excel search failed: {e}")
        
        # 2. Try Google Sheets
        try:
            sheets_results = self._search_projects_google_sheets(params, filters)
            if sheets_results:
                all_results.extend(sheets_results)
        except Exception as e:
            print(f"Warning: Google Sheets search failed: {e}")
        
        # 3. Try SharePoint
        try:
            sp_results = self._search_projects_sharepoint(params, filters)
            if sp_results:
                all_results.extend(sp_results)
        except Exception as e:
            print(f"Warning: SharePoint search failed: {e}")
        
    def _search_projects_excel(self, params: Dict[str, Any], filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search projects in Excel/OneDrive data"""
        if not self.excel_connector:
            return []
        criteria = filters.copy() if filters else {}
        
        # Add parameters from query
        if 'status' in params:
            criteria['Status'] = params['status'].title()
        
        if 'budget_filter' in params:
            if params['budget_filter'] == 'over':
                return self._format_projects(self.excel_connector.get_projects_over_budget())
            elif params['budget_filter'] == 'under':
                # Custom logic for under-budget projects could be added here
                pass
        
        # Search in Excel data
        if criteria:
            projects_df = self.excel_connector.search_projects_by_criteria(criteria)
        else:
            projects_df = self.excel_connector.get_project_data()
        
        return self._format_projects(projects_df)
    
    def _search_projects_google_sheets(self, params: Dict[str, Any], filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search projects in Google Sheets data"""
        if not self.google_sheets_connector:
            return []
        criteria = filters.copy() if filters else {}
        
        # Add parameters from query
        if 'status' in params:
            criteria['Status'] = params['status'].title()
        
        if 'budget_filter' in params:
            if params['budget_filter'] == 'over':
                return self._format_projects(self.google_sheets_connector.get_projects_over_budget())
        
        # Search in Google Sheets data
        if criteria:
            projects_df = self.google_sheets_connector.search_projects_by_criteria(criteria)
        else:
            projects_df = self.google_sheets_connector.get_project_data()
        
        return self._format_projects(projects_df)
    
    def _search_projects_sharepoint(self, params: Dict[str, Any], filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search projects in SharePoint data"""
        if not self.sharepoint_connector:
            return []
        project_id = params.get('project_id')
        return self.sharepoint_connector.get_projects_list(project_id=project_id)
    
    def _deduplicate_results(self, results: List[Dict[str, Any]], id_field: str) -> List[Dict[str, Any]]:
        """Remove duplicate results based on ID field"""
        seen_ids = set()
        unique_results = []
        
        for result in results:
            result_id = result.get(id_field) or result.get(id_field.lower()) or result.get('id')
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
            elif not result_id:
                # If no ID, include it anyway (can't deduplicate)
                unique_results.append(result)
        
        return unique_results
    
    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """
        Get detailed status for a specific project
        
        Args:
            project_id: Project identifier
        
        Returns:
            Detailed project status
        """
        status = {
            'id': project_id,
            'name': 'Unknown Project',
            'status': 'Unknown',
            'progress': 0,
            'budget_status': 'Unknown',
            'schedule_status': 'Unknown',
            'milestones': [],
            'health_metrics': {}
        }

        try:
            project_df = self._get_project_dataframe(project_id)
            if not project_df.empty:
                project_data = project_df.iloc[0].to_dict()
                status.update({
                    'name': project_data.get('ProjectName') or project_data.get('Name', 'Unknown'),
                    'status': project_data.get('Status', 'Unknown'),
                    'progress': project_data.get('Progress', 0) or 0,
                    'manager': project_data.get('ProjectManager', project_data.get('Manager', 'Unassigned'))
                })

            budget_df = self._get_budget_dataframe(project_id)
            if not budget_df.empty:
                budget_data = budget_df.iloc[0].to_dict()
                allocated = float(budget_data.get('BudgetAllocated') or 0)
                spent = float(budget_data.get('BudgetSpent') or 0)
                if allocated > 0:
                    variance = (spent - allocated) / allocated * 100
                    if variance > 10:
                        status['budget_status'] = f'Over Budget ({variance:+.1f}%)'
                    elif variance < -10:
                        status['budget_status'] = f'Under Budget ({variance:+.1f}%)'
                    else:
                        status['budget_status'] = 'On Budget'
                elif allocated == 0 and spent == 0:
                    status['budget_status'] = 'No Budget Data'

            tasks = self._get_schedule_tasks(project_id)
            if tasks:
                overdue_tasks = 0
                completed_tasks = 0
                total_tasks = len(tasks)
                upcoming_milestones: List[Dict[str, Any]] = []

                for task in tasks:
                    status_value = (task.get('Status') or '').lower()
                    if status_value in {'completed', 'done', 'closed'}:
                        completed_tasks += 1

                    due_value = task.get('DueDate')
                    due_date = self._parse_due_date_value(due_value)
                    if due_date:
                        if due_date < datetime.now() and status_value not in {'completed', 'done', 'closed'}:
                            overdue_tasks += 1
                        elif due_date >= datetime.now():
                            upcoming_milestones.append({
                                'name': task.get('Title') or task.get('Name', 'Task'),
                                'date': due_date.strftime('%Y-%m-%d'),
                                'type': task.get('TaskType') or task.get('Type', 'Task')
                            })

                if overdue_tasks > 0:
                    status['schedule_status'] = f'{overdue_tasks} Overdue Tasks'
                elif total_tasks > 0:
                    status['schedule_status'] = 'On Schedule'
                else:
                    status['schedule_status'] = 'Schedule data unavailable'

                status['progress'] = (completed_tasks / total_tasks * 100) if total_tasks > 0 else status['progress']
                status['milestones'] = upcoming_milestones[:5]
            else:
                status['schedule_status'] = 'Schedule data unavailable'

            if self.sharepoint_connector:
                status['health_metrics'] = self.sharepoint_connector.get_project_health_metrics(project_id)
            elif self.google_sheets_connector:
                status['health_metrics'] = {
                    'source': 'google_sheets',
                    'message': 'SharePoint connector disabled; health metrics not available.'
                }

        except Exception as e:
            status['error'] = f"Error retrieving project status: {str(e)}"

        return status
    
    def analyze_budget(self, project_id: Optional[str] = None, period: str = "current_month") -> Dict[str, Any]:
        """
        Analyze budget performance
        
        Args:
            project_id: Specific project (if None, analyzes all)
            period: Time period for analysis
        
        Returns:
            Budget analysis results
        """
        analysis = {
            'period': period,
            'total_budget': 0,
            'spent': 0,
            'remaining': 0,
            'variance_percent': 0,
            'over_budget_projects': [],
            'under_budget_projects': []
        }
        
        try:
            budget_df = self._get_budget_dataframe(project_id)

            if not budget_df.empty and 'BudgetAllocated' in budget_df.columns and 'BudgetSpent' in budget_df.columns:
                analysis['total_budget'] = float(budget_df['BudgetAllocated'].sum())
                analysis['spent'] = float(budget_df['BudgetSpent'].sum())
                analysis['remaining'] = analysis['total_budget'] - analysis['spent']

                if analysis['total_budget'] > 0:
                    analysis['variance_percent'] = (analysis['spent'] - analysis['total_budget']) / analysis['total_budget'] * 100

                for _, row in budget_df.iterrows():
                    allocated = float(row.get('BudgetAllocated') or 0)
                    spent = float(row.get('BudgetSpent') or 0)
                    if allocated > 0:
                        variance = (spent - allocated) / allocated * 100

                        project_info = {
                            'name': row.get('ProjectName') or row.get('ProjectID', 'Unknown'),
                            'variance': variance,
                            'allocated': allocated,
                            'spent': spent
                        }

                        if variance > 5:
                            analysis['over_budget_projects'].append(project_info)
                        elif variance < -5:
                            analysis['under_budget_projects'].append(project_info)
            else:
                analysis['message'] = 'No budget data available from configured sources.'

        except Exception as e:
            analysis['error'] = f"Error analyzing budget: {str(e)}"
        
        return analysis
    
    def get_schedule_updates(self, days_ahead: int = 30) -> Dict[str, Any]:
        """
        Get schedule updates and upcoming milestones
        
        Args:
            days_ahead: Number of days to look ahead
        
        Returns:
            Schedule updates and alerts
        """
        updates = {
            'period': f'Next {days_ahead} days',
            'upcoming_milestones': [],
            'delayed_projects': [],
            'overdue_tasks': []
        }
        
        try:
            projects_df = self._get_project_dataframe()
            end_date = datetime.now() + timedelta(days=days_ahead)

            if projects_df.empty:
                updates['message'] = 'No project schedule data available from configured sources.'
                return updates

            for _, project in projects_df.iterrows():
                project_id = project.get('ProjectID') or project.get('ID') or project.get('Project_Name')
                if not project_id:
                    continue

                tasks = self._get_schedule_tasks(project_id)

                for task in tasks:
                    due_value = task.get('DueDate')
                    due_date = self._parse_due_date_value(due_value)
                    if not due_date:
                        continue

                    if datetime.now() <= due_date <= end_date:
                        updates['upcoming_milestones'].append({
                            'project': project.get('ProjectName') or project.get('Project_Name', project_id),
                            'name': task.get('Title', 'Unknown Task'),
                            'date': due_date.strftime('%Y-%m-%d'),
                            'type': task.get('TaskType') or task.get('Type', 'Task')
                        })
                    elif due_date < datetime.now() and (task.get('Status') or '').lower() not in {'completed', 'done', 'closed'}:
                        days_overdue = (datetime.now() - due_date).days
                        updates['overdue_tasks'].append({
                            'project': project.get('ProjectName') or project.get('Project_Name', project_id),
                            'name': task.get('Title', 'Unknown Task'),
                            'days_overdue': days_overdue,
                            'due_date': due_date.strftime('%Y-%m-%d')
                        })

            delayed_df = pd.DataFrame()
            if self.excel_connector:
                delayed_df = self.excel_connector.get_delayed_projects()
            elif self.google_sheets_connector:
                try:
                    delayed_df = self.google_sheets_connector.get_delayed_projects()
                except Exception:
                    delayed_df = pd.DataFrame()

            if not delayed_df.empty:
                for _, project in delayed_df.iterrows():
                    updates['delayed_projects'].append({
                        'name': project.get('ProjectName') or project.get('Project_Name', 'Unknown'),
                        'delay_days': project.get('DelayDays', 0),
                        'original_end': project.get('PlannedEndDate') or project.get('Planned Finish'),
                        'current_end': project.get('ActualEndDate') or project.get('Actual Finish')
                    })

        except Exception as e:
            updates['error'] = f"Error getting schedule updates: {str(e)}"
        
        return updates
    
    def generate_report(self, report_type: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate various construction management reports
        
        Args:
            report_type: Type of report to generate
            project_id: Specific project (optional)
        
        Returns:
            Generated report data
        """
        report = {
            'title': f'{report_type.title()} Report',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'project_id': project_id,
            'content': ''
        }
        
        try:
            if report_type.lower() == 'status':
                if project_id:
                    status = self.get_project_status(project_id)
                    report['content'] = self._format_status_report(status)
                else:
                    # All projects status
                    projects_df = self._get_project_dataframe()
                    report['content'] = self._format_all_projects_status(projects_df)
            
            elif report_type.lower() == 'budget':
                analysis = self.analyze_budget(project_id)
                report['content'] = self._format_budget_report(analysis)
            
            elif report_type.lower() == 'safety':
                if self.sharepoint_connector:
                    incidents = self.sharepoint_connector.get_safety_incidents(project_id=project_id)
                else:
                    incidents = []
                report['content'] = self._format_safety_report(incidents)
            
            elif report_type.lower() == 'compliance':
                # Custom compliance report logic
                report['content'] = self._format_compliance_report(project_id)
            
            else:
                report['content'] = f"Report type '{report_type}' not implemented yet."
        
        except Exception as e:
            report['content'] = f"Error generating {report_type} report: {str(e)}"
        
        return report
    
    def general_search(self, search_term: str) -> Dict[str, Any]:
        """
        Perform general search across all data sources
        
        Args:
            search_term: Term to search for
        
        Returns:
            Search results from all sources
        """
        results = {
            'search_term': search_term,
            'excel_results': {},
            'sharepoint_results': {},
            'document_results': []
        }
        
        try:
            # Search in SharePoint lists
            if self.sharepoint_connector:
                results['sharepoint_results'] = self.sharepoint_connector.search_across_lists(search_term)
            else:
                results['sharepoint_results'] = {}
            
            # Search in documents
            if self.document_indexer:
                results['document_results'] = self.document_indexer.search_documents(search_term)
            else:
                results['document_results'] = []
            
            # Search in Excel data (basic text search in project names, descriptions)
            projects_df = self._get_project_dataframe()
            matching_projects = []
            
            for _, project in projects_df.iterrows():
                project_text = ' '.join([str(v) for v in project.values if pd.notna(v)])
                if search_term.lower() in project_text.lower():
                    matching_projects.append(project.to_dict())
            
            results['excel_results']['projects'] = matching_projects
        
        except Exception as e:
            results['error'] = f"Error in general search: {str(e)}"
        
        return results
    
    def enhance_response_with_construction_context(self, response: str, query_type: str, context_data: Dict[str, Any] = None) -> str:
        """
        Enhance AI responses with construction-specific context and terminology
        
        Args:
            response: Original response from AI/data source
            query_type: Type of construction query
            context_data: Additional context data
        
        Returns:
            Enhanced response with construction context
        """
        # Get construction-specific prompt for this query type
        construction_prompt = get_construction_prompt(query_type, context_data)
        
        # Add construction context to the response
        enhanced_response = f"{response}\n\n**Construction Context:**\n"
        
        # Add relevant construction terminology based on query type
        if query_type == "budget_analysis":
            enhanced_response += "- Budget variance analysis follows Earned Value Management (EVM) principles\n"
            enhanced_response += "- Cost overruns often result from change orders, material price increases, or unforeseen conditions\n"
            enhanced_response += "- Consider contingency reserves and escalation clauses in contracts\n"
        
        elif query_type == "safety_compliance":
            enhanced_response += "- Safety protocols must comply with OSHA standards and local regulations\n"
            enhanced_response += "- Regular safety training and PPE requirements are mandatory\n"
            enhanced_response += "- Incident reporting and investigation follow specific protocols\n"
        
        elif query_type == "schedule_management":
            enhanced_response += "- Schedule management uses Critical Path Method (CPM) for analysis\n"
            enhanced_response += "- Weather delays and material shortages are common risk factors\n"
            enhanced_response += "- Recovery plans may include schedule compression or resource reallocation\n"
        
        elif query_type == "project_status":
            enhanced_response += "- Project progress is measured using Planned Value vs Earned Value\n"
            enhanced_response += "- Milestone completion affects payment schedules and client reporting\n"
            enhanced_response += "- Risk assessment should consider safety, quality, and budget factors\n"
        
        else:
            enhanced_response += "- Construction projects follow standardized phases and methodologies\n"
            enhanced_response += "- Industry standards (OSHA, PMI, AGC) guide best practices\n"
            enhanced_response += "- Risk management is essential for project success\n"
        
        return enhanced_response

    def _get_project_dataframe(self, project_id: Optional[str] = None) -> pd.DataFrame:
        """Fetch project data from available connectors and normalize columns."""
        frames: List[pd.DataFrame] = []

        if self.excel_connector:
            try:
                df = self.excel_connector.get_project_data(project_id)
                if not df.empty:
                    frames.append(self._normalize_project_dataframe(df, source='excel'))
            except Exception as exc:
                print(f"Warning: Excel project data unavailable: {exc}")

        if self.google_sheets_connector:
            try:
                df = self.google_sheets_connector.get_project_data(project_id)
                if not df.empty:
                    frames.append(self._normalize_project_dataframe(df, source='google_sheets'))
            except Exception as exc:
                print(f"Warning: Google Sheets project data unavailable: {exc}")

        if frames:
            return pd.concat(frames, ignore_index=True, sort=False)

        return pd.DataFrame()

    def _normalize_project_dataframe(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """Normalize project DataFrame column names."""
        normalized = df.copy()

        rename_map = {
            'Project_ID': 'ProjectID',
            'project_id': 'ProjectID',
            'Project_Name': 'ProjectName',
            'Project_Manager': 'ProjectManager',
            'Manager': 'ProjectManager',
            'Progress_Percent': 'Progress',
            'ProgressPercent': 'Progress'
        }

        rename_dict = {}
        for old, new in rename_map.items():
            if old in normalized.columns and new not in normalized.columns:
                rename_dict[old] = new
        if rename_dict:
            normalized = normalized.rename(columns=rename_dict)

        if 'Progress' in normalized.columns:
            normalized['Progress'] = pd.to_numeric(normalized['Progress'], errors='coerce').fillna(0).clip(lower=0, upper=100)

        normalized['Source'] = source

        return normalized

    def _get_budget_dataframe(self, project_id: Optional[str] = None) -> pd.DataFrame:
        """Fetch budget data from available connectors and normalize columns."""
        frames: List[pd.DataFrame] = []

        if self.excel_connector:
            try:
                df = self.excel_connector.get_budget_data(project_id)
                if not df.empty:
                    frames.append(self._normalize_budget_dataframe(df, source='excel'))
            except Exception as exc:
                print(f"Warning: Excel budget data unavailable: {exc}")

        if self.google_sheets_connector:
            try:
                df = self.google_sheets_connector.get_budget_data(project_id)
                if not df.empty:
                    frames.append(self._normalize_budget_dataframe(df, source='google_sheets'))
            except Exception as exc:
                print(f"Warning: Google Sheets budget data unavailable: {exc}")

        if frames:
            return pd.concat(frames, ignore_index=True, sort=False)

        return pd.DataFrame()

    def _normalize_budget_dataframe(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """Normalize budget DataFrame column names."""
        normalized = df.copy()

        rename_map = {
            'Project_ID': 'ProjectID',
            'project_id': 'ProjectID',
            'Project': 'ProjectID',
            'Project_Name': 'ProjectName',
            'ProjectName': 'ProjectName',
            'Budget': 'BudgetAllocated',
            'Total_Budget': 'BudgetAllocated',
            'PlannedBudget': 'BudgetAllocated',
            'ActualSpend': 'BudgetSpent',
            'Spent': 'BudgetSpent',
            'Actual_Cost': 'BudgetSpent'
        }

        rename_dict = {}
        for old, new in rename_map.items():
            if old in normalized.columns and new not in normalized.columns:
                rename_dict[old] = new

        if rename_dict:
            normalized = normalized.rename(columns=rename_dict)

        for col in ['BudgetAllocated', 'BudgetSpent']:
            if col in normalized.columns:
                normalized[col] = pd.to_numeric(normalized[col], errors='coerce').fillna(0.0)

        normalized['Source'] = source

        return normalized

    def _get_schedule_tasks(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch schedule tasks from available connectors."""
        tasks: List[Dict[str, Any]] = []

        if self.sharepoint_connector:
            try:
                sharepoint_tasks = self.sharepoint_connector.get_tasks_list(project_id=project_id) or []
                tasks.extend(sharepoint_tasks)
            except Exception as exc:
                print(f"Warning: SharePoint schedule unavailable: {exc}")

        if tasks:
            return tasks

        if self.google_sheets_connector:
            try:
                schedule_df = self.google_sheets_connector.get_schedule_data(project_id)
                tasks.extend(self._convert_schedule_df_to_tasks(schedule_df))
            except Exception as exc:
                print(f"Warning: Google Sheets schedule unavailable: {exc}")

        return tasks

    def _convert_schedule_df_to_tasks(self, schedule_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert Google Sheets schedule DataFrame into task dictionaries."""
        tasks: List[Dict[str, Any]] = []

        if schedule_df.empty:
            return tasks

        name_columns = ['TaskName', 'Task', 'Milestone', 'Activity', 'Name']
        status_columns = ['Status', 'TaskStatus', 'Completion']
        due_columns = ['DueDate', 'Due Date', 'PlannedFinish', 'Planned Finish', 'EndDate', 'Target Date']
        type_columns = ['TaskType', 'Type', 'Category']

        for _, row in schedule_df.iterrows():
            task: Dict[str, Any] = {}

            name = None
            for col in name_columns:
                if col in schedule_df.columns:
                    value = row.get(col)
                    if pd.notna(value) and str(value).strip():
                        name = str(value).strip()
                        break
            task['Title'] = name or 'Task'

            status_value = None
            for col in status_columns:
                if col in schedule_df.columns:
                    value = row.get(col)
                    if pd.notna(value) and str(value).strip():
                        status_value = str(value).strip()
                        break
            if status_value:
                task['Status'] = status_value

            due_value = None
            for col in due_columns:
                if col in schedule_df.columns:
                    value = row.get(col)
                    if pd.notna(value) and str(value).strip():
                        due_value = str(value).strip()
                        break
            if due_value:
                parsed_due = self._parse_due_date_value(due_value)
                if parsed_due:
                    task['DueDate'] = parsed_due.isoformat()

            task_type = None
            for col in type_columns:
                if col in schedule_df.columns:
                    value = row.get(col)
                    if pd.notna(value) and str(value).strip():
                        task_type = str(value).strip()
                        break
            if task_type:
                task['TaskType'] = task_type

            tasks.append(task)

        return tasks

    def _parse_due_date_value(self, due_value: Any) -> Optional[datetime]:
        """Parse due date values into datetime objects."""
        if isinstance(due_value, datetime):
            return due_value

        if due_value is None or (isinstance(due_value, str) and not due_value.strip()):
            return None

        try:
            parsed = pd.to_datetime(due_value, errors='coerce')
            if pd.isna(parsed):
                return None
            parsed_dt = parsed.to_pydatetime() if hasattr(parsed, 'to_pydatetime') else parsed
            if parsed_dt.tzinfo:
                parsed_dt = parsed_dt.replace(tzinfo=None)
            return parsed_dt
        except Exception:
            return None
    
    def _format_projects(self, projects_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Format projects DataFrame as list of dictionaries"""
        if projects_df.empty:
            return []
        
        return projects_df.to_dict('records')
    
    def _format_status_report(self, status: Dict[str, Any]) -> str:
        """Format project status as report text"""
        content = f"Project: {status['name']}\n"
        content += f"Status: {status['status']}\n"
        content += f"Progress: {status['progress']}%\n"
        content += f"Budget Status: {status['budget_status']}\n"
        content += f"Schedule Status: {status['schedule_status']}\n"
        
        if status['milestones']:
            content += "\nUpcoming Milestones:\n"
            for milestone in status['milestones'][:5]:
                content += f"- {milestone['name']}: {milestone['date']}\n"
        
        return content
    
    def _format_all_projects_status(self, projects_df: pd.DataFrame) -> str:
        """Format status report for all projects"""
        if projects_df.empty:
            return "No projects found."
        
        content = f"Status Report for {len(projects_df)} Projects:\n\n"
        
        for _, project in projects_df.iterrows():
            name = project.get('ProjectName') or project.get('Project_Name') or project.get('Name', 'Unknown')
            status = project.get('Status', 'Unknown')
            progress = project.get('Progress') or project.get('Progress_Percent') or 0
            content += f"• {name}: {status} ({progress}%)\n"
        
        return content
    
    def _format_budget_report(self, analysis: Dict[str, Any]) -> str:
        """Format budget analysis as report text"""
        content = f"Budget Analysis - {analysis['period']}\n\n"
        content += f"Total Budget: ${analysis['total_budget']:,.2f}\n"
        content += f"Spent to Date: ${analysis['spent']:,.2f}\n"
        content += f"Remaining: ${analysis['remaining']:,.2f}\n"
        content += f"Overall Variance: {analysis['variance_percent']:+.1f}%\n\n"
        
        if analysis['over_budget_projects']:
            content += "Projects Over Budget:\n"
            for project in analysis['over_budget_projects']:
                content += f"- {project['name']}: {project['variance']:+.1f}%\n"
        
        return content
    
    def _format_safety_report(self, incidents: List[Dict[str, Any]]) -> str:
        """Format safety incidents as report text"""
        if not incidents:
            return "Safety data not available. SharePoint connector is disabled."

        content = f"Safety Report - {len(incidents)} Incidents\n\n"

        for incident in incidents:
            content += f"• {incident.get('Title', 'Unknown Incident')}\n"
            content += f"  Date: {incident.get('IncidentDate', 'Unknown')}\n"
            content += f"  Severity: {incident.get('Severity', 'Unknown')}\n"
            content += f"  Status: {incident.get('Status', 'Unknown')}\n\n"

        return content
    
    def _format_compliance_report(self, project_id: Optional[str]) -> str:
        """Format compliance report"""
        return "Compliance report functionality to be implemented based on specific requirements."