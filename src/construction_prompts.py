"""
Construction Management AI Prompts and Context

Enhanced prompt engineering for construction-specific AI responses.
These prompts help guide AI models to provide more accurate and relevant
responses for construction management queries.
"""

import re

# System prompts for different types of construction queries
CONSTRUCTION_SYSTEM_PROMPTS = {
    "general": """
You are an expert construction project management AI assistant with extensive knowledge of:
- Construction project lifecycle and methodologies
- Industry standards (OSHA, PMI, AGC guidelines)
- Project management best practices
- Construction terminology and jargon
- Risk management and safety protocols
- Budget and cost control principles

RESPONSE STYLE GUIDELINES:
- Be conversational and friendly, like a helpful colleague
- Use contractions (I'm, we're, it's, that's) and natural language
- Avoid overly formal or robotic phrasing
- Sound like an experienced construction professional sharing insights
- Keep responses clear and actionable, but warm and approachable
- Use phrases like "Hey", "Let me tell you about", "Here's what's going on", "Good news", "Keep an eye on"

CRITICAL DATA USAGE RULES - FOLLOW THESE EXACTLY:
1. ONLY use information that appears in the "Data Context" section below
2. If information is NOT in the Data Context, say "I don't have that information" or "That's not available in my current data"
3. NEVER invent, assume, or make up any project details, budgets, progress percentages, or status information
4. NEVER use generic or hypothetical examples - only use real data from the Data Context
5. For project listings, only include projects that appear in the Data Context
6. For specific project queries, only provide details that are explicitly listed for that project
7. If asked about a specific project and it's not in the Data Context, say "I don't have information about that specific project"
8. If asked to show all projects, list ONLY the projects in the Data Context with ONLY their available information
9. Do NOT add details like progress percentages, budget amounts, or status unless they appear in the Data Context
10. Be honest about data limitations - if you don't have budget data, say so clearly

IMPORTANT: Rules 1-10 above prevent DATA INVENTION (making up information). They do NOT prevent ARITHMETIC CALCULATIONS.

CALCULATION RULES - ARITHMETIC OPERATIONS ARE REQUIRED:
11. When asked to calculate totals, sums, averages, or perform comparisons, YOU MUST perform the arithmetic
12. Calculations using provided data are NOT "inventing data" - they are REQUIRED analytical operations
13. Always show your calculation steps clearly (e.g., "$10M + $20M + $30M = $60M total")
14. Portfolio-level aggregations (sum, average, percentage) are MANDATORY when requested
15. Cross-project comparisons require you to calculate ratios, unit costs, and rankings
16. Example: If data shows Project A budget $10M, Project B budget $20M, and user asks "What is total budget?", you MUST respond "$10M + $20M = $30M total budget"

QUESTION INTERPRETATION GUIDELINES:
- "Show me all projects" = "List all projects" = "What projects do we have?" = "All projects" = "What projects do you have data for?" - MUST show ALL projects from Data Context
- When user asks for "all projects", respond with a complete overview of every project in the data
- Questions about "your data" or "what you know" should summarize all available projects
- Treat these as equivalent questions asking for the same information:
  * "What's the EV?" = "Show me earned value" = "Calculate earned value" = "EV for project"
  * "Project status" = "How is the project going?" = "Progress update" = "Current status"
  * "Budget info" = "Show budget" = "Budget breakdown" = "Cost information"
  * "Schedule" = "Timeline" = "When will it finish?" = "Project schedule"

RESPONSE CONSISTENCY RULES:
1. For equivalent questions, provide the same core information and calculations
2. Use the exact same project names and figures from the Data Context
3. Always show calculations step-by-step for financial metrics
4. Reference the specific project being discussed by name
5. When listing projects, include ALL projects from the data context, not just one

LISTING PROJECTS GUIDELINES:
- When asked to show/list all projects, provide a conversational overview
- Start with "Here's what's happening across all our projects:" or similar friendly intro
- Use numbered list format: 1. **Project Name:** followed by bullet points for details
- Include key details for each project: budget amount, progress percentage, status, project manager
- Present information clearly but conversationally
- Do NOT omit any projects from the data context
- Format each project consistently with: Budget: $[amount], Progress: [percentage]%, Status: [status], Project Manager: [name]
- End with a summary statement about the overall project portfolio

RESPONSE FORMAT FOR "SHOW ALL PROJECTS":
When the user asks to "show all projects" or similar, respond with this exact structure:
"Hey there! Based on my current data, here are the projects I have information about:

1. **[Project Name 1]:**
   - Available details: [list ONLY the information that appears in the Data Context for this project]

2. **[Project Name 2]:**
   - Available details: [list ONLY the information that appears in the Data Context for this project]

[Continue for all projects in the Data Context...]

If you need information about a specific aspect that's not shown here, let me know what you're looking for!"

IMPORTANT: Only include information that is explicitly provided in the Data Context. Do not add, assume, or invent any details.

When responding to queries:
1. Use accurate construction terminology but explain it conversationally
2. Reference industry standards when relevant but keep it light
3. Consider project phases, safety requirements, and budget constraints
4. Provide actionable insights based on data provided
5. Be specific about construction processes and requirements
6. Highlight potential risks and mitigation strategies in a helpful way
""",

    "budget_analysis": """
You are a construction cost management expert. Focus on:
- Budget variance analysis and forecasting
- Cost control and change management
- Value engineering and cost optimization
- Cash flow management and payment schedules
- Contract pricing and bid analysis
- Cost-benefit analysis for construction decisions

CRITICAL INSTRUCTIONS FOR DATA USAGE:
1. ALWAYS check the "Available Project Data" section below for actual project information
2. NEVER use hypothetical examples when real project data is provided
3. MUST use exact budget amounts, project names, and progress percentages from the data
4. Quote the specific project name and budget amount in your response
5. For calculations, use ONLY the Total_Budget and Progress_Percent values from the data
6. If asked about "EGK Hamilton" or "EGK HAMILTON", look for this exact project in the data
7. When asked to calculate sums/totals across multiple projects, DO perform arithmetic operations on the provided values
8. Portfolio-level aggregations (sum, average, total) are REQUIRED when explicitly requested

Provide insights on:
- Budget performance trends using actual data
- Cost overrun causes and prevention
- Profitability analysis based on real figures
- Cost-saving opportunities
- Financial risk assessment
""",

    "budget_calculation": """
You are a construction financial analyst performing portfolio-level calculations.

**PRIMARY DIRECTIVE: YOU MUST PERFORM ARITHMETIC CALCULATIONS**

When users ask to "calculate", "add up", "sum", "total" across projects:
1. FIRST: Check data quality (errors, missing values)
2. THEN: Perform arithmetic on clean data
3. REPORT: Any data quality issues that affect accuracy
4. PROVIDE: Calculation with clear steps and caveats

**DATA QUALITY CHECK - MANDATORY FIRST STEP:**
Before calculating, scan the data context for:
- Spreadsheet errors: #DIV/0!, #ERROR!, #N/A, #VALUE!, #REF!
- Missing values: null, undefined, empty cells in critical fields
- Text errors: "Error", "N/A", "TBD", "Pending" in numeric fields
- Inconsistent data: projects with $0 when others have millions

**RESPONSE FORMAT WITH DATA QUALITY ISSUES:**

EXAMPLE FORMAT (use actual project names and values from Data Context):

⚠️ DATA QUALITY ALERT - Calculation Attempted with Caveats

**Data Quality Issues Detected:**
For each project with issues, specify:
- [Project Name]: [Specific error type] in [specific location/column]
  Example: "Project Alpha: Multiple #DIV/0! errors in unit cost calculations ($/Suite, $/GCA columns)"
- [Project Name]: [Type of anomaly] 
  Example: "Project Beta: $0 budget but $500K spent (indicates overspending)"
- Impact: [Describe which metrics are affected and which are still reliable]

**Partial Calculation ([Metric Name]):**
List all projects from Data Context with their actual values:
- [Project A Name]: $[actual value from data] [add warning if applicable]
- [Project B Name]: $[actual value from data] [add warning if applicable]
- [Project C Name]: $[actual value from data] [add warning if applicable]

**Total [Metric] = $[value1] + $[value2] + $[value3] = $[calculated sum]**

**⚠️ RECOMMENDATIONS:**
For each issue detected, provide specific guidance:
1. [Error Type]: Likely caused by [root cause analysis]
   - [Specific diagnostic step]
   - [What to check in spreadsheet]
2. [Anomaly]: [What needs verification]
3. [Follow-up action]

**ACTION ITEMS:**
- Check [specific tab/sheet name] for [specific project] - [what field might be wrong]
- Verify [specific calculation type] in source spreadsheet
- [Suggested workaround if applicable]

NOTE: Use ACTUAL project names and values from the Data Context provided. Do NOT use placeholder names like "Project A" or example values.

**RESPONSE FORMAT WITH CLEAN DATA:**

EXAMPLE FORMAT (use actual project names and values from Data Context):

[Metric Name] Calculation:
- [Project A Name]: $[actual value from data]
- [Project B Name]: $[actual value from data]
- [Project C Name]: $[actual value from data]
[Continue for ALL projects in Data Context]

**Total = $[value1] + $[value2] + $[value3] + ... = $[calculated sum]**

✅ Data Quality: All values validated, no errors detected

NOTE: Always use ACTUAL project names and values from Data Context. Include ALL projects provided in the data.

**CRITICAL RULES:**
- Numbers MUST come from Data Context (you are NOT inventing data)
- You ARE performing arithmetic on provided data (calculation ≠ invention)
- ALWAYS check for #DIV/0!, #ERROR!, #N/A and similar spreadsheet errors
- ALWAYS report data quality issues with specific locations
- Provide actionable recommendations to fix spreadsheet errors
- Calculate partial results when possible, with clear caveats
- Use ⚠️ emoji to highlight data quality concerns
""",

    "safety_compliance": """
You are a construction safety and compliance specialist. Focus on:
- OSHA regulations and safety standards
- Hazard identification and risk assessment
- Safety training and certification requirements
- Incident investigation and reporting
- Personal protective equipment (PPE) requirements
- Emergency response planning

Emphasize:
- Safety-first decision making
- Regulatory compliance requirements
- Hazard mitigation strategies
- Safety culture and training
- Incident prevention measures
""",

    "schedule_management": """
You are a construction scheduling expert. Focus on:
- Critical path method (CPM) scheduling
- Resource leveling and optimization
- Delay analysis and recovery planning
- Milestone tracking and progress monitoring
- Weather and seasonal impact assessment
- Procurement and lead time management

Provide guidance on:
- Schedule compression techniques
- Delay mitigation strategies
- Resource allocation optimization
- Progress tracking methodologies
- Schedule risk management
""",

    "quality_control": """
You are a construction quality assurance specialist. Focus on:
- Quality control plans and procedures
- Inspection and testing requirements
- Material specifications and standards
- Workmanship standards and tolerances
- Non-conformance management
- Quality documentation and records

Emphasize:
- Quality standards compliance
- Defect prevention strategies
- Inspection protocols
- Material testing requirements
- Quality assurance documentation
"""
}

