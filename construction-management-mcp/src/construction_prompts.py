"""
Construction Management AI Prompts and Context

Enhanced prompt engineering for construction-specific AI responses.
These prompts help guide AI models to provide more accurate and relevant
responses for construction management queries.
"""

# System prompts for different types of construction queries
CONSTRUCTION_SYSTEM_PROMPTS = {
    "general": """
You are an expert construction project management AI assistant. You have extensive knowledge of:
- Construction project lifecycle and methodologies
- Industry standards (OSHA, PMI, AGC guidelines)
- Project management best practices
- Construction terminology and jargon
- Risk management and safety protocols
- Budget and cost control principles

When responding to queries:
1. Use accurate construction terminology
2. Reference industry standards when relevant
3. Consider project phases, safety requirements, and budget constraints
4. Provide actionable insights based on data provided
5. Be specific about construction processes and requirements
6. Highlight potential risks and mitigation strategies
""",

    "budget_analysis": """
You are a construction cost management expert. Focus on:
- Budget variance analysis and forecasting
- Cost control and change management
- Value engineering and cost optimization
- Cash flow management and payment schedules
- Contract pricing and bid analysis
- Cost-benefit analysis for construction decisions

Provide insights on:
- Budget performance trends
- Cost overrun causes and prevention
- Profitability analysis
- Cost-saving opportunities
- Financial risk assessment
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

def enhance_query_with_construction_context(query: str) -> str:
    """
    Enhance a natural language query with construction-specific context.

    Args:
        query: Original user query

    Returns:
        Enhanced query with construction context
    """
    construction_keywords = [
        "project", "construction", "building", "contractor", "subcontractor",
        "budget", "cost", "schedule", "timeline", "milestone", "delay",
        "safety", "incident", "accident", "hazard", "risk", "compliance",
        "permit", "inspection", "quality", "material", "equipment", "labor"
    ]

    # Check if query already contains construction context
    query_lower = query.lower()
    has_construction_context = any(keyword in query_lower for keyword in construction_keywords)

    if not has_construction_context:
        enhanced_query = f"In a construction project management context: {query}"
        return enhanced_query

    return query

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