#!/usr/bin/env python3
"""
Create ground truth data from Google Sheets for testing validation

This script extracts current data from cached Google Sheets and creates
a ground truth JSON file that can be used to validate MCP query accuracy.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def extract_ground_truth():
    """Extract ground truth data from cached Google Sheets data"""
    
    projects = ['72_perth', '17175_yonge_st', 'azure_road']
    cache_dir = Path(__file__).parent.parent / "cache" / "normalized"
    
    ground_truth = {
        "generated_at": datetime.now().isoformat(),
        "source": "Google Sheets cache",
        "projects": {}
    }
    
    for project_id in projects:
        cache_file = cache_dir / f'{project_id}.json'
        
        if not cache_file.exists():
            print(f"⚠️  Cache not found for {project_id} at {cache_file}")
            print(f"   Run: python scripts/refresh_manifest_local.py")
            continue
        
        with open(cache_file, 'r') as f:
            data = json.load(f)
        
        project_data = data.get('project', {})
        
        # Extract and convert values
        ground_truth['projects'][project_id] = {
            'name': project_data.get('Project_Name', 'Unknown'),
            'location': project_data.get('Location', 'Unknown'),
            'client': project_data.get('Client', 'Unknown'),
            'budget_date': project_data.get('Budget_Date', 'Unknown'),
            'total_budget': float(project_data.get('Total_Budget', 0)),
            'total_direct_cost': float(project_data.get('Total_Direct_Cost', 0)),
            'building_area_metric': float(project_data.get('Building_Area_Metric', 0)),
            'total_gca_sf': float(project_data.get('Total_GCA_SF', 0)),
            'parking_stalls': int(project_data.get('Parking_Stalls', 0)),
            'parking_below_grade': int(project_data.get('Parking_Below_Grade', 0)),
            'parking_above_grade': int(project_data.get('Parking_Above_Grade', 0)) if project_data.get('Parking_Above_Grade') else 0,
            'parking_total': int(project_data.get('Parking_Total', 0)),
            'subtotal_siteworks': float(project_data.get('Subtotal_Siteworks', 0)),
            'division_cost_totals': project_data.get('Division_Cost_Totals', {})
        }
        
        print(f"✅ Extracted ground truth for {project_id}: {ground_truth['projects'][project_id]['name']}")
    
    # Calculate portfolio totals
    ground_truth['portfolio_totals'] = {
        'total_projects': len(ground_truth['projects']),
        'total_budget': sum(p['total_budget'] for p in ground_truth['projects'].values()),
        'total_direct_cost': sum(p['total_direct_cost'] for p in ground_truth['projects'].values()),
        'total_gca_sf': sum(p['total_gca_sf'] for p in ground_truth['projects'].values()),
        'total_building_area_metric': sum(p['building_area_metric'] for p in ground_truth['projects'].values()),
        'total_parking': sum(p['parking_total'] for p in ground_truth['projects'].values()),
    }
    
    # Calculate averages
    num_projects = len(ground_truth['projects'])
    if num_projects > 0:
        ground_truth['portfolio_averages'] = {
            'avg_budget': ground_truth['portfolio_totals']['total_budget'] / num_projects,
            'avg_direct_cost': ground_truth['portfolio_totals']['total_direct_cost'] / num_projects,
            'avg_gca_sf': ground_truth['portfolio_totals']['total_gca_sf'] / num_projects,
            'avg_parking': ground_truth['portfolio_totals']['total_parking'] / num_projects,
        }
    
    # Save ground truth
    output_dir = Path(__file__).parent.parent / "tests"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / 'ground_truth.json'
    
    with open(output_file, 'w') as f:
        json.dump(ground_truth, f, indent=2)
    
    print(f"\n✅ Ground truth saved to {output_file}")
    print(f"   Projects: {num_projects}")
    print(f"   Total Portfolio Budget: ${ground_truth['portfolio_totals']['total_budget']:,.0f}")
    print(f"   Total Direct Cost: ${ground_truth['portfolio_totals']['total_direct_cost']:,.0f}")
    print(f"   Total GCA: {ground_truth['portfolio_totals']['total_gca_sf']:,.0f} SF")
    print(f"   Total Parking: {ground_truth['portfolio_totals']['total_parking']:,} stalls")
    
    return ground_truth

if __name__ == "__main__":
    print("=" * 60)
    print("🏗️  BuildBridge-MCP Ground Truth Generator")
    print("=" * 60)
    print()
    
    try:
        ground_truth = extract_ground_truth()
        print("\n✅ Ground truth generation complete!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error generating ground truth: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