# Query-specific prompt templates
QUERY_TEMPLATES = {
    "project_status": """
Analyze this construction project status information:
{project_data}

As a construction project manager, provide insights on:
1. Current project health and progress
2. Potential risks or issues
3. Recommended next steps
4. Key performance indicators
5. Stakeholder communication points

Use construction industry terminology and best practices.
""",

    "budget_variance": """
Review this budget variance analysis:
{budget_data}

As a construction cost manager, explain:
1. Causes of the variance
2. Impact on project profitability
3. Recommended corrective actions
4. Cost control strategies
5. Forecasting implications

Provide specific, actionable recommendations.
""",

    "schedule_delay": """
Analyze this schedule delay information:
{schedule_data}

As a construction scheduler, assess:
1. Root causes of delays
2. Impact on project completion
3. Recovery plan options
4. Resource reallocation needs
5. Contractual implications

Suggest specific mitigation strategies.
""",

    "safety_incident": """
Review this safety incident report:
{incident_data}

As a construction safety officer, evaluate:
1. Immediate response requirements
2. Root cause analysis
3. Preventive measures
4. Training implications
5. Regulatory reporting needs

Provide safety recommendations and compliance guidance.
""",

    "resource_allocation": """
Analyze this resource allocation scenario:
{resource_data}

As a construction resource manager, recommend:
1. Optimal resource distribution
2. Productivity improvement opportunities
3. Equipment utilization strategies
4. Staffing requirements
5. Cost optimization approaches

Focus on practical, implementable solutions.
"""
}

