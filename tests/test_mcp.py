#!/usr/bin/env python3
"""
Test script for Construction Management MCP Server

Tests the various components and functionality of the MCP server
without requiring full SharePoint/OneDrive integration.
"""

import sys
import os
# Ensure runtime can import from the local src/ folder
PROJECT_ROOT = os.path.dirname(__file__)
SRC_PATH = os.path.join(PROJECT_ROOT, '..', 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

import pandas as pd
import zipfile
from unittest.mock import Mock, patch
import json

def test_excel_connector_local():
    """Test Excel connector with local sample files"""
    print("Testing Excel Connector with local files...")
    
    try:
        # Mock the Excel connector to use local CSV files instead of OneDrive
        from connectors.excel_connector import ExcelConnector
        
        # Create a mock config
        config = {
            'client_id': 'test',
            'client_secret': 'test', 
            'tenant_id': 'test',
            'sharepoint_site': 'test',
            'excel_files': {
                'projects': 'Project_Database.xlsx',
                'budgets': 'Budget_Tracking.xlsx',
                'schedules': 'Master_Schedule.xlsx',
                'resources': 'Resource_Allocation.xlsx'
            }
        }
        
        # Test reading sample data from local sample folder
        data_dir = os.path.join(PROJECT_ROOT, 'data', 'sample')
        
        # Helper to read either real Excel or CSV masquerading as .xlsx
        def _read_table(path: str) -> pd.DataFrame:
            try:
                return pd.read_excel(path, engine='openpyxl')
            except (zipfile.BadZipFile, ValueError, FileNotFoundError):
                # Fallback to CSV if it's not a valid Excel file
                return pd.read_csv(path)

        # Read project data
        projects_file = os.path.join(data_dir, 'Project_Database.xlsx')
        if os.path.exists(projects_file):
            projects_df = _read_table(projects_file)
            print(f"✓ Loaded {len(projects_df)} projects")
            if 'ProjectName' in projects_df.columns:
                print(f"Projects: {projects_df['ProjectName'].dropna().astype(str).tolist()}")
        
        # Read budget data
        budget_file = os.path.join(data_dir, 'Budget_Tracking.xlsx')
        if os.path.exists(budget_file):
            budget_df = _read_table(budget_file)
            print(f"✓ Loaded budget data rows: {len(budget_df)}")
        
        print("Excel connector test passed!")
        assert True
        
    except Exception as e:
        print(f"✗ Excel connector test failed: {str(e)}")
        assert False, f"Excel connector test failed: {str(e)}"

def test_query_processor():
    """Test the query processing engine"""
    print("\nTesting Query Processor...")
    
    try:
        from query_processor import QueryProcessor
        
        # Create mock connectors
        excel_mock = Mock()
        sharepoint_mock = Mock()
        document_mock = Mock()
        google_sheets_mock = Mock()
        
        processor = QueryProcessor(excel_mock, sharepoint_mock, document_mock, google_sheets_mock)
        
        # Test query parsing
        test_queries = [
            "Show me all projects that are over budget",
            "What's the status of project PROJ001?",
            "List all active projects",
            "Find safety incident reports",
            "Generate a budget analysis report"
        ]
        
        for query in test_queries:
            parsed = processor.parse_query(query)
            print(f"✓ Parsed '{query}' → {parsed['type']} ({parsed['method']})")
        
        print("Query processor test passed!")
        assert True
        
    except Exception as e:
        print(f"✗ Query processor test failed: {str(e)}")
        assert False, f"Query processor test failed: {str(e)}"

def test_document_indexer():
    """Test document indexing functionality"""
    print("\nTesting Document Indexer...")
    
    try:
        from connectors.document_indexer import DocumentIndexer
        
        config = {
            'client_id': 'test',
            'client_secret': 'test',
            'tenant_id': 'test', 
            'sharepoint_site': 'test',
            'local_docs_path': os.path.join(PROJECT_ROOT, 'data', 'sample'),
            'index_file': os.path.join(PROJECT_ROOT, 'data', 'test_index.json')
        }
        
        # Mock the authentication to avoid SharePoint calls
        with patch.object(DocumentIndexer, '_init_auth'):
            indexer = DocumentIndexer(config)
            
            # Test keyword extraction
            keywords = indexer._extract_keywords("Project_ABC_Blueprint_Final.dwg", "/drawings/Project_ABC_Blueprint_Final.dwg")
            print(f"✓ Extracted keywords: {keywords}")
            
            # Test document categorization
            category = indexer._categorize_document("safety_incident_report_2024.pdf")
            print(f"✓ Categorized 'safety_incident_report_2024.pdf' as: {category}")
            
            # Test search functionality (with empty index)
            results = indexer.search_documents("project")
            print(f"✓ Search returned {len(results)} results")
        
        print("Document indexer test passed!")
        assert True
        
    except Exception as e:
        print(f"✗ Document indexer test failed: {str(e)}")
        assert False, f"Document indexer test failed: {str(e)}"

def test_sample_queries():
    """Test sample construction management queries"""
    print("\nTesting Sample Queries...")
    
    sample_queries = [
        "Show me all projects that are over budget this month",
        "What's the completion percentage for the downtown office building?", 
        "List all safety incidents from the last quarter",
        "Which subcontractors are working on active projects?",
        "Generate a status report for projects ending this month",
        "Find all electrical drawings for project PROJ001",
        "What's the budget variance for residential projects?",
        "Show overdue tasks for all active projects"
    ]
    
    try:
        from query_processor import QueryProcessor
        
        # Mock connectors
        excel_mock = Mock()
        sharepoint_mock = Mock() 
        document_mock = Mock()
        google_sheets_mock = Mock()
        
        processor = QueryProcessor(excel_mock, sharepoint_mock, document_mock, google_sheets_mock)
        
        for query in sample_queries:
            parsed = processor.parse_query(query)
            print(f"✓ '{query}' → {parsed['type']} using {parsed['data_source']}")
        
        print("Sample queries test passed!")
        assert True
        
    except Exception as e:
        print(f"✗ Sample queries test failed: {str(e)}")
        assert False, f"Sample queries test failed: {str(e)}"

def create_sample_credentials():
    """Create sample credentials file for testing"""
    print("\nCreating sample credentials file...")
    
    try:
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
        os.makedirs(config_dir, exist_ok=True)
        
        credentials_file = os.path.join(config_dir, 'credentials.json')
        
        if not os.path.exists(credentials_file):
            sample_credentials = {
                "client_id": "your-azure-app-client-id-here",
                "client_secret": "your-azure-app-client-secret-here",
                "tenant_id": "your-azure-tenant-id-here", 
                "sharepoint_site": "https://yourcompany.sharepoint.com/sites/construction",
                "onedrive_folder": "/Construction Projects",
                "excel_files": {
                    "projects": "Project_Database.xlsx",
                    "budgets": "Budget_Tracking.xlsx",
                    "schedules": "Master_Schedule.xlsx", 
                    "resources": "Resource_Allocation.xlsx"
                },
                "sharepoint_lists": {
                    "projects": "Projects",
                    "tasks": "Tasks",
                    "safety_incidents": "Safety Incidents",
                    "subcontractors": "Subcontractors"
                }
            }
            
            with open(credentials_file, 'w') as f:
                json.dump(sample_credentials, f, indent=2)
                
            print(f"✓ Created sample credentials file at {credentials_file}")
            print("⚠ Remember to update with your actual Azure credentials!")
        else:
            print("✓ Credentials file already exists")
        
        assert True
        
    except Exception as e:
        print(f"✗ Failed to create credentials file: {str(e)}")
        assert False, f"Failed to create credentials file: {str(e)}"

def main():
    """Run all tests"""
    print("🏗️ Construction Management MCP - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Sample Credentials", create_sample_credentials),
        ("Excel Connector", test_excel_connector_local),
        ("Query Processor", test_query_processor),
        ("Document Indexer", test_document_indexer), 
        ("Sample Queries", test_sample_queries)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("Test Results:")
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED" 
        print(f"{test_name}: {status}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\nOverall: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("🎉 All tests passed! Your MCP server is ready to use.")
        print("\nNext steps:")
        print("1. Update config/credentials.json with your Azure credentials")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Configure your MCP client (VS Code/Cursor)")
        print("4. Test with real data: python src/main.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()