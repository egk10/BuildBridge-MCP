#!/usr/bin/env python3
"""
Construction Management MCP Server

A Model Context Protocol server for automating construction management 
data analysis using Excel files and SharePoint data.
"""

import os
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

import fastmcp
from fastmcp import FastMCP

from connectors.excel_connector import ExcelConnector
from connectors.sharepoint_connector import SharePointConnector  
from connectors.document_indexer import DocumentIndexer
from query_processor import QueryProcessor

# Initialize MCP server
mcp = FastMCP("Construction Management MCP")

# Global connectors
excel_connector: Optional[ExcelConnector] = None
sharepoint_connector: Optional[SharePointConnector] = None
document_indexer: Optional[DocumentIndexer] = None
query_processor: Optional[QueryProcessor] = None

def load_config() -> Dict[str, Any]:
    """Load configuration from credentials.json"""
    config_path = Path(__file__).parent.parent / "config" / "credentials.json"
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            "Please copy credentials.json.template to credentials.json and fill in your details."
        )
    
    with open(config_path, 'r') as f:
        return json.load(f)

def initialize_connectors():
    """Initialize all data connectors"""
    global excel_connector, sharepoint_connector, document_indexer, query_processor
    
    config = load_config()
    
    # Initialize connectors
    # Propagate local_mode from config (optional)
    local_mode = bool(config.get('local_mode'))
    if local_mode:
        config = {**config, 'local_mode': True}

    excel_connector = ExcelConnector(config)
    sharepoint_connector = SharePointConnector(config)
    document_indexer = DocumentIndexer(config)
    query_processor = QueryProcessor(excel_connector, sharepoint_connector, document_indexer)

@mcp.tool()
def search_projects(query: str, filters: Optional[Dict[str, Any]] = None) -> str:
    """
    Search for construction projects based on natural language query.
    
    Args:
        query: Natural language query (e.g., "show projects over budget")
        filters: Optional filters like date range, status, etc.
    
    Returns:
        Formatted project data matching the query
    """
    if not query_processor:
        return "Error: MCP server not properly initialized"
    
    try:
        results = query_processor.search_projects(query, filters)
        return format_project_results(results)
    except Exception as e:
        return f"Error searching projects: {str(e)}"

@mcp.tool()
def get_project_status(project_id: str) -> str:
    """
    Get detailed status for a specific construction project.
    
    Args:
        project_id: Unique identifier for the project
    
    Returns:
        Detailed project status including schedule, budget, and milestones
    """
    if not query_processor:
        return "Error: MCP server not properly initialized"
    
    try:
        status = query_processor.get_project_status(project_id)
        return format_project_status(status)
    except Exception as e:
        return f"Error getting project status: {str(e)}"

@mcp.tool()
def analyze_budget(project_id: Optional[str] = None, period: str = "current_month") -> str:
    """
    Analyze budget performance for projects.
    
    Args:
        project_id: Specific project ID (if None, analyzes all projects)
        period: Time period for analysis (current_month, quarter, year)
    
    Returns:
        Budget analysis with variance, forecasts, and recommendations
    """
    if not query_processor:
        return "Error: MCP server not properly initialized"
    
    try:
        analysis = query_processor.analyze_budget(project_id, period)
        return format_budget_analysis(analysis)
    except Exception as e:
        return f"Error analyzing budget: {str(e)}"

@mcp.tool()
def get_schedule_updates(days_ahead: int = 30) -> str:
    """
    Get upcoming schedule milestones and potential delays.
    
    Args:
        days_ahead: Number of days to look ahead for schedule items
    
    Returns:
        Schedule updates, milestones, and risk alerts
    """
    if not query_processor:
        return "Error: MCP server not properly initialized"
    
    try:
        updates = query_processor.get_schedule_updates(days_ahead)
        return format_schedule_updates(updates)
    except Exception as e:
        return f"Error getting schedule updates: {str(e)}"

@mcp.tool()
def search_documents(query: str, doc_type: Optional[str] = None) -> str:
    """
    Search construction documents by keywords or content.
    
    Args:
        query: Search terms or keywords
        doc_type: Optional document type filter (drawings, specs, reports, etc.)
    
    Returns:
        List of relevant documents with summaries
    """
    if not document_indexer:
        return "Error: Document indexer not initialized"
    
    try:
        results = document_indexer.search_documents(query, doc_type)
        return format_document_results(results)
    except Exception as e:
        return f"Error searching documents: {str(e)}"

@mcp.tool()
def generate_report(report_type: str, project_id: Optional[str] = None) -> str:
    """
    Generate construction management reports.
    
    Args:
        report_type: Type of report (status, budget, safety, compliance)
        project_id: Specific project (if None, generates for all projects)
    
    Returns:
        Formatted report based on current data
    """
    if not query_processor:
        return "Error: MCP server not properly initialized"
    
    try:
        report = query_processor.generate_report(report_type, project_id)
        return format_report(report)
    except Exception as e:
        return f"Error generating report: {str(e)}"