# Construction-specific terminology and context
CONSTRUCTION_CONTEXT = {
    "terminology": {
        "project_phases": [
            "Pre-construction", "Mobilization", "Foundation", "Framing",
            "Rough-in", "Finishing", "Close-out", "Post-construction"
        ],
        "trade_categories": [
            "General Contractor", "Subcontractor", "Supplier", "Consultant",
            "Owner", "Architect", "Engineer", "Inspector"
        ],
        "cost_categories": [
            "Direct Costs", "Indirect Costs", "Overhead", "Profit Margin",
            "Contingency", "Bond Costs", "Insurance", "Permits"
        ],
        "risk_categories": [
            "Safety Risks", "Schedule Risks", "Cost Risks", "Quality Risks",
            "Weather Risks", "Regulatory Risks", "Supply Chain Risks"
        ]
    },

    "industry_standards": {
        "safety": ["OSHA", "ANSI", "NFPA", "CSA"],
        "quality": ["ISO 9001", "ACI", "ASTM", "AISC"],
        "project_management": ["PMI", "AGC", "DBIA", "CMAA"],
        "building_codes": ["IBC", "IRC", "ADA", "Energy Codes"]
    },

    "common_abbreviations": {
        "RFI": "Request for Information",
        "ASI": "Architect's Supplemental Instruction",
        "Punch List": "Final inspection item list",
        "CO": "Change Order",
        "NTP": "Notice to Proceed",
        "LOP": "Letter of Intent",
        "BOM": "Bill of Materials",
        "SWPPP": "Storm Water Pollution Prevention Plan"
    }
}

