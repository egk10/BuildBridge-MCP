#!/usr/bin/env python3
"""
Construction Management MCP with Enhanced AI Integration

This script demonstrates how to integrate enhanced prompt engineering
and fine-tuned LLM capabilities into the Construction Management MCP server.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from query_processor import QueryProcessor
from construction_prompts import get_construction_prompt, enhance_query_with_construction_context

class EnhancedConstructionMCP:
    """
    Enhanced Construction MCP with AI integration capabilities

    Supports both:
    1. Enhanced prompt engineering for immediate improvements
    2. Fine-tuned LLM integration for advanced capabilities
    """

    def __init__(self, use_fine_tuned_llm=False):
        """
        Initialize enhanced MCP

        Args:
            use_fine_tuned_llm: Whether to use fine-tuned local LLM
        """
        self.use_fine_tuned_llm = use_fine_tuned_llm
        self.fine_tuned_model = None

        if use_fine_tuned_llm:
            self._load_fine_tuned_model()

    def _load_fine_tuned_model(self):
        """Load the fine-tuned construction LLM"""
        try:
            # Import here to avoid dependency if not using fine-tuned model
            from inference_construction_llm import ConstructionLLM
            self.fine_tuned_model = ConstructionLLM()
            print("✅ Fine-tuned construction LLM loaded successfully")
        except ImportError:
            print("⚠️ Fine-tuned model not available. Using enhanced prompts only.")
            self.use_fine_tuned_llm = False

    def process_construction_query(self, query: str) -> dict:
        """
        Process a construction management query with enhanced AI capabilities

        Args:
            query: Natural language construction query

        Returns:
            Dictionary with processed results and AI enhancements
        """
        # Initialize basic MCP processing
        # Note: In real implementation, this would use the full MCP pipeline
        processor = QueryProcessor(None, None, None)  # Mock connectors for demo

        # Parse query with enhanced context
        parsed_query = processor.parse_query(query)

        # Get construction-specific prompt
        construction_prompt = parsed_query.get('construction_prompt', '')

        # Prepare response
        response = {
            'original_query': query,
            'enhanced_query': parsed_query.get('enhanced_query', query),
            'query_type': parsed_query.get('type', 'unknown'),
            'construction_context': construction_prompt,
            'ai_enhancement': self._get_ai_enhancement(query, parsed_query),
            'recommendations': self._get_construction_recommendations(parsed_query)
        }

        return response

    def _get_ai_enhancement(self, query: str, parsed_query: dict) -> str:
        """
        Get AI enhancement for the query

        Args:
            query: Original query
            parsed_query: Parsed query information

        Returns:
            AI-enhanced response or guidance
        """
        query_type = parsed_query.get('type', 'general')

        if self.use_fine_tuned_llm and self.fine_tuned_model:
            # Use fine-tuned model for advanced responses
            try:
                enhanced_prompt = f"""
                As a construction project management expert, analyze and respond to: {query}

                Consider:
                - Industry standards and best practices
                - Safety and compliance requirements
                - Project management methodologies
                - Risk assessment and mitigation
                - Cost control and efficiency

                Provide specific, actionable insights.
                """

                ai_response = self.fine_tuned_model.generate_response(enhanced_prompt)
                return f"🤖 **AI-Enhanced Analysis:**\n{ai_response}"

            except Exception as e:
                print(f"Error with fine-tuned model: {e}")
                return self._get_enhanced_prompt_response(query, query_type)

        else:
            # Use enhanced prompt engineering
            return self._get_enhanced_prompt_response(query, query_type)

    def _get_enhanced_prompt_response(self, query: str, query_type: str) -> str:
        """
        Get enhanced response using prompt engineering

        Args:
            query: Original query
            query_type: Type of construction query

        Returns:
            Enhanced response with construction context
        """
        base_responses = {
            'budget_analysis': """
            💰 **Budget Analysis Guidance:**
            - Use Earned Value Management (EVM) for progress tracking
            - Monitor variance between planned vs actual costs
            - Consider contingency reserves (typically 5-10% of project cost)
            - Track change orders and their impact on budget
            - Regular cost forecasting helps prevent overruns
            """,

            'safety_compliance': """
            ⚠️ **Safety & Compliance Considerations:**
            - Ensure OSHA compliance for all safety protocols
            - Regular safety training and toolbox talks required
            - Personal Protective Equipment (PPE) must be provided and used
            - Incident reporting within 24 hours for recordable incidents
            - Safety inspections should be conducted weekly
            """,

            'schedule_management': """
            📅 **Schedule Management Best Practices:**
            - Use Critical Path Method (CPM) for schedule analysis
            - Identify and monitor critical path activities
            - Build in schedule contingency (typically 10-15%)
            - Regular progress updates and milestone tracking
            - Weather and supply chain delays are common risks
            """,

            'project_status': """
            📊 **Project Status Assessment:**
            - Progress measured as: (Earned Value ÷ Planned Value) × 100
            - Key metrics: Schedule Performance Index (SPI), Cost Performance Index (CPI)
            - Risk assessment should cover safety, quality, budget, and schedule
            - Stakeholder communication is critical for project success
            - Regular status reports help identify issues early
            """
        }

        return base_responses.get(query_type, """
        🏗️ **Construction Project Management Context:**
        - Projects follow standardized phases: Pre-construction, Mobilization, Foundation, Framing, Finishing, Close-out
        - Industry standards: OSHA (safety), PMI (project management), ISO 9001 (quality)
        - Key success factors: Safety, Quality, Budget, Schedule, Stakeholder satisfaction
        - Risk management covers technical, financial, and operational risks
        """)

    def _get_construction_recommendations(self, parsed_query: dict) -> list:
        """
        Get construction-specific recommendations

        Args:
            parsed_query: Parsed query information

        Returns:
            List of actionable recommendations
        """
        query_type = parsed_query.get('type', 'general')

        recommendations = {
            'budget_analysis': [
                "Implement monthly budget reviews with variance analysis",
                "Establish change order approval process",
                "Monitor material price trends and escalation clauses",
                "Use cost forecasting for better cash flow management",
                "Consider value engineering for cost optimization"
            ],

            'safety_compliance': [
                "Conduct weekly safety inspections and toolbox talks",
                "Ensure all workers have current safety training certifications",
                "Maintain comprehensive incident reporting system",
                "Regular PPE inspections and replacement program",
                "Develop emergency response and evacuation procedures"
            ],

            'schedule_management': [
                "Identify and monitor critical path activities",
                "Build schedule contingency into project timeline",
                "Regular progress meetings with all stakeholders",
                "Weather monitoring and delay contingency planning",
                "Resource leveling to optimize productivity"
            ],

            'project_status': [
                "Establish clear KPIs and milestone tracking",
                "Regular stakeholder communication and reporting",
                "Risk register maintenance and monitoring",
                "Quality control and assurance processes",
                "Change management and scope control procedures"
            ]
        }

        return recommendations.get(query_type, [
            "Establish clear project objectives and success criteria",
            "Develop comprehensive project management plan",
            "Implement regular monitoring and reporting processes",
            "Maintain open communication with all stakeholders",
            "Document lessons learned for future projects"
        ])

def demo_enhanced_mcp():
    """Demonstrate the enhanced MCP capabilities"""

    print("🏗️ Enhanced Construction Management MCP Demo")
    print("=" * 60)

    # Initialize enhanced MCP
    mcp = EnhancedConstructionMCP(use_fine_tuned_llm=False)  # Set to True if you have fine-tuned model

    # Test queries
    test_queries = [
        "What's the budget status for the Downtown Office Building?",
        "How can we improve safety on construction sites?",
        "What are the main phases of a construction project?",
        "How do you handle construction schedule delays?",
        "What causes cost overruns in construction projects?"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Query {i}: {query}")
        print("-" * 50)

        result = mcp.process_construction_query(query)

        print(f"📋 Query Type: {result['query_type']}")
        print(f"🔧 Enhanced Query: {result['enhanced_query'][:100]}...")
        print(f"{result['ai_enhancement']}")
        print("\n💡 Recommendations:")
        for rec in result['recommendations'][:3]:  # Show first 3
            print(f"  • {rec}")

def create_mcp_integration_example():
    """Create example of how to integrate with existing MCP server"""

    integration_code = '''
# Example: Integrating Enhanced AI into your MCP server

from enhanced_construction_mcp import EnhancedConstructionMCP

# Initialize enhanced MCP
enhanced_mcp = EnhancedConstructionMCP(use_fine_tuned_llm=False)

@mcp.tool()
def analyze_project_with_ai(project_id: str, analysis_type: str) -> str:
    """
    Analyze project with enhanced AI capabilities

    Args:
        project_id: Project identifier
        analysis_type: Type of analysis (budget, schedule, safety, etc.)

    Returns:
        AI-enhanced analysis
    """
    # Get basic project data
    project_data = query_processor.get_project_status(project_id)

    # Create AI-enhanced query
    query = f"Analyze this {analysis_type} data for project {project_id}: {project_data}"

    # Process with enhanced AI
    result = enhanced_mcp.process_construction_query(query)

    # Return enhanced response
    return f"""
    📊 **AI-Enhanced {analysis_type.title()} Analysis**

    {result['ai_enhancement']}

    🎯 **Key Recommendations:**
    {chr(10).join(f"• {rec}" for rec in result['recommendations'][:5])}
    """

# Add to your MCP server
# enhanced_mcp = EnhancedConstructionMCP()
'''

    with open("mcp_integration_example.py", "w") as f:
        f.write(integration_code)

    print("✅ Created MCP integration example: mcp_integration_example.py")

if __name__ == "__main__":
    demo_enhanced_mcp()
    create_mcp_integration_example()

    print("\n🎉 Demo complete!")
    print("\n📋 Next steps:")
    print("1. Review the enhanced responses above")
    print("2. Try the MCP integration example")
    print("3. Set up fine-tuning environment if desired")
    print("4. Customize prompts for your specific needs")

if __name__ == "__main__":
    demo_enhanced_mcp()
    create_mcp_integration_example()</content>
<parameter name="filePath">/home/egk/buildbridge-MCP/BuildBridge-MCP/construction-management-mcp/enhanced_construction_mcp.py