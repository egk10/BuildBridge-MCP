# Construction Management MCP - Test Results and Usage Examples

## Test Queries

Here are example queries you can use to test your Construction Management MCP:

### Project Management Queries

1. **Project Search**
   - "Show me all active projects"
   - "List projects that are in progress"
   - "Find all commercial projects"
   - "Show projects managed by John Smith"

2. **Project Status**
   - "What's the status of project PROJ001?"
   - "How is the downtown office building progressing?"
   - "Give me details on the residential complex project"

3. **Budget Analysis**
   - "Show me all projects that are over budget"
   - "What's the budget variance for project PROJ002?"
   - "Analyze budget performance this month"
   - "List projects under budget"

### Schedule Management Queries

4. **Schedule and Timeline**
   - "What are the upcoming milestones for the next 30 days?"
   - "Show me overdue tasks"
   - "Which projects are behind schedule?"
   - "What's due this week?"

5. **Resource Management**
   - "Which subcontractors are working on active projects?"
   - "Show resource allocation for project PROJ001"
   - "List all equipment being used this month"

### Safety and Compliance

6. **Safety Queries**
   - "Show safety incidents from this quarter"
   - "List all accidents on project PROJ003"
   - "Generate a safety report"

### Document Management

7. **Document Search**
   - "Find electrical drawings for downtown office building"
   - "Search for safety specifications"
   - "Locate permit documents"
   - "Show me recent project photos"

### Reporting

8. **Report Generation**
   - "Generate a status report for all projects"
   - "Create a budget analysis report"
   - "Prepare a safety compliance report"
   - "Generate project timeline report"

## Expected Responses

When you run these queries through the MCP server, you should expect responses like:

### Example 1: "Show me all projects that are over budget"

```
## Project Search Results

**Residential Complex Phase 1** (ID: PROJ002)
- Status: Active
- Budget: $1,800,000.00
- Progress: 80%
- Manager: Sarah Johnson

Budget Analysis shows this project is 10% over allocated budget.
```

### Example 2: "What's the status of project PROJ001?"

```
## Project Status: Downtown Office Building

**Project ID:** PROJ001
**Status:** In Progress
**Progress:** 65%
**Budget Status:** On Budget
**Schedule Status:** 2 Overdue Tasks

**Upcoming Milestones:**
- HVAC Installation: 2024-08-30
- Electrical Inspection: 2024-09-15
- Interior Finishing: 2024-10-01
```

### Example 3: "Generate a budget analysis report"

```
## Budget Analysis

**Total Budget:** $12,200,000.00
**Spent to Date:** $5,927,500.00
**Remaining:** $6,272,500.00
**Variance:** -3.2%

**Projects Over Budget:**
- Residential Complex Phase 1: +10.0%
```

## Testing the System

1. **Run the test script:**
   ```bash
   cd "c:/Users/eliek/Data Science MCP/construction-management-mcp"
   python test_mcp.py
   ```

2. **Test individual components:**
   ```bash
   # Test the main server
   python src/main.py
   
   # Test with sample data
   python -c "import pandas as pd; print(pd.read_csv('data/sample/Project_Database.xlsx'))"
   ```

3. **Test in your MCP client:**
   - Configure VS Code or Cursor with the MCP server
   - Try the sample queries listed above
   - Verify responses match expected format

## Troubleshooting Common Issues

### Authentication Errors
- Verify Azure app registration
- Check client ID, secret, and tenant ID
- Ensure proper API permissions

### Data Access Issues
- Check SharePoint site URL
- Verify OneDrive folder paths
- Ensure Excel file names match configuration

### Query Processing Issues
- Check natural language query format
- Verify query patterns match expected structure
- Review query processor logs

## Performance Optimization

### For Large Datasets
- Enable caching in Excel connector
- Use index optimization in document indexer
- Implement pagination for large result sets

### For Real-Time Updates
- Set appropriate cache expiry times
- Use SharePoint webhooks for live updates
- Implement incremental indexing

## Next Steps

1. **Customize for Your Environment**
   - Update SharePoint list names
   - Modify Excel file structures
   - Add custom query patterns

2. **Extend Functionality**
   - Add more document types
   - Implement additional report types
   - Create custom analytics

3. **Production Deployment**
   - Set up proper logging
   - Implement error handling
   - Configure monitoring and alerts