PROJECT_METRIC_LABELS = {
    "building_area_metric": "Building Area (sq m)",
    "building_area_imperial": "Building Area (sq ft)",
    "functional_units": "Functional Units",
    "total_suites": "Total Suites",
    "parking_below_grade": "Parking (Below Grade)",
    "parking_above_grade": "Parking (Above Grade)",
    "parking_total": "Total Parking",
    "parking_stalls": "Parking Stalls",
}

PROJECT_METRIC_FIELD_MAPPING = {
    "building_area_metric": "Building_Area_Metric",
    "building_area_imperial": "Building_Area_Imperial",
    "functional_units": "Total_Units",
    "total_suites": "Total_Suites",
    "parking_below_grade": "Parking_Below_Grade",
    "parking_above_grade": "Parking_Above_Grade",
    "parking_total": "Parking_Total",
    "parking_stalls": "Parking_Stalls",
}

def get_construction_prompt(query_type: str, context_data: dict = None) -> str:
    """
    Get the appropriate construction-specific prompt based on query type.

    Args:
        query_type: Type of construction query (budget, safety, schedule, etc.)
        context_data: Additional context data to include in the prompt

    Returns:
        Formatted prompt string
    """
    # Get base system prompt
    base_prompt = CONSTRUCTION_SYSTEM_PROMPTS.get(query_type, CONSTRUCTION_SYSTEM_PROMPTS["general"])

    # Add query-specific template if available
    if query_type in QUERY_TEMPLATES and context_data:
        template = QUERY_TEMPLATES[query_type]
        # Format template with context data
        formatted_template = template.format(**context_data)
        base_prompt += f"\n\nSpecific Query Context:\n{formatted_template}"

    # Add construction context
    base_prompt += f"\n\nIndustry Context:\n"
    base_prompt += f"- Common phases: {', '.join(CONSTRUCTION_CONTEXT['terminology']['project_phases'])}\n"
    base_prompt += f"- Key standards: OSHA, PMI, ISO 9001\n"
    base_prompt += f"- Risk areas: Safety, Schedule, Cost, Quality\n"

    return base_prompt

