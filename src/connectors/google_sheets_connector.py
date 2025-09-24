"""
Google Sheets Connector for Construction Management MCP

Handles reading and processing Google Sheets containing construction project data,
budgets, schedules, and resource information.
"""

import os
import json
import pickle
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import webbrowser
import threading

from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleSheetsConnector:
    """Connector for accessing Google Sheets"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Google Sheets connector with OAuth2 or service account credentials

        Args:
            config: Configuration dictionary with Google API credentials
        """
        self.config = config
        
        # Resolve paths relative to project root (parent of src directory)
        project_root = Path(__file__).parent.parent.parent
        self.credentials_file = config.get('google_credentials_file')
        if self.credentials_file:
            self.credentials_file = str(project_root / self.credentials_file)
        
        self.service_account_file = config.get('google_service_account_file')
        if self.service_account_file:
            self.service_account_file = str(project_root / self.service_account_file)
            
        self.google_sheets = config.get('google_sheets', {})
        self.token_file = config.get('google_token_file', 'token.pickle')
        if not self.token_file.startswith('/'):
            self.token_file = str(project_root / self.token_file)

        # Scopes for Google Sheets and Drive access
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]

        # Local mode toggle
        self.local_mode = bool(
            config.get('local_mode') or
            (not self.credentials_file and not self.service_account_file)
        )

        # Authentication type
        self.auth_type = self._determine_auth_type()

        # Cache for sheet data
        self._data_cache = {}
        self._cache_expiry = {}
        self._cache_duration = timedelta(minutes=15)  # Cache for 15 minutes

        # Initialize service only if NOT in local mode
        if not self.local_mode:
            self._init_service()
        else:
            self.service = None
            self.drive_service = None

    def _resolve_sheet_id(self, sheet_id_ref: str) -> str:
        """
        Resolve sheet ID references like 'projects.72_perth' to actual sheet IDs

        Args:
            sheet_id_ref: Sheet ID reference, either direct ID or 'projects.<project_key>'

        Returns:
            Actual Google Sheet ID
        """
        if '.' in sheet_id_ref and sheet_id_ref.startswith('projects.'):
            # This is a project reference like 'projects.72_perth'
            _, project_key = sheet_id_ref.split('.', 1)
            projects = self.google_sheets.get('projects', {})
            if project_key in projects:
                return projects[project_key]
            else:
                raise ValueError(f"Project '{project_key}' not found in projects configuration")
        else:
            # Direct sheet ID
            return sheet_id_ref

    def _determine_auth_type(self) -> str:
        """Determine which authentication method to use"""
        if self.service_account_file and os.path.exists(self.service_account_file):
            return 'service_account'
        elif self.credentials_file and os.path.exists(self.credentials_file):
            return 'oauth'
        else:
            return 'none'

    def _init_service(self):
        """Initialize Google API services based on authentication type"""
        try:
            if self.auth_type == 'service_account':
                self._init_service_account_auth()
            elif self.auth_type == 'oauth':
                self._init_oauth_auth()
            else:
                raise Exception("No valid Google authentication method found")

            # Check if we have valid credentials
            if not self.creds:
                raise Exception("No valid Google credentials available")

            # Initialize both Sheets and Drive services
            self.service = build('sheets', 'v4', credentials=self.creds)
            self.drive_service = build('drive', 'v3', credentials=self.creds)

        except Exception as e:
            print(f"Failed to initialize Google services: {str(e)}")
            # Set to local mode if Google services fail
            self.local_mode = True
            self.service = None
            self.drive_service = None

    def _init_service_account_auth(self):
        """Initialize service account authentication"""
        self.creds = ServiceAccountCredentials.from_service_account_file(
            self.service_account_file, scopes=self.scopes
        )

    def _init_oauth_auth(self):
        """Initialize OAuth2 authentication"""
        self.creds = None

        # Check if token file exists
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'rb') as token:
                    self.creds = pickle.load(token)
            except Exception as e:
                print(f"Warning: Failed to load token file: {e}")
                self.creds = None

        # If credentials are invalid or don't exist, try to refresh or fail gracefully
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    print("Attempting to refresh Google OAuth tokens...")
                    self.creds.refresh(Request())
                    # Save the refreshed credentials
                    with open(self.token_file, 'wb') as token:
                        pickle.dump(self.creds, token)
                    print("✅ Successfully refreshed Google OAuth tokens")
                except Exception as e:
                    print(f"❌ Failed to refresh tokens: {e}")
                    print("Google Sheets authentication will not be available")
                    self.creds = None
            else:
                print("No valid Google OAuth tokens found and cannot refresh")
                print("Google Sheets authentication will not be available")
                self.creds = None

    def _perform_oauth_flow(self):
        """Perform OAuth2 flow to get user credentials"""
        flow = InstalledAppFlow.from_client_secrets_file(
            self.credentials_file, self.scopes
        )

        # Explicitly set redirect URI for desktop app
        flow.redirect_uri = "http://localhost"

        # Use manual flow instead of local server to avoid port issues
        auth_url, _ = flow.authorization_url(prompt='consent')

        print(f"\n🔗 Please visit this URL to authorize the application:")
        print(f"{auth_url}")
        print(f"\nAfter authorization, you'll be redirected to a page showing an authorization code.")
        print(f"Copy the code from the URL (the part after 'code=') and paste it here:")

        auth_code = input("Enter the authorization code: ").strip()

        # Exchange the authorization code for credentials
        flow.fetch_token(code=auth_code)
        self.creds = flow.credentials

    def authenticate_google_drive(self) -> bool:
        """
        Authenticate with Google Drive and return success status

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            if self.local_mode:
                print("Running in local mode - no Google authentication needed")
                return True

            if not self.service:
                self._init_service()

            # Test authentication by listing files
            results = self.drive_service.files().list(
                pageSize=1, fields="files(id, name)"
            ).execute()

            files = results.get('files', [])
            print(f"✅ Google Drive authentication successful! Found {len(files)} files accessible.")
            return True

        except Exception as e:
            print(f"❌ Google Drive authentication failed: {str(e)}")
            return False

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry[cache_key]

    def read_sheet(self, sheet_id: str, range_name: str, force_refresh: bool = False) -> pd.DataFrame:
        """
        Read data from a Google Sheet

        Args:
            sheet_id: Google Sheet ID or project reference (e.g., 'projects.72_perth')
            range_name: Range to read (e.g., 'Sheet1!A1:Z100')
            force_refresh: Force refresh from Google Sheets (ignore cache)

        Returns:
            DataFrame with sheet data
        """
        # Resolve project references to actual sheet IDs
        actual_sheet_id = self._resolve_sheet_id(sheet_id)
        cache_key = f"{actual_sheet_id}_{range_name}"

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
            result = sheet.values().get(spreadsheetId=actual_sheet_id, range=range_name).execute()
            values = result.get('values', [])

            if not values:
                # Empty sheet
                df = pd.DataFrame()
            else:
                # Handle irregular sheet structures
                # Find the maximum number of columns in any row
                max_cols = max(len(row) for row in values) if values else 0
                
                if len(values) == 1:
                    # Only headers, no data
                    df = pd.DataFrame(columns=values[0])
                elif max_cols == len(values[0]):
                    # Regular structure: first row is headers
                    df = pd.DataFrame(values[1:], columns=values[0])
                else:
                    # Irregular structure: create generic column names
                    columns = [f'Col_{i+1}' for i in range(max_cols)]
                    # Pad shorter rows with empty strings
                    padded_values = []
                    for row in values:
                        padded_row = row + [''] * (max_cols - len(row))
                        padded_values.append(padded_row)
                    df = pd.DataFrame(padded_values, columns=columns)

            # Cache the data
            self._data_cache[cache_key] = df
            self._cache_expiry[cache_key] = datetime.now() + self._cache_duration

            return df

        except HttpError as err:
            raise Exception(f"Google Sheets API error: {err}")
        except Exception as e:
            raise Exception(f"Failed to read Google Sheet {actual_sheet_id}: {str(e)}")

    def get_project_data(self, project_id: Optional[str] = None) -> pd.DataFrame:
        """
        Get project data from Google Sheets

        Args:
            project_id: Specific project ID to filter

        Returns:
            DataFrame with project information
        """
        all_projects = []
        
        # Get project configurations from config
        projects_config = self.google_sheets.get('projects', {})
        
        # For each project, try to get data from its summary sheet
        for project_key, sheet_id in projects_config.items():
            try:
                # Create the expected summary sheet key name
                # Convert project key format (e.g., "72_perth" -> "72perth_project_summary")
                clean_key = project_key.replace('_', '').replace('-', '')
                summary_sheet_key = f"{clean_key}_project_summary"
                
                # Check if the summary sheet config exists
                if summary_sheet_key in self.google_sheets:
                    sheet_config = self.google_sheets[summary_sheet_key]
                    config_sheet_id = sheet_config['sheet_id']
                    
                    # Resolve sheet_id reference if it uses "projects.<key>" format
                    if config_sheet_id.startswith('projects.'):
                        ref_key = config_sheet_id.split('.', 1)[1]
                        actual_sheet_id = projects_config.get(ref_key, config_sheet_id)
                    else:
                        actual_sheet_id = config_sheet_id
                    
                    # Try to read the sheet
                    df = self.read_sheet(actual_sheet_id, sheet_config['range'])
                    
                    if not df.empty and len(df) > 0:
                        # Extract structured project data from the sheet
                        project_data = self._extract_project_info_from_sheet(df, project_key)
                        if project_data:
                            project_data['source'] = 'google_sheets'
                            all_projects.append(project_data)
                        
            except Exception as e:
                print(f"Warning: Failed to get data for project {project_key}: {e}")
                continue
        
        # Convert to DataFrame
        if all_projects:
            result_df = pd.DataFrame(all_projects)
        else:
            result_df = pd.DataFrame()
        
        if project_id:
            # Filter by project ID if specified
            if not result_df.empty and 'Project_ID' in result_df.columns:
                result_df = result_df[result_df['Project_ID'] == project_id]
        
        return result_df

    def _extract_project_info_from_sheet(self, df: pd.DataFrame, project_key: str) -> Optional[Dict[str, Any]]:
        """
        Extract structured project information from a complex sheet layout
        
        Args:
            df: DataFrame from the sheet
            project_key: Project identifier
            
        Returns:
            Dictionary with structured project data
        """
        project_data = {
            'Project_ID': project_key,
            'Project_Name': project_key.replace('_', ' ').title(),
            'source': 'google_sheets'
        }
        
        try:
            # Convert all data to strings for easier processing
            df_str = df.astype(str)
            
            # Try multiple column combinations for labels and values
            # Original pattern: labels in column F (5), values in column K (10)
            # New pattern found: labels in column D (3), values in column E (4)
            column_patterns = [
                (5, 10),  # Original: F and K
                (3, 4),   # New: D and E
                (4, 5),   # Alternative: E and F
            ]
            
            for label_col_idx, value_col_idx in column_patterns:
                if len(df_str.columns) > max(label_col_idx, value_col_idx):
                    for idx, row in df_str.iterrows():
                        label = str(row.iloc[label_col_idx]).strip()
                        if len(df_str.columns) > value_col_idx:
                            value = str(row.iloc[value_col_idx]).strip()
                        else:
                            value = ""
                        
                        # Extract information based on labels
                        if 'PROJECT:' in label.upper():
                            if value and value != '':
                                project_data['Project_Name'] = value
                        elif 'LOCATION:' in label.upper():
                            if value and value != '':
                                project_data['Location'] = value
                        elif 'CLIENT:' in label.upper():
                            if value and value != '':
                                project_data['Client'] = value
                        elif 'DATE:' in label.upper():
                            if value and value != '':
                                project_data['Start_Date'] = value
            
            # Also scan all cells for budget information
            budget_found = False
            for idx, row in df_str.iterrows():
                for col in df_str.columns:
                    cell_value = str(row[col]).strip()
                    # Look for dollar amounts
                    if '$' in cell_value and not budget_found:
                        import re
                        match = re.search(r'\$([0-9,]+(?:\.[0-9]+)?)', cell_value)
                        if match:
                            amount_str = match.group(1).replace(',', '')
                            try:
                                budget = float(amount_str)
                                if budget > 10000:  # Reasonable budget threshold
                                    project_data['Total_Budget'] = budget
                                    budget_found = True
                                    break
                            except ValueError:
                                continue
                if budget_found:
                    break
            
            # Set default values for missing information
            project_data.setdefault('Status', 'Active')
            project_data.setdefault('Progress_Percent', 25)  # Default progress
            project_data.setdefault('Project_Manager', 'TBD')
            project_data.setdefault('Location', 'TBD')
            project_data.setdefault('Client', 'TBD')
            project_data.setdefault('Total_Budget', 750000)  # Default budget
            project_data.setdefault('Start_Date', 'TBD')
            
        except Exception as e:
            print(f"Warning: Error extracting project info for {project_key}: {e}")
            return None
        
        return project_data

    def _find_project_name_near_label(self, df: pd.DataFrame, label_row: int, label_col: str) -> Optional[str]:
        """Find project name near a label like 'PROJECT:'"""
        try:
            # Check cells to the right of the label
            col_index = df.columns.get_loc(label_col)
            for offset in range(1, min(5, len(df.columns) - col_index)):
                next_col = df.columns[col_index + offset]
                cell_value = str(df.at[label_row, next_col]).strip()
                if cell_value and cell_value != '' and not cell_value.startswith('PROJECT'):
                    return cell_value
            
            # Check the next row
            if label_row + 1 < len(df):
                for col in df.columns:
                    cell_value = str(df.at[label_row + 1, col]).strip()
                    if cell_value and cell_value != '' and len(cell_value) > 3:
                        return cell_value
                        
        except Exception:
            pass
        return None

    def _find_value_near_label(self, df: pd.DataFrame, label_row: int, label_col: str) -> Optional[str]:
        """Find a value near a label"""
        try:
            # Check cells to the right of the label
            col_index = df.columns.get_loc(label_col)
            for offset in range(1, min(5, len(df.columns) - col_index)):
                next_col = df.columns[col_index + offset]
                cell_value = str(df.at[label_row, next_col]).strip()
                if cell_value and cell_value != '':
                    return cell_value
            
            # Check the next row
            if label_row + 1 < len(df):
                for col in df.columns:
                    cell_value = str(df.at[label_row + 1, col]).strip()
                    if cell_value and cell_value != '':
                        return cell_value
                        
        except Exception:
            pass
        return None

    def _extract_budget_from_sheet(self, df: pd.DataFrame) -> Optional[float]:
        """Extract budget amount from sheet data"""
        try:
            # Look for dollar amounts in the sheet
            for idx, row in df.iterrows():
                for col in df.columns:
                    cell_value = str(row[col]).strip()
                    # Look for patterns like $750,000 or 750000
                    if '$' in cell_value:
                        # Extract number from dollar format
                        import re
                        match = re.search(r'\$([0-9,]+(?:\.[0-9]+)?)', cell_value)
                        if match:
                            amount_str = match.group(1).replace(',', '')
                            try:
                                return float(amount_str)
                            except ValueError:
                                continue
                    elif cell_value.replace(',', '').replace('.', '').isdigit():
                        # Check if it's a large number that could be a budget
                        try:
                            amount = float(cell_value.replace(',', ''))
                            if amount > 10000:  # Assume budgets are over $10k
                                return amount
                        except ValueError:
                            continue
        except Exception:
            pass
        return None

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
            sheet_id: Google Sheet ID or project reference (e.g., 'projects.72_perth')

        Returns:
            List of sheet names
        """
        try:
            if self.local_mode:
                return []

            # Resolve project references to actual sheet IDs
            actual_sheet_id = self._resolve_sheet_id(sheet_id)

            sheet_metadata = self.service.spreadsheets().get(spreadsheetId=actual_sheet_id).execute()
            sheets = sheet_metadata.get('sheets', [])

            return [sheet['properties']['title'] for sheet in sheets]

        except HttpError as err:
            raise Exception(f"Google Sheets API error: {err}")
        except Exception as e:
            raise Exception(f"Failed to list sheets for {actual_sheet_id}: {str(e)}")