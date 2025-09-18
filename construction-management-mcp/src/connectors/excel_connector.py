"""
Excel Connector for Construction Management MCP

Handles reading and processing Excel files from OneDrive containing
construction project data, budgets, schedules, and resource information.
"""

import os
import json
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path
import tempfile

import msal
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential
from office365.sharepoint.files.file import File


class ExcelConnector:
    """Connector for accessing Excel files in OneDrive/SharePoint"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Excel connector with Microsoft 365 credentials
        
        Args:
            config: Configuration dictionary with Azure app credentials
        """
        self.config = config
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.tenant_id = config['tenant_id']
        self.sharepoint_site = config['sharepoint_site']
        self.onedrive_folder = config.get('onedrive_folder', '/Construction Projects')
        self.excel_files = config.get('excel_files', {})
        
        # Cache for Excel data
        self._data_cache = {}
        self._cache_expiry = {}
        
        # Initialize authentication
        self._init_auth()
    
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
            raise Exception(f"Failed to initialize authentication: {str(e)}")
    
    def _get_access_token(self):
        """Get access token for Microsoft Graph API"""
        scopes = ["https://graph.microsoft.com/.default"]
        
        result = self.app.acquire_token_for_client(scopes=scopes)
        
        if "access_token" in result:
            self.access_token = result["access_token"]
        else:
            raise Exception(f"Failed to acquire token: {result.get('error_description', 'Unknown error')}")
    
    def _get_sharepoint_context(self):
        """Get SharePoint client context"""
        try:
            # Use the access token to create SharePoint context
            ctx = ClientContext(self.sharepoint_site)
            ctx.with_access_token(self.access_token)
            return ctx
        except Exception as e:
            raise Exception(f"Failed to create SharePoint context: {str(e)}")
    
    def download_excel_file(self, file_name: str, local_path: Optional[str] = None) -> str:
        """
        Download Excel file from OneDrive/SharePoint
        
        Args:
            file_name: Name of the Excel file to download
            local_path: Local path to save file (if None, uses temp directory)
        
        Returns:
            Path to downloaded file
        """
        try:
            ctx = self._get_sharepoint_context()
            
            # Construct file URL
            file_url = f"{self.onedrive_folder}/{file_name}"
            
            # Get file from SharePoint
            file_obj = ctx.web.get_file_by_server_relative_url(file_url)
            
            # Download file content
            if local_path is None:
                # Use temporary directory
                temp_dir = tempfile.gettempdir()
                local_path = os.path.join(temp_dir, file_name)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Download file
            with open(local_path, 'wb') as local_file:
                file_obj.download(local_file)
                ctx.execute_query()
            
            return local_path
            
        except Exception as e:
            raise Exception(f"Failed to download Excel file {file_name}: {str(e)}")
    
    def read_excel_file(self, file_type: str, sheet_name: Optional[str] = None, force_refresh: bool = False) -> pd.DataFrame:
        """
        Read Excel file data into DataFrame
        
        Args:
            file_type: Type of Excel file (projects, budgets, schedules, resources)
            sheet_name: Specific sheet to read (if None, reads first sheet)
            force_refresh: Force download fresh copy from OneDrive
        
        Returns:
            DataFrame with Excel data
        """
        if file_type not in self.excel_files:
            raise ValueError(f"Unknown file type: {file_type}. Available types: {list(self.excel_files.keys())}")
        
        file_name = self.excel_files[file_type]
        cache_key = f"{file_type}_{sheet_name or 'default'}"
        
        # Check cache first (unless force refresh)
        if not force_refresh and cache_key in self._data_cache:
            return self._data_cache[cache_key]
        
        try:
            # Download file
            local_path = self.download_excel_file(file_name)
            
            # Read Excel file
            if sheet_name:
                df = pd.read_excel(local_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(local_path)
            
            # Cache the data
            self._data_cache[cache_key] = df
            
            # Clean up temporary file
            if local_path.startswith(tempfile.gettempdir()):
                os.remove(local_path)
            
            return df
            
        except Exception as e:
            raise Exception(f"Failed to read Excel file {file_name}: {str(e)}")
    
    def get_project_data(self, project_id: Optional[str] = None) -> pd.DataFrame:
        """
        Get project data from projects Excel file
        
        Args:
            project_id: Specific project ID to filter (if None, returns all)
        
        Returns:
            DataFrame with project information
        """
        df = self.read_excel_file('projects')
        
        if project_id:
            # Assume project ID is in a column named 'ProjectID', 'ID', or 'Project_ID'
            id_columns = ['ProjectID', 'ID', 'Project_ID', 'project_id']
            id_column = None
            
            for col in id_columns:
                if col in df.columns:
                    id_column = col
                    break
            
            if id_column:
                df = df[df[id_column] == project_id]
            else:
                raise ValueError("Could not find project ID column in projects file")
        
        return df
    
    def get_budget_data(self, project_id: Optional[str] = None) -> pd.DataFrame:
        """
        Get budget data from budgets Excel file
        
        Args:
            project_id: Specific project ID to filter
        
        Returns:
            DataFrame with budget information
        """
        df = self.read_excel_file('budgets')
        
        if project_id:
            # Filter by project ID
            project_columns = ['ProjectID', 'Project_ID', 'project_id', 'Project']
            project_column = None
            
            for col in project_columns:
                if col in df.columns:
                    project_column = col
                    break
            
            if project_column:
                df = df[df[project_column] == project_id]
        
        return df
    
    def get_schedule_data(self, project_id: Optional[str] = None) -> pd.DataFrame:
        """
        Get schedule data from schedules Excel file
        
        Args:
            project_id: Specific project ID to filter
        
        Returns:
            DataFrame with schedule information
        """
        df = self.read_excel_file('schedules')
        
        if project_id:
            # Filter by project ID
            project_columns = ['ProjectID', 'Project_ID', 'project_id', 'Project']
            project_column = None
            
            for col in project_columns:
                if col in df.columns:
                    project_column = col
                    break
            
            if project_column:
                df = df[df[project_column] == project_id]
        
        return df
    
    def get_resource_data(self, project_id: Optional[str] = None) -> pd.DataFrame:
        """
        Get resource allocation data from resources Excel file
        
        Args:
            project_id: Specific project ID to filter
        
        Returns:
            DataFrame with resource information
        """
        df = self.read_excel_file('resources')
        
        if project_id:
            # Filter by project ID
            project_columns = ['ProjectID', 'Project_ID', 'project_id', 'Project']
            project_column = None
            
            for col in project_columns:
                if col in df.columns:
                    project_column = col
                    break
            
            if project_column:
                df = df[df[project_column] == project_id]
        
        return df
    
    def search_projects_by_criteria(self, criteria: Dict[str, Any]) -> pd.DataFrame:
        """
        Search projects based on multiple criteria
        
        Args:
            criteria: Dictionary of search criteria (status, budget_range, manager, etc.)
        
        Returns:
            DataFrame with matching projects
        """
        df = self.get_project_data()
        
        # Apply filters based on criteria
        for field, value in criteria.items():
            if field in df.columns:
                if isinstance(value, dict):
                    # Handle range queries (e.g., budget_range: {"min": 100000, "max": 500000})
                    if 'min' in value and 'max' in value:
                        df = df[(df[field] >= value['min']) & (df[field] <= value['max'])]
                    elif 'min' in value:
                        df = df[df[field] >= value['min']]
                    elif 'max' in value:
                        df = df[df[field] <= value['max']]
                elif isinstance(value, list):
                    # Handle multiple values (e.g., status: ["Active", "In Progress"])
                    df = df[df[field].isin(value)]
                else:
                    # Handle exact match
                    df = df[df[field] == value]
        
        return df
    
    def get_projects_over_budget(self, threshold_percent: float = 0.0) -> pd.DataFrame:
        """
        Get projects that are over budget by specified threshold
        
        Args:
            threshold_percent: Minimum percentage over budget (0.0 = any amount over)
        
        Returns:
            DataFrame with over-budget projects
        """
        # Get project and budget data
        projects_df = self.get_project_data()
        budget_df = self.get_budget_data()
        
        # Merge project and budget data
        # Assuming both have a common project identifier
        merged_df = pd.merge(projects_df, budget_df, on='ProjectID', how='inner')
        
        # Calculate budget variance
        if 'BudgetAllocated' in merged_df.columns and 'BudgetSpent' in merged_df.columns:
            merged_df['BudgetVariance'] = (merged_df['BudgetSpent'] - merged_df['BudgetAllocated']) / merged_df['BudgetAllocated'] * 100
            
            # Filter over-budget projects
            over_budget = merged_df[merged_df['BudgetVariance'] > threshold_percent]
            return over_budget
        else:
            raise ValueError("Budget columns not found in data")
    
    def get_delayed_projects(self, days_threshold: int = 0) -> pd.DataFrame:
        """
        Get projects that are delayed beyond threshold
        
        Args:
            days_threshold: Minimum days delayed (0 = any delay)
        
        Returns:
            DataFrame with delayed projects
        """
        # Get project and schedule data
        projects_df = self.get_project_data()
        schedule_df = self.get_schedule_data()
        
        # Merge data
        merged_df = pd.merge(projects_df, schedule_df, on='ProjectID', how='inner')
        
        # Calculate delays (assuming we have planned and actual dates)
        if 'PlannedEndDate' in merged_df.columns and 'ActualEndDate' in merged_df.columns:
            merged_df['PlannedEndDate'] = pd.to_datetime(merged_df['PlannedEndDate'])
            merged_df['ActualEndDate'] = pd.to_datetime(merged_df['ActualEndDate'])
            
            # Calculate delay in days
            merged_df['DelayDays'] = (merged_df['ActualEndDate'] - merged_df['PlannedEndDate']).dt.days
            
            # Filter delayed projects
            delayed = merged_df[merged_df['DelayDays'] > days_threshold]
            return delayed
        else:
            raise ValueError("Date columns not found in schedule data")
    
    def clear_cache(self):
        """Clear cached Excel data"""
        self._data_cache.clear()
        self._cache_expiry.clear()
    
    def list_available_files(self) -> List[str]:
        """
        List available Excel files in OneDrive folder
        
        Returns:
            List of Excel file names
        """
        try:
            ctx = self._get_sharepoint_context()
            
            # Get folder
            folder = ctx.web.get_folder_by_server_relative_url(self.onedrive_folder)
            files = folder.files
            ctx.load(files)
            ctx.execute_query()
            
            excel_files = []
            for file in files:
                if file.name.endswith(('.xlsx', '.xls')):
                    excel_files.append(file.name)
            
            return excel_files
            
        except Exception as e:
            raise Exception(f"Failed to list files: {str(e)}")