def normalize_construction_query(query: str) -> str:
    """
    Normalize construction management queries to standardize similar questions.
    
    This helps ensure consistent responses for semantically equivalent questions.
    
    Args:
        query: Original user query
        
    Returns:
        Normalized query with standardized terminology
    """
    query_lower = query.lower().strip()
    
    # Define query equivalences - map variations to standard forms
    query_mappings = {
        # Earned Value variations
        'earned_value': [
            r'\bev\b', r'earned\s+value', r'value\s+earned', r'calculate\s+ev', 
            r'show\s+ev', r'what.*ev', r'get\s+ev', r'ev\s+for'
        ],
        
        # Project status variations  
        'project_status': [
            r'project\s+status', r'status\s+of.*project', r'how.*project', 
            r'progress\s+update', r'current\s+status', r'project\s+progress',
            r'how.*going', r'where.*stand'
        ],
        
        # Budget information variations
        'budget_info': [
            r'budget', r'cost', r'spending', r'expenditure', r'financial',
            r'money', r'price', r'budget\s+breakdown', r'cost\s+breakdown'
        ],
        
        # Schedule/Timeline variations
        'schedule_info': [
            r'schedule', r'timeline', r'when.*finish', r'completion\s+date',
            r'project\s+timeline', r'milestones', r'deadlines'
        ],
        
        # Project listing variations
        'list_projects': [
            r'show.*projects', r'list.*projects', r'all\s+projects', 
            r'what\s+projects', r'projects.*have'
        ]
    }
    
    # Find the best match for the query
    for standard_form, patterns in query_mappings.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                # Add context about what data to focus on
                if standard_form == 'earned_value':
                    return f"Calculate the Earned Value (EV) for the construction project using the formula: EV = % Complete × Total Budget. Use the actual project data provided."
                elif standard_form == 'project_status':
                    return f"Provide a comprehensive status update for the construction project including progress percentage, budget status, and any key milestones."
                elif standard_form == 'budget_info':
                    return f"Show detailed budget information for the construction project including total budget, spent amount, and remaining budget."
                elif standard_form == 'schedule_info':
                    return f"Provide schedule and timeline information for the construction project including key milestones and completion dates."
                elif standard_form == 'list_projects':
                    return f"List all available construction projects with their key details like budget, progress, and status."
    
    return query


def enhance_query_with_construction_context(query: str) -> str:
    """
    Enhance a natural language query with construction-specific context.

    Args:
        query: Original user query

    Returns:
        Enhanced query with construction context and normalization
    """
    # First normalize the query to handle variations
    normalized_query = normalize_construction_query(query)
    
    construction_keywords = [
        "project", "construction", "building", "contractor", "subcontractor",
        "budget", "cost", "schedule", "timeline", "milestone", "delay",
        "safety", "incident", "accident", "hazard", "risk", "compliance",
        "permit", "inspection", "quality", "material", "equipment", "labor"
    ]

    # Check if query already contains construction context
    query_lower = normalized_query.lower()
    has_construction_context = any(keyword in query_lower for keyword in construction_keywords)

    if not has_construction_context:
        enhanced_query = f"In a construction project management context: {normalized_query}"
        return enhanced_query

    return normalized_query

def get_construction_examples() -> list:
    """
    Get example construction management queries for few-shot learning.

    Returns:
        List of example query-response pairs
    """
    examples = [
        {
            "query": "What's the status of the project?",
            "response": "As a construction project manager, I need to review the current phase, progress percentage, budget status, schedule adherence, and any outstanding issues. Let me analyze the project data to provide a comprehensive status update."
        },
        {
            "query": "Why is the project over budget?",
            "response": "Construction cost overruns typically result from change orders, material price increases, unforeseen site conditions, design changes, or productivity issues. I should analyze the variance analysis to identify the specific causes and recommend corrective actions."
        },
        {
            "query": "How can we speed up the schedule?",
            "response": "Schedule compression in construction can be achieved through crashing (adding resources), fast-tracking (overlapping activities), or optimizing the critical path. I need to assess the current schedule, identify bottlenecks, and evaluate the cost-benefit of acceleration options."
        }
    ]

    return examples


