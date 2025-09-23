"""
Google Sheets Connector for Construction Management MCP

Handles reading and processing Google Sheets containing construction project data,
budgets, schedules, and resource information.
"""

import os
import json
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleSheetsConnector:
    """Connector for accessing Google Sheets"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Google Sheets connector with service account credentials

        Args:
            config: Configuration dictionary with Google API credentials
        """
        self.config = config
        self.service_account_file = config.get('google_service_account_file')
        self.google_sheets = config.get('google_sheets', {})
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']

        # Local mode toggle
        self.local_mode = bool(
            config.get('local_mode') or
            not self.service_account_file or
            not os.path.exists(self.service_account_file)
        )

        # Cache for sheet data
        self._data_cache = {}
        self._cache_expiry = {}
        self._cache_duration = timedelta(minutes=15)  # Cache for 15 minutes

        # Initialize service only if NOT in local mode
        if not self.local_mode:
            self._init_service()
        else:
            self.service = None

    def _init_service(self):
        """Initialize Google Sheets API service"""
        try:
            credentials = Credentials.from_service_account_file(
                self.service_account_file, scopes=self.scopes
            )
            self.service = build('sheets', 'v4', credentials=credentials)
        except Exception as e:
            raise Exception(f"Failed to initialize Google Sheets service: {str(e)}")

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry[cache_key]

    def read_sheet(self, sheet_id: str, range_name: str, force_refresh: bool = False) -> pd.DataFrame:
        """
        Read data from a Google Sheet

        Args:
            sheet_id: Google Sheet ID
            range_name: Range to read (e.g., 'Sheet1!A1:Z100')
            force_refresh: Force refresh from Google Sheets (ignore cache)

        Returns:
            DataFrame with sheet data
        """
        cache_key = f"{sheet_id}_{range_name}"

        # Check cache first
        if not force_refresh and self._is_cache_valid(cache_key) and cache_key in self._data_cache:
            return self._data_cache[cache_key]

        try:
            if self.local_mode:
                # Return empty DataFrame in local mode
                df = pd.DataFrame()
                self._data_cache[cache_key] = df
                self._cache_expiry[cache_key] = datetime.now() + self._cache_duration
                return df

            # Call the Sheets API
            sheet = self.service.spreadsheets()
            result = sheet.values().get(spreadsheetId=sheet_id, range=range_name).execute()
            values = result.get('values', [])

            if not values:
                # Empty sheet
                df = pd.DataFrame()
            else:
                # Convert to DataFrame
                df = pd.DataFrame(values[1:], columns=values[0])  # First row as headers

            # Cache the data
            self._data_cache[cache_key] = df
            self._cache_expiry[cache_key] = datetime.now() + self._cache_duration

            return df

        except HttpError as err:
            raise Exception(f"Google Sheets API error: {err}")
        except Exception as e:
            raise Exception(f"Failed to read Google Sheet {sheet_id}: {str(e)}")

    def get_project_data(self, project_id: Optional[str] = None) -> pd.DataFrame:
        """
        Get project data from Google Sheets

        Args:
            project_id: Specific project ID to filter

        Returns:
            DataFrame with project information
        """
        sheet_config = self.google_sheets.get('projects')
        if not sheet_config:
            raise ValueError("Projects sheet not configured")

        df = self.read_sheet(sheet_config['sheet_id'], sheet_config['range'])

        if project_id:
            # Try common project ID column names
            id_columns = ['ProjectID', 'ID', 'Project_ID', 'project_id']
            id_column = None

            for col in id_columns:
                if col in df.columns:
                    id_column = col
                    break

            if id_column:
                df = df[df[id_column] == project_id]
            else:
                raise ValueError("Could not find project ID column in projects sheet")

        return df

    def get_budget_data(self, project_id: Optional[str] = None) -> pd.DataFrame:
        """
        Get budget data from Google Sheets

        Args:
            project_id: Specific project ID to filter

        Returns:
            DataFrame with budget information
        """
        sheet_config = self.google_sheets.get('budgets')
        if not sheet_config:
            raise ValueError("Budgets sheet not configured")

        df = self.read_sheet(sheet_config['sheet_id'], sheet_config['range'])

        if project_id:
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
        Get schedule data from Google Sheets

        Args:
            project_id: Specific project ID to filter

        Returns:
            DataFrame with schedule information
        """
        sheet_config = self.google_sheets.get('schedules')
        if not sheet_config:
            raise ValueError("Schedules sheet not configured")

        df = self.read_sheet(sheet_config['sheet_id'], sheet_config['range'])

        if project_id:
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
        Get resource allocation data from Google Sheets

        Args:
            project_id: Specific project ID to filter

        Returns:
            DataFrame with resource information
        """
        sheet_config = self.google_sheets.get('resources')
        if not sheet_config:
            raise ValueError("Resources sheet not configured")

        df = self.read_sheet(sheet_config['sheet_id'], sheet_config['range'])

        if project_id:
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
            criteria: Dictionary of search criteria

        Returns:
            DataFrame with matching projects
        """
        df = self.get_project_data()

        # Apply filters based on criteria
        for field, value in criteria.items():
            if field in df.columns:
                if isinstance(value, dict):
                    # Handle range queries
                    if 'min' in value and 'max' in value:
                        df = df[(df[field] >= value['min']) & (df[field] <= value['max'])]
                    elif 'min' in value:
                        df = df[df[field] >= value['min']]
                    elif 'max' in value:
                        df = df[df[field] <= value['max']]
                elif isinstance(value, list):
                    df = df[df[field].isin(value)]
                else:
                    df = df[df[field] == value]

        return df

    def get_projects_over_budget(self, threshold_percent: float = 0.0) -> pd.DataFrame:
        """
        Get projects that are over budget by specified threshold

        Args:
            threshold_percent: Minimum percentage over budget

        Returns:
            DataFrame with over-budget projects
        """
        projects_df = self.get_project_data()
        budget_df = self.get_budget_data()

        # Merge data
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
            days_threshold: Minimum days delayed

        Returns:
            DataFrame with delayed projects
        """
        projects_df = self.get_project_data()
        schedule_df = self.get_schedule_data()

        # Merge data
        merged_df = pd.merge(projects_df, schedule_df, on='ProjectID', how='inner')

        # Calculate delays
        if 'PlannedEndDate' in merged_df.columns and 'ActualEndDate' in merged_df.columns:
            merged_df['PlannedEndDate'] = pd.to_datetime(merged_df['PlannedEndDate'])
            merged_df['ActualEndDate'] = pd.to_datetime(merged_df['ActualEndDate'])

            merged_df['DelayDays'] = (merged_df['ActualEndDate'] - merged_df['PlannedEndDate']).dt.days

            # Filter delayed projects
            delayed = merged_df[merged_df['DelayDays'] > days_threshold]
            return delayed
        else:
            raise ValueError("Date columns not found in schedule data")

    def clear_cache(self):
        """Clear cached sheet data"""
        self._data_cache.clear()
        self._cache_expiry.clear()

    def list_available_sheets(self, sheet_id: str) -> List[str]:
        """
        List available sheets in a Google Spreadsheet

        Args:
            sheet_id: Google Sheet ID

        Returns:
            List of sheet names
        """
        try:
            if self.local_mode:
                return []

            sheet_metadata = self.service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            sheets = sheet_metadata.get('sheets', [])

            return [sheet['properties']['title'] for sheet in sheets]

        except HttpError as err:
            raise Exception(f"Google Sheets API error: {err}")
        except Exception as e:
            raise Exception(f"Failed to list sheets for {sheet_id}: {str(e)}")