#!/usr/bin/env python3
"""Debug script to test GCA value extraction from AI responses"""

import re
import requests

# Sample response text (from actual AI)
sample_response = """To find the total Gross Construction Area (GCA) for the projects Azure Road, 17175 Yonge St, and 72 Perth Avenue, we need to sum up the GCA for each project. Here's the breakdown:

1. **Azure Road:**
   - Total GCA: 376,332 SF

2. **17175 Yonge St:**
   - Total GCA: 269,141 SF

3. **72 Perth Avenue:**
   - Total GCA: 214,384 SF

To calculate the total GCA for all three projects, you would add up the GCA for each project:
376,332 SF (Azure Road) + 269,141 SF (17175 Yonge St) + 214,384 SF (72 Perth Avenue) = Total GCA for all projects

Adding these together:
376,332 + 269,141 + 214,384 = 859,857 SF

Therefore, the total Gross Construction Area for the projects Azure Road, 17175 Yonge St, and 72 Perth Avenue is 859,857 square feet."""

print("=" * 60)
print("Testing GCA Extraction")
print("=" * 60)

projects = {
    '72_perth': '72 Perth Avenue',
    '17175_yonge_st': '17175 Yonge St',
    'azure_road': 'Azure Road'
}

expected = {
    '72_perth': 214384,
    '17175_yonge_st': 269141,
    'azure_road': 376332
}

for project_id, project_name in projects.items():
    print(f"\n🔍 Extracting GCA for: {project_name}")
    
    # Strategy: Find the project section first, then extract from ONLY that section
    # This prevents cross-project value contamination
    
    # Pattern: **Name:** or **Name** followed by content until next numbered item or end
    section_patterns = [
        # Colon inside bold: **Name:**
        (r'\*\*' + re.escape(project_name) + r':\*\*(.*?)(?=\n\d+\.\s|\Z)', "Colon inside bold"),
        # Colon outside bold: **Name**:
        (r'\*\*' + re.escape(project_name) + r'\*\*:?(.*?)(?=\n\d+\.\s|\Z)', "Colon outside bold"),
    ]
    
    found_section = False
    for section_pattern, pattern_desc in section_patterns:
        section_match = re.search(section_pattern, sample_response, re.DOTALL)
        
        if section_match:
            project_section = section_match.group(1)
            print(f"  📍 Found section using '{pattern_desc}' ({len(project_section)} chars)")
            found_section = True
            
            # Extract GCA from this section only
            gca_patterns = [
                (r'Total GCA:\s*(\d{1,3}(?:,\d{3})*)\s*SF', "Total GCA"),
                (r'GCA:\s*(\d{1,3}(?:,\d{3})*)\s*SF', "GCA"),
                (r'(\d{1,3}(?:,\d{3})*)\s*SF', "Any number SF"),
            ]
            
            for gca_pattern, gca_desc in gca_patterns:
                gca_match = re.search(gca_pattern, project_section)
                if gca_match:
                    extracted_value = int(gca_match.group(1).replace(',', ''))
                    expected_value = expected[project_id]
                    status = "✅" if extracted_value == expected_value else "❌"
                    print(f"    {gca_desc}: {status} {extracted_value:,} SF (expected {expected_value:,})")
                    if extracted_value == expected_value:
                        break
            break
    
    if not found_section:
        print(f"  ❌ Could not find project section")

print("\n" + "=" * 60)
