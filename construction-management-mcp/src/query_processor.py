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
from construction_prompts import get_construction_prompt, enhance_query_with_construction_context


class QueryProcessor:
    """Processes natural language queries and routes to appropriate data sources"""
    
    def __init__(self, excel_connector: ExcelConnector, 
                 sharepoint_connector: SharePointConnector,
                 document_indexer: DocumentIndexer):
        """
        Initialize query processor with data connectors
        
        Args:
            excel_connector: Excel data connector
            sharepoint_connector: SharePoint lists connector
            document_indexer: Document search and indexing
        """
        self.excel_connector = excel_connector
        self.sharepoint_connector = sharepoint_connector
        self.document_indexer = document_indexer
        
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
        
        # Build search criteria
        criteria = {}
        
        if filters:
            criteria.update(filters)
        
        # Add parameters from query
        if 'status' in params:
            criteria['Status'] = params['status'].title()
        
        if 'budget_filter' in params:
            if params['budget_filter'] == 'over':
                # Use Excel connector to find over-budget projects
                return self._format_projects(self.excel_connector.get_projects_over_budget())
            elif params['budget_filter'] == 'under':
                # Custom logic for under-budget projects
                pass
        
        # Search in Excel data
        try:
            if criteria:
                projects_df = self.excel_connector.search_projects_by_criteria(criteria)
            else:
                projects_df = self.excel_connector.get_project_data()
            
            return self._format_projects(projects_df)
        except Exception as e:
            # Fallback to SharePoint
            try:
                project_id = params.get('project_id')
                return self.sharepoint_connector.get_projects_list(project_id=project_id)
            except Exception as sp_error:
                raise Exception(f"Failed to search projects: Excel error: {str(e)}, SharePoint error: {str(sp_error)}")
    
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
            # Get project data from Excel
            project_df = self.excel_connector.get_project_data(project_id)
            if not project_df.empty:
                project_data = project_df.iloc[0].to_dict()
                status.update({
                    'name': project_data.get('ProjectName', project_data.get('Name', 'Unknown')),
                    'status': project_data.get('Status', 'Unknown'),
                    'progress': project_data.get('Progress', 0),
                    'manager': project_data.get('ProjectManager', 'Unassigned')
                })
            
            # Get budget status
            budget_df = self.excel_connector.get_budget_data(project_id)
            if not budget_df.empty:
                budget_data = budget_df.iloc[0].to_dict()
                allocated = budget_data.get('BudgetAllocated', 0)
                spent = budget_data.get('BudgetSpent', 0)
                if allocated > 0:
                    variance = (spent - allocated) / allocated * 100
                    if variance > 10:
                        status['budget_status'] = f'Over Budget ({variance:+.1f}%)'
                    elif variance < -10:
                        status['budget_status'] = f'Under Budget ({variance:+.1f}%)'
                    else:
                        status['budget_status'] = 'On Budget'
            
            # Get schedule status from SharePoint
            tasks = self.sharepoint_connector.get_tasks_list(project_id=project_id)
            if tasks:
                overdue_tasks = 0
                total_tasks = len(tasks)
                completed_tasks = 0
                
                for task in tasks:
                    if task.get('Status') == 'Completed':
                        completed_tasks += 1
                    elif task.get('DueDate'):
                        due_date = datetime.fromisoformat(task['DueDate'].replace('Z', '+00:00'))
                        if due_date < datetime.now() and task.get('Status') != 'Completed':
                            overdue_tasks += 1
                
                if overdue_tasks > 0:
                    status['schedule_status'] = f'{overdue_tasks} Overdue Tasks'
                else:
                    status['schedule_status'] = 'On Schedule'
                
                status['progress'] = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Get health metrics
            status['health_metrics'] = self.sharepoint_connector.get_project_health_metrics(project_id)
            
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
            # Get budget data
            budget_df = self.excel_connector.get_budget_data(project_id)
            
            if not budget_df.empty:
                analysis['total_budget'] = budget_df['BudgetAllocated'].sum()
                analysis['spent'] = budget_df['BudgetSpent'].sum()
                analysis['remaining'] = analysis['total_budget'] - analysis['spent']
                
                if analysis['total_budget'] > 0:
                    analysis['variance_percent'] = (analysis['spent'] - analysis['total_budget']) / analysis['total_budget'] * 100
                
                # Find over/under budget projects
                for _, row in budget_df.iterrows():
                    if row['BudgetAllocated'] > 0:
                        variance = (row['BudgetSpent'] - row['BudgetAllocated']) / row['BudgetAllocated'] * 100
                        
                        project_info = {
                            'name': row.get('ProjectName', row.get('ProjectID', 'Unknown')),
                            'variance': variance,
                            'allocated': row['BudgetAllocated'],
                            'spent': row['BudgetSpent']
                        }
                        
                        if variance > 5:  # More than 5% over budget
                            analysis['over_budget_projects'].append(project_info)
                        elif variance < -5:  # More than 5% under budget
                            analysis['under_budget_projects'].append(project_info)
        
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
            # Get all projects to check schedules
            projects_df = self.excel_connector.get_project_data()
            
            end_date = datetime.now() + timedelta(days=days_ahead)
            
            for _, project in projects_df.iterrows():
                project_id = project.get('ProjectID', project.get('ID'))
                
                # Get tasks from SharePoint
                tasks = self.sharepoint_connector.get_tasks_list(project_id=project_id)
                
                for task in tasks:
                    if task.get('DueDate'):
                        due_date = datetime.fromisoformat(task['DueDate'].replace('Z', '+00:00'))
                        
                        # Check for upcoming milestones
                        if datetime.now() <= due_date <= end_date:
                            updates['upcoming_milestones'].append({
                                'project': project.get('ProjectName', project_id),
                                'name': task.get('Title', 'Unknown Task'),
                                'date': due_date.strftime('%Y-%m-%d'),
                                'type': task.get('TaskType', 'Task')
                            })
                        
                        # Check for overdue tasks
                        elif due_date < datetime.now() and task.get('Status') != 'Completed':
                            days_overdue = (datetime.now() - due_date).days
                            updates['overdue_tasks'].append({
                                'project': project.get('ProjectName', project_id),
                                'name': task.get('Title', 'Unknown Task'),
                                'days_overdue': days_overdue,
                                'due_date': due_date.strftime('%Y-%m-%d')
                            })
            
            # Check for delayed projects
            delayed_df = self.excel_connector.get_delayed_projects()
            for _, project in delayed_df.iterrows():
                updates['delayed_projects'].append({
                    'name': project.get('ProjectName', 'Unknown'),
                    'delay_days': project.get('DelayDays', 0),
                    'original_end': project.get('PlannedEndDate'),
                    'current_end': project.get('ActualEndDate')
                })
        
        except Exception as e:
            updates['error'] = f"Error getting schedule updates: {str(e)}"
        
        return updates
    
    def generate_report(self, report_type: str, project_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Generate various construction management reports
        
        Args:
            report_type: Type of report to generate
            project_id: Specific project (optional)
            **kwargs: Additional parameters
        
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
                    projects_df = self.excel_connector.get_project_data()
                    report['content'] = self._format_all_projects_status(projects_df)
            
            elif report_type.lower() == 'budget':
                analysis = self.analyze_budget(project_id)
                report['content'] = self._format_budget_report(analysis)
            
            elif report_type.lower() == 'safety':
                incidents = self.sharepoint_connector.get_safety_incidents(project_id=project_id)
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
            results['sharepoint_results'] = self.sharepoint_connector.search_across_lists(search_term)
            
            # Search in documents
            results['document_results'] = self.document_indexer.search_documents(search_term)
            
            # Search in Excel data (basic text search in project names, descriptions)
            projects_df = self.excel_connector.get_project_data()
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
    
    # Helper formatting methods
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
            content += f"• {project.get('ProjectName', 'Unknown')}: {project.get('Status', 'Unknown')} ({project.get('Progress', 0)}%)\n"
        
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