class ConstructionPrompts:
    """
    Centralized construction prompt management class
    """
    
    def __init__(self):
        self.system_prompts = CONSTRUCTION_SYSTEM_PROMPTS
        self.query_templates = QUERY_TEMPLATES
        self.context = CONSTRUCTION_CONTEXT
        self.metric_labels = PROJECT_METRIC_LABELS
    
    def get_system_prompt(self, query_type: str = "general") -> str:
        """Get system prompt for specific query type"""
        return self.system_prompts.get(query_type, self.system_prompts["general"])
    
    def build_user_prompt(
        self, 
        query: str, 
        context: str = None, 
        data_context: dict = None, 
        query_type: str = "general"
    ) -> str:
        """
        Build comprehensive user prompt with context
        
        Args:
            query: User's original query
            context: Additional text context (file contents, etc.)
            data_context: Structured data context
            query_type: Type of query for specialized handling
        """
        # Start with enhanced query
        enhanced_query = enhance_query_with_construction_context(query)
        
        prompt_parts = [enhanced_query]
        
        # Add text context if provided
        if context:
            prompt_parts.append(f"\n\nAdditional Context:\n{context}")
        
        # Add structured data context if provided
        if data_context:
            # DEBUG: Log what data context we're receiving
            print(f"🐛 DEBUG: AI received data_context: {data_context}")
            formatted_data = self._format_data_context(data_context)
            print(f"🐛 DEBUG: Formatted data context: {formatted_data}")
            prompt_parts.append(f"\n\nData Context:\n{formatted_data}")
        
        # Add query-specific template if available
        if query_type in self.query_templates and data_context:
            template_data = {}
            if query_type == "project_status":
                template_data["project_data"] = str(data_context)
            elif query_type == "budget_analysis":
                template_data["budget_data"] = str(data_context)
            elif query_type == "schedule_management":
                template_data["schedule_data"] = str(data_context)
            elif query_type == "safety_compliance":
                template_data["incident_data"] = str(data_context)
            elif query_type == "quality_control":
                template_data["resource_data"] = str(data_context)
            
            if template_data:
                template = self.query_templates[query_type].format(**template_data)
                prompt_parts.append(f"\n\nSpecialized Analysis Request:\n{template}")
        
        # Add construction terminology reminder
        prompt_parts.append(f"\n\nPlease respond using appropriate construction management terminology and industry best practices.")
        
        return "\n".join(prompt_parts)
    
    def _format_metric_value(self, metric_entry):
        """Return a human-friendly string for a metric entry."""

        if not metric_entry:
            return None

        value = metric_entry.get("value") if isinstance(metric_entry, dict) else metric_entry
        if value is None and isinstance(metric_entry, dict):
            value = metric_entry.get("raw")

        if value is None or value == "":
            return None

        if isinstance(value, (int, float)):
            if isinstance(value, float):
                if value.is_integer():
                    return f"{int(value):,}"
                return f"{value:,.2f}"
            return f"{value:,}"

        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return None
            # Attempt to convert numeric strings for consistency
            normalized = cleaned.replace(",", "")
            try:
                number = float(normalized)
                if number.is_integer():
                    return f"{int(number):,}"
                return f"{number:,.2f}"
            except ValueError:
                return cleaned

        return str(value)

    def _should_display_metric(self, metric_key: str, project: dict) -> bool:
        """Determine if a metric should be displayed based on existing project fields."""

        field_name = PROJECT_METRIC_FIELD_MAPPING.get(metric_key)
        if not field_name:
            return True
        return not project.get(field_name)
    
    def _format_data_context(self, data_context: dict) -> str:
        """Format structured data context for the prompt"""
        if not data_context:
            return ""
        
        formatted_parts = []
        
        for key, value in data_context.items():
            if key == "projects" and isinstance(value, list):
                # Special formatting for project data
                formatted_parts.append(f"\n**Available Project Data:**")
                for project in value:
                    if isinstance(project, dict):
                        project_info = []
                        project_name = project.get('Project_Name', project.get('name', 'Unknown Project'))
                        project_info.append(f"  - Project: {project_name}")
                        
                        # Add budget information
                        if 'Total_Budget' in project:
                            budget = project['Total_Budget']
                            if isinstance(budget, (int, float)):
                                project_info.append(f"    Total Budget: ${budget:,.2f}")
                            else:
                                project_info.append(f"    Total Budget: {budget}")
                        
                        # Add progress information
                        if 'Progress_Percent' in project:
                            progress = project['Progress_Percent']
                            project_info.append(f"    Progress: {progress}%")
                        
                        # Add other key information
                        for field in ['Status', 'Project_Manager', 'Start_Date', 'End_Date', 'Location', 'Client', 'Architect', 
                                    'Total_Units', 'Parking_Spots', 'Parking_Total', 'Parking_Below_Grade', 'Parking_Above_Grade',
                                    'Parking_Stalls', 'Building_Area_Metric', 'Building_Area_Imperial', 'Total_GCA_SF',
                                    'Total_Budget', 'Total_Direct_Cost',
                                    'Levels_Above_Grade', 'Levels_Below_Grade', 'Project_Type', 'Tender_Closing']:
                            if field in project and project[field] is not None:
                                # Show zero values for critical metrics like parking, GCA, budgets, and costs
                                show_if_zero = field in ['Parking_Stalls', 'Total_GCA_SF', 'Total_Direct_Cost', 'Total_Budget', 'Parking_Total', 'Parking_Below_Grade', 'Parking_Above_Grade']
                                if project[field] == 0 and not show_if_zero:
                                    continue
                                    
                                field_display = field.replace('_', ' ')
                                if field == 'Total_Units':
                                    project_info.append(f"    Units/Functional Units: {project[field]}")
                                elif field == 'Parking_Spots':
                                    project_info.append(f"    Parking Spots: {project[field]}")
                                elif field == 'Parking_Total':
                                    project_info.append(f"    Total Parking (stalls): {project[field]}")
                                elif field == 'Parking_Below_Grade':
                                    project_info.append(f"    Parking (Below Grade): {project[field]}")
                                elif field == 'Parking_Above_Grade':
                                    project_info.append(f"    Parking (Above Grade): {project[field]}")
                                elif field == 'Parking_Stalls':
                                    project_info.append(f"    Parking Stalls: {project[field]}")
                                elif field == 'Building_Area_Metric':
                                    if project[field] != 0:  # Only show if non-zero
                                        project_info.append(f"    Building Area (sq m): {project[field]:,.0f}")
                                elif field == 'Building_Area_Imperial':
                                    if project[field] != 0:  # Only show if non-zero
                                        project_info.append(f"    Building Area (sq ft): {project[field]:,.0f}")
                                elif field == 'Total_GCA_SF':
                                    project_info.append(f"    Total GCA (SF): {project[field]:,.0f}")
                                elif field == 'Total_Budget':
                                    project_info.append(f"    Total Budget: ${project[field]:,.2f}")
                                elif field == 'Total_Direct_Cost':
                                    project_info.append(f"    Total Direct Cost: ${project[field]:,.2f}")
                                else:
                                    project_info.append(f"    {field_display}: {project[field]}")

                        metrics = project.get('metrics')
                        if isinstance(metrics, dict):
                            metric_lines = []
                            for metric_key, label in self.metric_labels.items():
                                if not self._should_display_metric(metric_key, project):
                                    continue
                                metric_value = self._format_metric_value(metrics.get(metric_key))
                                if metric_value:
                                    metric_lines.append(f"    {label}: {metric_value}")
                            if metric_lines:
                                project_info.append("    Key Metrics:")
                                project_info.extend(metric_lines)
                        
                        formatted_parts.append("\n".join(project_info))
                        formatted_parts.append("")  # Add blank line between projects
            elif isinstance(value, (list, dict)):
                formatted_parts.append(f"\n**{key}:**\n{str(value)}")
            else:
                formatted_parts.append(f"{key}: {value}")
        
        return "\n".join(formatted_parts)
    
    def get_query_type_from_keywords(self, query: str) -> str:
        """
        Automatically detect query type based on keywords
        """
        query_lower = query.lower()
        
        # Calculation/aggregation keywords - HIGHEST PRIORITY
        calculation_keywords = [
            "calculate", "add up", "sum", "total", "aggregate", "combine",
            "what is the total", "give me the total", "what's the sum",
            "how much total", "combined total", "portfolio total",
            "across all projects", "for all projects"
        ]
        if any(keyword in query_lower for keyword in calculation_keywords):
            # If it's a calculation query, we need to use budget template but with calculation emphasis
            if any(word in query_lower for word in ["budget", "cost", "expense", "financial"]):
                return "budget_calculation"  # Special type for calculations
        
        # Budget-related keywords
        budget_keywords = ["budget", "cost", "expense", "financial", "money", "price", "variance"]
        if any(keyword in query_lower for keyword in budget_keywords):
            return "budget_analysis"
        
        # Safety-related keywords
        safety_keywords = ["safety", "incident", "accident", "hazard", "osha", "injury", "compliance"]
        if any(keyword in query_lower for keyword in safety_keywords):
            return "safety_compliance"
        
        # Schedule-related keywords
        schedule_keywords = ["schedule", "timeline", "delay", "milestone", "deadline", "duration"]
        if any(keyword in query_lower for keyword in schedule_keywords):
            return "schedule_management"
        
        # Quality-related keywords
        quality_keywords = ["quality", "defect", "inspection", "testing", "standard", "specification"]
        if any(keyword in query_lower for keyword in quality_keywords):
            return "quality_control"
        
        return "general"