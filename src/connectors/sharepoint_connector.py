"""
SharePoint Connector for Construction Management MCP

Handles accessing SharePoint Lists containing construction project data,
tasks, safety incidents, subcontractor information, and other list-based data.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

import msal
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.lists.list import List as SPList
from office365.sharepoint.listitems.listitem import ListItem


class SharePointConnector:
    """Connector for accessing SharePoint Lists"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SharePoint connector with Microsoft 365 credentials
        
        Args:
            config: Configuration dictionary with Azure app credentials
        """
        self.config = config
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.tenant_id = config['tenant_id']
        self.sharepoint_site = config['sharepoint_site']
        self.sharepoint_lists = config.get('sharepoint_lists', {})
        
        # Local mode toggle
        self.local_mode = bool(
            config.get('local_mode') or
            self.sharepoint_site in ('local-test', 'local', '')
        )

        # Cache for list data
        self._list_cache = {}
        self._cache_expiry = {}
        self._cache_duration = timedelta(minutes=15)  # Cache for 15 minutes
        
        # Initialize authentication only if NOT in local mode
        if not self.local_mode:
            self._init_auth()
        else:
            # In local mode, set dummy values to avoid attribute errors
            self.app = None
            self.access_token = None
    
    def _init_auth(self):
        """Initialize Microsoft Graph authentication"""
        try:
            # Create MSAL app for authentication
            self.app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )
            
            # Get access token
            self._get_access_token()
            
        except Exception as e:
            raise Exception(f"Failed to initialize SharePoint authentication: {str(e)}")
    
    def _get_access_token(self):
        """Get access token for SharePoint API"""
        scopes = [f"{self.sharepoint_site}/.default"]
        
        result = self.app.acquire_token_for_client(scopes=scopes)
        
        if "access_token" in result:
            self.access_token = result["access_token"]
        else:
            raise Exception(f"Failed to acquire SharePoint token: {result.get('error_description', 'Unknown error')}")
    
    def _get_sharepoint_context(self):
        """Get SharePoint client context"""
        try:
            ctx = ClientContext(self.sharepoint_site)
            ctx.with_access_token(self.access_token)
            return ctx
        except Exception as e:
            raise Exception(f"Failed to create SharePoint context: {str(e)}")
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry[cache_key]
    
    def get_list_items(self, list_name: str, fields: Optional[List[str]] = None, 
                      filter_query: Optional[str] = None, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get items from a SharePoint list
        
        Args:
            list_name: Name of the SharePoint list
            fields: Specific fields to retrieve (if None, gets all fields)
            filter_query: OData filter query for filtering results
            force_refresh: Force refresh from SharePoint (ignore cache)
        
        Returns:
            List of dictionaries containing list item data
        """
        cache_key = f"{list_name}_{filter_query or 'all'}"
        
        # Check cache first
        if not force_refresh and self._is_cache_valid(cache_key) and cache_key in self._list_cache:
            return self._list_cache[cache_key]
        
        try:
            if self.local_mode:
                # Return an empty list or simple mocked data in local mode
                items: List[Dict[str, Any]] = []
                self._list_cache[cache_key] = items
                self._cache_expiry[cache_key] = datetime.now() + self._cache_duration
                return items
            ctx = self._get_sharepoint_context()
            
            # Get the list
            target_list = ctx.web.lists.get_by_title(list_name)
            
            # Build query
            query = target_list.items
            
            if filter_query:
                query = query.filter(filter_query)
            
            if fields:
                query = query.select(fields)
            
            # Execute query
            ctx.load(query)
            ctx.execute_query()
            
            # Convert to list of dictionaries
            items = []
            for item in query:
                item_dict = {}
                for field_name in item.properties:
                    item_dict[field_name] = item.properties[field_name]
                items.append(item_dict)
            
            # Cache the results
            self._list_cache[cache_key] = items
            self._cache_expiry[cache_key] = datetime.now() + self._cache_duration
            
            return items
            
        except Exception as e:
            raise Exception(f"Failed to get items from list {list_name}: {str(e)}")
    
    def get_projects_list(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get projects from SharePoint Projects list
        
        Args:
            project_id: Specific project ID to filter
        
        Returns:
            List of project dictionaries
        """
        list_name = self.sharepoint_lists.get('projects', 'Projects')
        
        filter_query = None
        if project_id:
            filter_query = f"ProjectID eq '{project_id}'"
        
        return self.get_list_items(list_name, filter_query=filter_query)
    
    def get_tasks_list(self, project_id: Optional[str] = None, 
                      status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get tasks from SharePoint Tasks list
        
        Args:
            project_id: Filter by specific project
            status: Filter by task status
        
        Returns:
            List of task dictionaries
        """
        list_name = self.sharepoint_lists.get('tasks', 'Tasks')
        
        filters = []
        if project_id:
            filters.append(f"ProjectID eq '{project_id}'")
        if status:
            filters.append(f"Status eq '{status}'")
        
        filter_query = ' and '.join(filters) if filters else None
        
        return self.get_list_items(list_name, filter_query=filter_query)
    
    def get_safety_incidents(self, project_id: Optional[str] = None, 
                           date_from: Optional[datetime] = None,
                           date_to: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get safety incidents from SharePoint Safety Incidents list
        
        Args:
            project_id: Filter by specific project
            date_from: Start date for incident search
            date_to: End date for incident search
        
        Returns:
            List of safety incident dictionaries
        """
        list_name = self.sharepoint_lists.get('safety_incidents', 'Safety Incidents')
        
        filters = []
        if project_id:
            filters.append(f"ProjectID eq '{project_id}'")
        if date_from:
            filters.append(f"IncidentDate ge datetime'{date_from.isoformat()}'")
        if date_to:
            filters.append(f"IncidentDate le datetime'{date_to.isoformat()}'")
        
        filter_query = ' and '.join(filters) if filters else None
        
        return self.get_list_items(list_name, filter_query=filter_query)
    
    def get_subcontractors(self, project_id: Optional[str] = None,
                          active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get subcontractors from SharePoint Subcontractors list
        
        Args:
            project_id: Filter by specific project
            active_only: Only return active subcontractors
        
        Returns:
            List of subcontractor dictionaries
        """
        list_name = self.sharepoint_lists.get('subcontractors', 'Subcontractors')
        
        filters = []
        if project_id:
            filters.append(f"ProjectID eq '{project_id}'")
        if active_only:
            filters.append("Status eq 'Active'")
        
        filter_query = ' and '.join(filters) if filters else None
        
        return self.get_list_items(list_name, filter_query=filter_query)
    
    def search_across_lists(self, search_term: str, list_names: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for a term across multiple SharePoint lists
        
        Args:
            search_term: Term to search for
            list_names: Specific lists to search (if None, searches all configured lists)
        
        Returns:
            Dictionary with list names as keys and matching items as values
        """
        if list_names is None:
            list_names = list(self.sharepoint_lists.values())
        
        results = {}
        
        for list_name in list_names:
            try:
                # Search in title and description fields (common fields)
                search_filter = f"substringof('{search_term}', Title) or substringof('{search_term}', Description)"
                items = self.get_list_items(list_name, filter_query=search_filter)
                
                if items:
                    results[list_name] = items
                    
            except Exception as e:
                # Continue with other lists if one fails
                print(f"Warning: Failed to search in list {list_name}: {str(e)}")
                continue
        
        return results
    
    def get_project_timeline(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get project timeline by combining tasks and milestones
        
        Args:
            project_id: Project identifier
        
        Returns:
            List of timeline events sorted by date
        """
        # Get tasks for the project
        tasks = [] if self.local_mode else self.get_tasks_list(project_id=project_id)
        
        timeline = []
        
        for task in tasks:
            timeline_item = {
                'type': 'task',
                'title': task.get('Title', 'Unknown Task'),
                'start_date': task.get('StartDate'),
                'end_date': task.get('DueDate'),
                'status': task.get('Status'),
                'assigned_to': task.get('AssignedTo'),
                'project_id': project_id
            }
            timeline.append(timeline_item)
        
        # Sort by start date
        timeline.sort(key=lambda x: x.get('start_date', datetime.min))
        
        return timeline
    
    def get_project_health_metrics(self, project_id: str) -> Dict[str, Any]:
        """
        Calculate project health metrics from SharePoint data
        
        Args:
            project_id: Project identifier
        
        Returns:
            Dictionary with health metrics
        """
        metrics = {
            'project_id': project_id,
            'task_completion_rate': 0,
            'safety_incidents_count': 0,
            'active_subcontractors_count': 0,
            'overdue_tasks_count': 0
        }
        
        try:
            # Get tasks
            tasks = [] if self.local_mode else self.get_tasks_list(project_id=project_id)
            if tasks:
                completed_tasks = [t for t in tasks if t.get('Status') == 'Completed']
                metrics['task_completion_rate'] = len(completed_tasks) / len(tasks) * 100
                
                # Count overdue tasks
                today = datetime.now()
                overdue_tasks = [t for t in tasks if t.get('DueDate') and 
                               datetime.fromisoformat(t['DueDate'].replace('Z', '+00:00')) < today and 
                               t.get('Status') != 'Completed']
                metrics['overdue_tasks_count'] = len(overdue_tasks)
            
            # Get safety incidents
            safety_incidents = self.get_safety_incidents(project_id=project_id)
            metrics['safety_incidents_count'] = len(safety_incidents)
            
            # Get active subcontractors
            subcontractors = self.get_subcontractors(project_id=project_id, active_only=True)
            metrics['active_subcontractors_count'] = len(subcontractors)
            
        except Exception as e:
            print(f"Warning: Error calculating metrics for project {project_id}: {str(e)}")
        
        return metrics
    
    def create_list_item(self, list_name: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new item in a SharePoint list
        
        Args:
            list_name: Name of the SharePoint list
            item_data: Dictionary of field values for the new item
        
        Returns:
            Created item data
        """
        try:
            ctx = self._get_sharepoint_context()
            
            # Get the list
            target_list = ctx.web.lists.get_by_title(list_name)
            
            # Create new item
            new_item = target_list.add_item(item_data)
            ctx.execute_query()
            
            # Clear cache for this list
            cache_keys_to_remove = [key for key in self._list_cache.keys() if key.startswith(list_name)]
            for key in cache_keys_to_remove:
                del self._list_cache[key]
                if key in self._cache_expiry:
                    del self._cache_expiry[key]
            
            return new_item.properties
            
        except Exception as e:
            raise Exception(f"Failed to create item in list {list_name}: {str(e)}")
    
    def update_list_item(self, list_name: str, item_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing item in a SharePoint list
        
        Args:
            list_name: Name of the SharePoint list
            item_id: ID of the item to update
            item_data: Dictionary of field values to update
        
        Returns:
            Updated item data
        """
        try:
            ctx = self._get_sharepoint_context()
            
            # Get the list and item
            target_list = ctx.web.lists.get_by_title(list_name)
            item = target_list.get_item_by_id(item_id)
            
            # Update item
            item.update(item_data)
            ctx.execute_query()
            
            # Clear cache for this list
            cache_keys_to_remove = [key for key in self._list_cache.keys() if key.startswith(list_name)]
            for key in cache_keys_to_remove:
                del self._list_cache[key]
                if key in self._cache_expiry:
                    del self._cache_expiry[key]
            
            return item.properties
            
        except Exception as e:
            raise Exception(f"Failed to update item {item_id} in list {list_name}: {str(e)}")
    
    def get_list_schema(self, list_name: str) -> Dict[str, Any]:
        """
        Get the schema (field definitions) for a SharePoint list
        
        Args:
            list_name: Name of the SharePoint list
        
        Returns:
            Dictionary with field definitions
        """
        try:
            ctx = self._get_sharepoint_context()
            
            # Get the list
            target_list = ctx.web.lists.get_by_title(list_name)
            fields = target_list.fields
            ctx.load(fields)
            ctx.execute_query()
            
            schema = {}
            for field in fields:
                schema[field.internal_name] = {
                    'title': field.title,
                    'type': field.field_type_kind,
                    'required': field.required,
                    'description': field.description
                }
            
            return schema
            
        except Exception as e:
            raise Exception(f"Failed to get schema for list {list_name}: {str(e)}")
    
    def clear_cache(self):
        """Clear all cached list data"""
        self._list_cache.clear()
        self._cache_expiry.clear()
    
    def list_available_lists(self) -> List[Dict[str, str]]:
        """
        List all available SharePoint lists in the site
        
        Returns:
            List of dictionaries with list information
        """
        try:
            ctx = self._get_sharepoint_context()
            
            lists = ctx.web.lists
            ctx.load(lists)
            ctx.execute_query()
            
            list_info = []
            for sp_list in lists:
                if not sp_list.hidden:  # Only show non-hidden lists
                    list_info.append({
                        'title': sp_list.title,
                        'description': sp_list.description,
                        'item_count': sp_list.item_count,
                        'id': sp_list.id
                    })
            
            return list_info
            
        except Exception as e:
            raise Exception(f"Failed to list SharePoint lists: {str(e)}")