# Formatting helper functions
def format_project_results(results: List[Dict[str, Any]]) -> str:
    """Format project search results"""
    if not results:
        return "No projects found matching your criteria."
    
    formatted = "## Project Search Results\n\n"
    for project in results:
        formatted += f"**{project.get('name', 'Unknown')}** (ID: {project.get('id', 'N/A')})\n"
        formatted += f"- Status: {project.get('status', 'Unknown')}\n"
        formatted += f"- Budget: ${project.get('budget', 0):,.2f}\n"
        formatted += f"- Progress: {project.get('progress', 0)}%\n"
        formatted += f"- Manager: {project.get('manager', 'Unassigned')}\n\n"
    
    return formatted

def format_project_status(status: Dict[str, Any]) -> str:
    """Format detailed project status"""
    formatted = f"## Project Status: {status.get('name', 'Unknown Project')}\n\n"
    formatted += f"**Project ID:** {status.get('id', 'N/A')}\n"
    formatted += f"**Status:** {status.get('status', 'Unknown')}\n"
    formatted += f"**Progress:** {status.get('progress', 0)}%\n"
    formatted += f"**Budget Status:** {status.get('budget_status', 'Unknown')}\n"
    formatted += f"**Schedule Status:** {status.get('schedule_status', 'Unknown')}\n"
    
    if 'milestones' in status:
        formatted += "\n**Upcoming Milestones:**\n"
        for milestone in status['milestones'][:5]:  # Show next 5 milestones
            formatted += f"- {milestone.get('name', 'Unknown')}: {milestone.get('date', 'TBD')}\n"
    
    return formatted

def format_budget_analysis(analysis: Dict[str, Any]) -> str:
    """Format budget analysis results"""
    formatted = "## Budget Analysis\n\n"
    formatted += f"**Total Budget:** ${analysis.get('total_budget', 0):,.2f}\n"
    formatted += f"**Spent to Date:** ${analysis.get('spent', 0):,.2f}\n"
    formatted += f"**Remaining:** ${analysis.get('remaining', 0):,.2f}\n"
    formatted += f"**Variance:** {analysis.get('variance_percent', 0):+.1f}%\n"
    
    if 'over_budget_projects' in analysis:
        formatted += "\n**Projects Over Budget:**\n"
        for project in analysis['over_budget_projects']:
            formatted += f"- {project.get('name', 'Unknown')}: {project.get('variance', 0):+.1f}%\n"
    
    return formatted

def format_schedule_updates(updates: Dict[str, Any]) -> str:
    """Format schedule updates"""
    formatted = "## Schedule Updates\n\n"
    
    if 'upcoming_milestones' in updates:
        formatted += "**Upcoming Milestones:**\n"
        for milestone in updates['upcoming_milestones']:
            formatted += f"- {milestone.get('project', 'Unknown')}: {milestone.get('name', 'Unknown')} ({milestone.get('date', 'TBD')})\n"
    
    if 'delayed_projects' in updates:
        formatted += "\n**Projects with Delays:**\n"
        for project in updates['delayed_projects']:
            formatted += f"- {project.get('name', 'Unknown')}: {project.get('delay_days', 0)} days behind\n"
    
    return formatted

def format_document_results(results: List[Dict[str, Any]]) -> str:
    """Format document search results"""
    if not results:
        return "No documents found matching your search."
    
    formatted = "## Document Search Results\n\n"
    for doc in results:
        formatted += f"**{doc.get('title', 'Unknown Document')}**\n"
        formatted += f"- Type: {doc.get('type', 'Unknown')}\n"
        formatted += f"- Modified: {doc.get('modified', 'Unknown')}\n"
        formatted += f"- Location: {doc.get('location', 'Unknown')}\n"
        if 'summary' in doc:
            formatted += f"- Summary: {doc['summary']}\n"
        formatted += "\n"
    
    return formatted

def format_report(report: Dict[str, Any]) -> str:
    """Format generated reports"""
    formatted = f"## {report.get('title', 'Construction Report')}\n\n"
    formatted += f"**Generated:** {report.get('timestamp', 'Unknown')}\n"
    formatted += f"**Period:** {report.get('period', 'Unknown')}\n\n"
    
    if 'content' in report:
        formatted += report['content']
    
    return formatted

if __name__ == "__main__":
    # Initialize connectors
    try:
        initialize_connectors()
        print("Construction Management MCP Server initialized successfully!")
        print("Available tools:")
        print("- search_projects: Search for projects by natural language")
        print("- get_project_status: Get detailed project status")
        print("- analyze_budget: Analyze budget performance")
        print("- get_schedule_updates: Get schedule milestones and delays")
        print("- search_documents: Search construction documents")
        print("- generate_report: Generate various reports")
    except Exception as e:
        print(f"Error initializing MCP server: {e}")
        exit(1)
    
    # Run the server
    mcp.run()