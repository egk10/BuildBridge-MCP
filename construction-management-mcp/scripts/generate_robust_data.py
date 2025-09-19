#!/usr/bin/env python3
"""
Robust Sample Data Generator for Construction MCP
Creates comprehensive project data with realistic delays, budget overruns, and detailed tracking
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json
from pathlib import Path

class ConstructionDataGenerator:
    """Generate realistic construction project data with MS Project-style details"""
    
    def __init__(self):
        self.project_types = [
            "Commercial Office Building",
            "Residential Complex", 
            "Industrial Warehouse",
            "Healthcare Facility",
            "Educational Institution",
            "Retail Shopping Center",
            "Mixed-Use Development",
            "Infrastructure Project"
        ]
        
        self.phases = [
            "Pre-Construction",
            "Site Preparation", 
            "Foundation",
            "Structural",
            "MEP Systems",
            "Interior Finishes",
            "Exterior Finishes",
            "Final Inspections",
            "Project Closeout"
        ]
        
        self.risk_factors = [
            "Weather delays",
            "Material shortages", 
            "Labor availability",
            "Permit delays",
            "Change orders",
            "Site conditions",
            "Equipment issues",
            "Supply chain disruptions"
        ]
        
        self.data_dir = Path("data/sample")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_master_schedule(self) -> pd.DataFrame:
        """Generate detailed project schedule with Gantt chart style data"""
        tasks = []
        
        projects = [
            {"id": "PROJ001", "name": "Downtown Office Tower", "type": "Commercial Office Building"},
            {"id": "PROJ002", "name": "Riverside Apartments", "type": "Residential Complex"},
            {"id": "PROJ003", "name": "Tech Campus Expansion", "type": "Commercial Office Building"},
            {"id": "PROJ004", "name": "Metro Hospital Wing", "type": "Healthcare Facility"},
            {"id": "PROJ005", "name": "Logistics Hub Warehouse", "type": "Industrial Warehouse"},
            {"id": "PROJ006", "name": "University Science Center", "type": "Educational Institution"},
            {"id": "PROJ007", "name": "Suburban Shopping Plaza", "type": "Retail Shopping Center"}
        ]
        
        task_id = 1
        for project in projects:
            project_start = datetime(2024, 1, 15) + timedelta(days=random.randint(0, 90))
            current_date = project_start
            
            for phase_idx, phase in enumerate(self.phases):
                # Calculate phase duration (with realistic variations)
                base_duration = {
                    "Pre-Construction": 30,
                    "Site Preparation": 45, 
                    "Foundation": 60,
                    "Structural": 120,
                    "MEP Systems": 90,
                    "Interior Finishes": 75,
                    "Exterior Finishes": 45,
                    "Final Inspections": 15,
                    "Project Closeout": 10
                }
                
                duration = base_duration[phase] + random.randint(-10, 20)
                end_date = current_date + timedelta(days=duration)
                
                # Add realistic delays for some phases
                delay_chance = 0.3 if random.random() < 0.3 else 0
                if delay_chance:
                    delay_days = random.randint(5, 30)
                    end_date += timedelta(days=delay_days)
                    delay_reason = random.choice(self.risk_factors)
                else:
                    delay_days = 0
                    delay_reason = ""
                
                # Calculate progress (with realistic patterns)
                if end_date < datetime.now():
                    progress = 100  # Completed
                elif current_date > datetime.now():
                    progress = 0    # Not started
                else:
                    # In progress - calculate based on time elapsed
                    total_days = (end_date - current_date).days
                    elapsed_days = (datetime.now() - current_date).days
                    progress = min(100, max(0, (elapsed_days / total_days) * 100))
                    
                    # Add some randomness to progress
                    progress += random.randint(-10, 10)
                    progress = max(0, min(100, progress))
                
                # Determine status
                if progress == 100:
                    status = "Completed"
                elif progress == 0:
                    status = "Not Started"
                elif delay_days > 0:
                    status = "Delayed"
                elif progress > 80:
                    status = "Near Completion"
                else:
                    status = "In Progress"
                
                # Assign responsible team
                teams = ["General Contractor", "Structural", "MEP", "Finishes", "Quality Control"]
                responsible_team = random.choice(teams)
                
                tasks.append({
                    "Task_ID": f"T{task_id:04d}",
                    "Project_ID": project["id"],
                    "Project_Name": project["name"],
                    "Project_Type": project["type"],
                    "Phase": phase,
                    "Task_Name": f"{phase} - {project['name']}",
                    "Start_Date": current_date.strftime("%Y-%m-%d"),
                    "End_Date": end_date.strftime("%Y-%m-%d"),
                    "Duration_Days": duration + delay_days,
                    "Progress_Percent": round(progress, 1),
                    "Status": status,
                    "Responsible_Team": responsible_team,
                    "Delay_Days": delay_days,
                    "Delay_Reason": delay_reason,
                    "Priority": random.choice(["High", "Medium", "Low"]),
                    "Dependencies": f"T{max(1, task_id-1):04d}" if task_id > 1 and phase_idx > 0 else "",
                    "Critical_Path": random.choice([True, False]) if phase in ["Foundation", "Structural", "MEP Systems"] else False
                })
                
                current_date = end_date + timedelta(days=random.randint(1, 5))  # Small buffer between phases
                task_id += 1
        
        return pd.DataFrame(tasks)
    
    def generate_budget_tracking(self) -> pd.DataFrame:
        """Generate detailed budget tracking with cost overruns and analysis"""
        budget_items = []
        
        projects = [
            {"id": "PROJ001", "name": "Downtown Office Tower", "total_budget": 25000000},
            {"id": "PROJ002", "name": "Riverside Apartments", "total_budget": 18000000},
            {"id": "PROJ003", "name": "Tech Campus Expansion", "total_budget": 35000000},
            {"id": "PROJ004", "name": "Metro Hospital Wing", "total_budget": 45000000},
            {"id": "PROJ005", "name": "Logistics Hub Warehouse", "total_budget": 12000000},
            {"id": "PROJ006", "name": "University Science Center", "total_budget": 28000000},
            {"id": "PROJ007", "name": "Suburban Shopping Plaza", "total_budget": 15000000}
        ]
        
        cost_categories = [
            {"category": "Site Preparation", "percentage": 0.08},
            {"category": "Foundation", "percentage": 0.15},
            {"category": "Structural Steel", "percentage": 0.20},
            {"category": "Concrete", "percentage": 0.12},
            {"category": "MEP Systems", "percentage": 0.25},
            {"category": "Interior Finishes", "percentage": 0.12},
            {"category": "Exterior Finishes", "percentage": 0.05},
            {"category": "Equipment", "percentage": 0.03}
        ]
        
        for project in projects:
            for category in cost_categories:
                allocated_amount = project["total_budget"] * category["percentage"]
                
                # Add realistic spending patterns
                spending_variance = random.uniform(0.85, 1.25)  # -15% to +25% variance
                actual_spent = allocated_amount * spending_variance * random.uniform(0.3, 0.95)
                
                # Calculate remaining budget
                remaining_budget = allocated_amount - actual_spent
                
                # Determine status
                if actual_spent > allocated_amount:
                    budget_status = "Over Budget"
                    variance_percent = ((actual_spent - allocated_amount) / allocated_amount) * 100
                elif actual_spent > allocated_amount * 0.9:
                    budget_status = "Near Budget Limit"
                    variance_percent = ((actual_spent - allocated_amount) / allocated_amount) * 100
                else:
                    budget_status = "Within Budget"
                    variance_percent = ((actual_spent - allocated_amount) / allocated_amount) * 100
                
                # Add spending by month for trend analysis
                months_data = []
                current_date = datetime(2024, 1, 1)
                monthly_spend = actual_spent / 12  # Distribute over 12 months
                
                for month in range(1, 13):
                    month_variance = random.uniform(0.5, 1.8)  # Monthly variation
                    month_amount = monthly_spend * month_variance
                    months_data.append({
                        "month": current_date.strftime("%Y-%m"),
                        "amount": round(month_amount, 2)
                    })
                    current_date += timedelta(days=30)
                
                budget_items.append({
                    "Budget_ID": f"B{len(budget_items)+1:04d}",
                    "Project_ID": project["id"],
                    "Project_Name": project["name"],
                    "Cost_Category": category["category"],
                    "Allocated_Budget": round(allocated_amount, 2),
                    "Actual_Spent": round(actual_spent, 2),
                    "Remaining_Budget": round(remaining_budget, 2),
                    "Budget_Status": budget_status,
                    "Variance_Percent": round(variance_percent, 2),
                    "Last_Updated": datetime.now().strftime("%Y-%m-%d"),
                    "Vendor": f"{category['category']} Contractor Inc.",
                    "Purchase_Orders": random.randint(5, 25),
                    "Committed_Costs": round(allocated_amount * random.uniform(0.1, 0.3), 2),
                    "Monthly_Spending": json.dumps(months_data),
                    "Risk_Level": random.choice(["Low", "Medium", "High"]),
                    "Notes": f"Budget tracking for {category['category']} activities"
                })
        
        return pd.DataFrame(budget_items)
    
    def generate_project_database(self) -> pd.DataFrame:
        """Generate comprehensive project database with all key information"""
        projects = []
        
        project_data = [
            {
                "id": "PROJ001", "name": "Downtown Office Tower", "type": "Commercial Office Building",
                "location": "123 Business District, Metro City", "size": "450,000 sq ft", 
                "budget": 25000000, "duration": 18
            },
            {
                "id": "PROJ002", "name": "Riverside Apartments", "type": "Residential Complex",
                "location": "789 Riverside Drive, Metro City", "size": "200 units", 
                "budget": 18000000, "duration": 14
            },
            {
                "id": "PROJ003", "name": "Tech Campus Expansion", "type": "Commercial Office Building",
                "location": "456 Innovation Park, Tech Valley", "size": "600,000 sq ft", 
                "budget": 35000000, "duration": 24
            },
            {
                "id": "PROJ004", "name": "Metro Hospital Wing", "type": "Healthcare Facility",
                "location": "321 Medical Center Dr, Metro City", "size": "300,000 sq ft", 
                "budget": 45000000, "duration": 30
            },
            {
                "id": "PROJ005", "name": "Logistics Hub Warehouse", "type": "Industrial Warehouse",
                "location": "987 Industrial Blvd, Port District", "size": "800,000 sq ft", 
                "budget": 12000000, "duration": 12
            },
            {
                "id": "PROJ006", "name": "University Science Center", "type": "Educational Institution",
                "location": "654 Campus Way, University Town", "size": "250,000 sq ft", 
                "budget": 28000000, "duration": 20
            },
            {
                "id": "PROJ007", "name": "Suburban Shopping Plaza", "type": "Retail Shopping Center",
                "location": "147 Mall Road, Suburbia", "size": "180,000 sq ft", 
                "budget": 15000000, "duration": 16
            }
        ]
        
        for proj_data in project_data:
            start_date = datetime(2024, 1, 15) + timedelta(days=random.randint(0, 90))
            end_date = start_date + timedelta(days=proj_data["duration"] * 30)
            
            # Calculate current progress
            if end_date < datetime.now():
                progress = 100
                status = "Completed"
            elif start_date > datetime.now():
                progress = 0
                status = "Planning"
            else:
                total_days = (end_date - start_date).days
                elapsed_days = (datetime.now() - start_date).days
                progress = min(100, max(0, (elapsed_days / total_days) * 100))
                
                if progress < 25:
                    status = "Early Stage"
                elif progress < 75:
                    status = "In Progress"
                else:
                    status = "Near Completion"
            
            # Add realistic complications
            risk_score = random.randint(1, 10)
            if risk_score > 7:
                status = "At Risk"
            elif risk_score > 8:
                status = "Critical"
            
            projects.append({
                "Project_ID": proj_data["id"],
                "Project_Name": proj_data["name"],
                "Project_Type": proj_data["type"],
                "Location": proj_data["location"],
                "Project_Size": proj_data["size"],
                "Total_Budget": proj_data["budget"],
                "Start_Date": start_date.strftime("%Y-%m-%d"),
                "End_Date": end_date.strftime("%Y-%m-%d"),
                "Duration_Months": proj_data["duration"],
                "Progress_Percent": round(progress, 1),
                "Status": status,
                "Project_Manager": f"PM {random.choice(['Johnson', 'Smith', 'Williams', 'Brown', 'Davis'])}",
                "General_Contractor": f"{random.choice(['Alpha', 'Beta', 'Gamma', 'Delta'])} Construction",
                "Architect": f"{random.choice(['Modern', 'Classic', 'Urban', 'Green'])} Design Group",
                "Client": f"{random.choice(['Metro', 'Global', 'Premier', 'United'])} {random.choice(['Corp', 'Industries', 'Holdings', 'Group'])}",
                "Risk_Score": risk_score,
                "Quality_Score": random.randint(6, 10),
                "Safety_Score": random.randint(7, 10),
                "Environmental_Impact": random.choice(["Low", "Medium", "High"]),
                "Sustainability_Rating": random.choice(["LEED Silver", "LEED Gold", "LEED Platinum", "Green Building"]),
                "Permits_Status": random.choice(["Approved", "Pending", "Under Review"]),
                "Last_Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Notes": f"Major {proj_data['type'].lower()} project with {random.choice(['standard', 'complex', 'innovative'])} requirements"
            })
        
        return pd.DataFrame(projects)
    
    def generate_resource_allocation(self) -> pd.DataFrame:
        """Generate resource allocation and workforce tracking"""
        resources = []
        
        resource_types = [
            {"type": "Project Manager", "rate": 150, "availability": 1.0},
            {"type": "Site Supervisor", "rate": 120, "availability": 1.0},
            {"type": "Structural Engineer", "rate": 140, "availability": 0.5},
            {"type": "MEP Engineer", "rate": 130, "availability": 0.7},
            {"type": "General Labor", "rate": 35, "availability": 8.0},
            {"type": "Skilled Carpenter", "rate": 45, "availability": 4.0},
            {"type": "Electrician", "rate": 55, "availability": 3.0},
            {"type": "Plumber", "rate": 50, "availability": 2.0},
            {"type": "Heavy Equipment Operator", "rate": 60, "availability": 2.0},
            {"type": "Safety Inspector", "rate": 80, "availability": 0.5}
        ]
        
        projects = ["PROJ001", "PROJ002", "PROJ003", "PROJ004", "PROJ005", "PROJ006", "PROJ007"]
        
        resource_id = 1
        for project in projects:
            for resource in resource_types:
                allocated_hours = resource["availability"] * 40 * random.uniform(0.5, 1.2)  # Weekly hours
                utilized_hours = allocated_hours * random.uniform(0.7, 0.95)
                
                efficiency = (utilized_hours / allocated_hours) * 100 if allocated_hours > 0 else 0
                
                # Calculate costs
                allocated_cost = allocated_hours * resource["rate"]
                actual_cost = utilized_hours * resource["rate"] * random.uniform(0.95, 1.1)  # Include overtime/variations
                
                resources.append({
                    "Resource_ID": f"R{resource_id:04d}",
                    "Project_ID": project,
                    "Resource_Type": resource["type"],
                    "Resource_Name": f"{resource['type']} - {random.choice(['Team A', 'Team B', 'Team C'])}",
                    "Hourly_Rate": resource["rate"],
                    "Allocated_Hours_Weekly": round(allocated_hours, 1),
                    "Utilized_Hours_Weekly": round(utilized_hours, 1),
                    "Efficiency_Percent": round(efficiency, 1),
                    "Allocated_Cost_Weekly": round(allocated_cost, 2),
                    "Actual_Cost_Weekly": round(actual_cost, 2),
                    "Start_Date": (datetime.now() - timedelta(days=random.randint(30, 180))).strftime("%Y-%m-%d"),
                    "End_Date": (datetime.now() + timedelta(days=random.randint(30, 180))).strftime("%Y-%m-%d"),
                    "Availability_Status": random.choice(["Available", "Partially Available", "Overallocated"]),
                    "Skill_Level": random.choice(["Junior", "Mid-Level", "Senior", "Expert"]),
                    "Certification_Status": random.choice(["Current", "Expiring Soon", "Expired"]),
                    "Performance_Rating": random.randint(7, 10),
                    "Notes": f"Resource allocation for {resource['type']} on project {project}"
                })
                
                resource_id += 1
        
        return pd.DataFrame(resources)
    
    def save_all_datasets(self):
        """Generate and save all sample datasets in both Excel and CSV formats"""
        print("🏗️ Generating Construction MCP Sample Data...")
        
        # Generate datasets
        print("📋 Creating Master Schedule...")
        schedule_df = self.generate_master_schedule()
        schedule_df.to_excel(self.data_dir / "Master_Schedule.xlsx", index=False)
        schedule_df.to_csv(self.data_dir / "Master_Schedule.csv", index=False)
        
        print("💰 Creating Budget Tracking...")
        budget_df = self.generate_budget_tracking()
        budget_df.to_excel(self.data_dir / "Budget_Tracking.xlsx", index=False)
        budget_df.to_csv(self.data_dir / "Budget_Tracking.csv", index=False)
        
        print("📊 Creating Project Database...")
        projects_df = self.generate_project_database()
        projects_df.to_excel(self.data_dir / "Project_Database.xlsx", index=False)
        projects_df.to_csv(self.data_dir / "Project_Database.csv", index=False)
        
        print("👥 Creating Resource Allocation...")
        resources_df = self.generate_resource_allocation()
        resources_df.to_excel(self.data_dir / "Resource_Allocation.xlsx", index=False)
        resources_df.to_csv(self.data_dir / "Resource_Allocation.csv", index=False)
        
        # Create consolidated Excel workbook with multiple sheets (typical for construction management)
        print("📑 Creating Consolidated Construction Management Workbook...")
        with pd.ExcelWriter(self.data_dir / "Construction_Management_Data.xlsx", engine='openpyxl') as writer:
            projects_df.to_excel(writer, sheet_name='Projects', index=False)
            schedule_df.to_excel(writer, sheet_name='Schedule', index=False)
            budget_df.to_excel(writer, sheet_name='Budget_Tracking', index=False)
            resources_df.to_excel(writer, sheet_name='Resources', index=False)
            
            # Add summary sheet
            summary_df = pd.DataFrame([
                {'Metric': 'Total Projects', 'Value': len(projects_df)},
                {'Metric': 'Total Budget', 'Value': f"${projects_df['Total_Budget'].sum():,.0f}"},
                {'Metric': 'Active Projects', 'Value': len(projects_df[projects_df['Status'] != 'Completed'])},
                {'Metric': 'Avg Progress', 'Value': f"{projects_df['Progress_Percent'].mean():.1f}%"},
                {'Metric': 'Tasks with Delays', 'Value': len(schedule_df[schedule_df['Delay_Days'] > 0])},
                {'Metric': 'Over Budget Items', 'Value': len(budget_df[budget_df['Budget_Status'] == 'Over Budget'])},
                {'Metric': 'Total Resources', 'Value': len(resources_df)},
                {'Metric': 'Data Generated', 'Value': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            ])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Generate summary report
        print("📈 Creating Data Summary...")
        summary = {
            "generation_date": datetime.now().isoformat(),
            "datasets": {
                "projects": int(len(projects_df)),
                "schedule_tasks": int(len(schedule_df)),
                "budget_items": int(len(budget_df)),
                "resource_allocations": int(len(resources_df))
            },
            "project_status_summary": {k: int(v) for k, v in projects_df['Status'].value_counts().to_dict().items()},
            "total_budget": float(projects_df['Total_Budget'].sum()),
            "avg_project_progress": float(projects_df['Progress_Percent'].mean()),
            "delayed_tasks": int(len(schedule_df[schedule_df['Delay_Days'] > 0])),
            "over_budget_items": int(len(budget_df[budget_df['Budget_Status'] == 'Over Budget']))
        }
        
        with open(self.data_dir / "data_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"✅ Generated {len(projects_df)} projects with comprehensive data")
        print(f"📁 Data saved to: {self.data_dir.absolute()}")
        print(f"📊 Summary: {summary['datasets']}")
        print(f"📑 Formats: Excel (.xlsx), CSV (.csv), Consolidated Workbook")
        print(f"🏗️ Ready for Construction MCP natural language queries!")
        
        return summary

if __name__ == "__main__":
    generator = ConstructionDataGenerator()
    summary = generator.save_all_datasets()
    
    # Print some sample insights
    print("\n🔍 Sample Data Insights:")
    print(f"- Total Projects: {summary['datasets']['projects']}")
    print(f"- Total Tasks: {summary['datasets']['schedule_tasks']}")
    print(f"- Total Budget: ${summary['total_budget']:,.0f}")
    print(f"- Average Progress: {summary['avg_project_progress']:.1f}%")
    print(f"- Delayed Tasks: {summary['delayed_tasks']}")
    print(f"- Over Budget Items: {summary['over_budget_items']}")