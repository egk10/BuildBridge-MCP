#!/usr/bin/env python3
"""
Construction Management Fine-tuning Dataset Generator

Creates a fine-tuning dataset from existing construction project data
for training a domain-specific LLM.
"""

import json
import csv
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import random
from datetime import datetime, timedelta

class ConstructionDatasetGenerator:
    """Generates fine-tuning datasets from construction project data"""

    def __init__(self, data_dir: str = "data/sample"):
        """
        Initialize dataset generator

        Args:
            data_dir: Directory containing sample data files
        """
        self.data_dir = Path(data_dir)
        self.project_data = None
        self.budget_data = None
        self.schedule_data = None
        self.resource_data = None

        # Load all data
        self._load_data()

    def _load_data(self):
        """Load all construction data files"""
        try:
            # Load project data
            project_file = self.data_dir / "Project_Database.xlsx"
            if project_file.exists():
                self.project_data = pd.read_excel(project_file)

            # Load budget data
            budget_file = self.data_dir / "Budget_Tracking.xlsx"
            if budget_file.exists():
                self.budget_data = pd.read_excel(budget_file)

            # Load schedule data
            schedule_file = self.data_dir / "Master_Schedule.xlsx"
            if schedule_file.exists():
                self.schedule_data = pd.read_excel(schedule_file)

            # Load resource data
            resource_file = self.data_dir / "Resource_Allocation.xlsx"
            if resource_file.exists():
                self.resource_data = pd.read_excel(resource_file)

            print(f"Loaded data: Projects={len(self.project_data) if self.project_data is not None else 0}, "
                  f"Budgets={len(self.budget_data) if self.budget_data is not None else 0}")

        except Exception as e:
            print(f"Error loading data: {e}")

    def generate_project_queries(self) -> List[Dict[str, str]]:
        """Generate project status and information queries"""
        queries = []

        if self.project_data is None:
            return queries

        for _, project in self.project_data.iterrows():
            project_name = project.get('ProjectName', 'Unknown Project')
            project_id = project.get('ProjectID', 'Unknown ID')
            status = project.get('Status', 'Unknown')
            progress = project.get('Progress', 0)
            manager = project.get('ProjectManager', 'Unknown')

            # Generate various query types
            query_templates = [
                {
                    "query": f"What's the status of {project_name}?",
                    "response": f"{project_name} (ID: {project_id}) is currently {status} with {progress}% completion. The project manager is {manager}. This appears to be a {project.get('ProjectType', 'construction')} project located in {project.get('Location', 'the specified area')}."
                },
                {
                    "query": f"How is {project_name} progressing?",
                    "response": f"{project_name} has achieved {progress}% completion and is in {status} phase. The project is managed by {manager} and is scheduled for completion by {project.get('PlannedEndDate', 'the planned date')}."
                },
                {
                    "query": f"Who is managing {project_name}?",
                    "response": f"{project_name} is managed by {manager}. The project is currently {status} with {progress}% completion."
                },
                {
                    "query": f"What type of project is {project_name}?",
                    "response": f"{project_name} is a {project.get('ProjectType', 'construction')} project located in {project.get('Location', 'the specified area')}. It is currently {status} with {progress}% completion."
                }
            ]

            queries.extend(query_templates)

        return queries

    def generate_budget_queries(self) -> List[Dict[str, str]]:
        """Generate budget analysis queries"""
        queries = []

        if self.budget_data is None:
            return queries

        for _, budget in self.budget_data.iterrows():
            project_name = budget.get('ProjectName', 'Unknown Project')
            allocated = budget.get('BudgetAllocated', 0)
            spent = budget.get('BudgetSpent', 0)
            remaining = allocated - spent

            if allocated > 0:
                variance = ((spent - allocated) / allocated) * 100
                variance_status = "over budget" if variance > 0 else "under budget"

                query_templates = [
                    {
                        "query": f"What's the budget status for {project_name}?",
                        "response": f"{project_name} has a budget of ${allocated:,.2f} with ${spent:,.2f} spent, leaving ${remaining:,.2f} remaining. The project is {variance_status} by {abs(variance):.1f}%."
                    },
                    {
                        "query": f"Is {project_name} over budget?",
                        "response": f"{project_name} is {variance_status} by {abs(variance):.1f}%. Total budget: ${allocated:,.2f}, Spent: ${spent:,.2f}, Remaining: ${remaining:,.2f}."
                    },
                    {
                        "query": f"How much budget is left for {project_name}?",
                        "response": f"{project_name} has ${remaining:,.2f} remaining from its ${allocated:,.2f} budget. ${spent:,.2f} has been spent so far."
                    }
                ]

                queries.extend(query_templates)

        return queries

    def generate_schedule_queries(self) -> List[Dict[str, str]]:
        """Generate schedule and timeline queries"""
        queries = []

        if self.schedule_data is None:
            return queries

        for _, schedule in self.schedule_data.iterrows():
            project_name = schedule.get('ProjectName', 'Unknown Project')
            task_name = schedule.get('TaskName', 'Unknown Task')
            start_date = schedule.get('StartDate', 'Unknown')
            end_date = schedule.get('EndDate', 'Unknown')
            progress = schedule.get('Progress', 0)

            query_templates = [
                {
                    "query": f"When does {task_name} start on {project_name}?",
                    "response": f"{task_name} on {project_name} is scheduled to start on {start_date} and end on {end_date}. Current progress is {progress}%."
                },
                {
                    "query": f"What's the timeline for {task_name}?",
                    "response": f"{task_name} runs from {start_date} to {end_date} with {progress}% completion."
                }
            ]

            queries.extend(query_templates)

        return queries

    def generate_general_construction_queries(self) -> List[Dict[str, str]]:
        """Generate general construction management queries"""
        queries = [
            {
                "query": "What are the main phases of a construction project?",
                "response": "Construction projects typically include: Pre-construction (planning, permits), Mobilization (site setup), Foundation, Framing, Rough-in (mechanical/electrical/plumbing), Finishing, and Close-out phases."
            },
            {
                "query": "How do you calculate construction project progress?",
                "response": "Project progress is typically calculated using Earned Value Management (EVM) which compares planned work vs actual completed work. Progress percentage = (Earned Value / Planned Value) × 100."
            },
            {
                "query": "What causes construction cost overruns?",
                "response": "Common causes of cost overruns include: change orders, material price increases, unforeseen site conditions, design changes, labor productivity issues, weather delays, and scope creep."
            },
            {
                "query": "How do you manage construction risks?",
                "response": "Construction risk management involves: identifying risks (safety, schedule, cost, quality), assessing probability and impact, developing mitigation strategies, and monitoring through regular risk reviews."
            },
            {
                "query": "What are key construction safety regulations?",
                "response": "Key safety regulations include OSHA standards for fall protection, hazard communication, electrical safety, and excavation. Regular safety training, PPE requirements, and incident reporting are essential."
            },
            {
                "query": "How do you handle construction schedule delays?",
                "response": "Schedule delay management includes: identifying delay causes, assessing impact, implementing recovery plans (crashing/fast-tracking), updating baselines, and communicating with stakeholders about changes."
            }
        ]

        return queries

    def generate_qa_pairs(self) -> List[Dict[str, str]]:
        """Generate question-answer pairs for fine-tuning"""
        qa_pairs = []

        # Generate from project data
        qa_pairs.extend(self.generate_project_queries())

        # Generate from budget data
        qa_pairs.extend(self.generate_budget_queries())

        # Generate from schedule data
        qa_pairs.extend(self.generate_schedule_queries())

        # Add general construction knowledge
        qa_pairs.extend(self.generate_general_construction_queries())

        return qa_pairs

    def create_fine_tuning_dataset(self, output_file: str = "construction_finetune_dataset.jsonl",
                                   num_samples: int = None) -> str:
        """
        Create a fine-tuning dataset in JSONL format

        Args:
            output_file: Output file path
            num_samples: Number of samples to generate (None for all)

        Returns:
            Path to created dataset file
        """
        qa_pairs = self.generate_qa_pairs()

        if num_samples:
            qa_pairs = random.sample(qa_pairs, min(num_samples, len(qa_pairs)))

        # Convert to fine-tuning format
        fine_tuning_data = []
        for pair in qa_pairs:
            # Format for instruction tuning
            formatted_pair = {
                "instruction": pair["query"],
                "input": "",
                "output": pair["response"]
            }
            fine_tuning_data.append(formatted_pair)

        # Save to JSONL file
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in fine_tuning_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        print(f"Created fine-tuning dataset with {len(fine_tuning_data)} samples at {output_path}")

        return str(output_path)

    def create_conversation_dataset(self, output_file: str = "construction_conversation_dataset.jsonl") -> str:
        """
        Create a conversation-style dataset for chat fine-tuning

        Args:
            output_file: Output file path

        Returns:
            Path to created dataset file
        """
        conversations = []

        # Create multi-turn conversations
        project_conversations = [
            [
                {"role": "user", "content": "What's the status of the Downtown Office Building?"},
                {"role": "assistant", "content": "The Downtown Office Building is currently in progress with 65% completion. It's managed by John Smith and has a budget of $2,500,000."},
                {"role": "user", "content": "Is it on schedule?"},
                {"role": "assistant", "content": "Based on the project data, the Downtown Office Building is scheduled for completion by December 15, 2024. With 65% completion, it appears to be on track for the planned timeline."}
            ],
            [
                {"role": "user", "content": "Show me projects that are over budget"},
                {"role": "assistant", "content": "I found several projects that are currently over budget. Let me analyze the budget variance data for you."},
                {"role": "user", "content": "Which one has the highest variance?"},
                {"role": "assistant", "content": "Looking at the budget analysis, the Highway Bridge Renovation shows the highest variance at 15.2% over budget. This $4.2M infrastructure project has spent more than allocated due to unforeseen site conditions."}
            ]
        ]

        conversations.extend(project_conversations)

        # Save conversation dataset
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            for conv in conversations:
                f.write(json.dumps({"conversations": conv}, ensure_ascii=False) + '\n')

        print(f"Created conversation dataset with {len(conversations)} conversations at {output_path}")

        return str(output_path)

def main():
    """Generate fine-tuning datasets"""
    print("🏗️ Construction Management Fine-tuning Dataset Generator")
    print("=" * 60)

    generator = ConstructionDatasetGenerator()

    # Create instruction tuning dataset
    instruction_file = generator.create_fine_tuning_dataset(
        "data/construction_instruction_dataset.jsonl",
        num_samples=500
    )

    # Create conversation dataset
    conversation_file = generator.create_conversation_dataset(
        "data/construction_conversation_dataset.jsonl"
    )

    print("\n✅ Dataset Generation Complete!")
    print(f"📁 Instruction dataset: {instruction_file}")
    print(f"📁 Conversation dataset: {conversation_file}")
    print("\n📋 Next steps:")
    print("1. Review and clean the generated datasets")
    print("2. Set up your local LLM training environment")
    print("3. Use these datasets for fine-tuning")
    print("4. Test the fine-tuned model with construction queries")

if __name__ == "__main__":
    main()