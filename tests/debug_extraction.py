#!/usr/bin/env python3
"""Debug script to test GCA value extraction from AI responses"""

import re
import requests

# Sample response text (from actual AI)
sample_response = """Hey there! Let's calculate the Gross Constructible Area (GCA) for the projects you mentioned:

1. **72 Perth Avenue:**
   - Total GCA: 214,384 SF

2. **17175 Yonge St:**
   - Total GCA: 269,141 SF

3. **Azure Road:**
   - Total GCA: 376,332 SF

To find the total GCA for all three projects, you would add up the GCA for each project:
214,384 SF + 269,141 SF + 376,332 SF = Total GCA for all projects

If you need more details or have any other questions, feel free to ask!"""

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
    
    # Try multiple patterns - ESCAPE the project name properly for markdown
    # In AI responses, project names often appear as "**Name:**"
    patterns = [
        # Pattern 1: Project name in bold markdown with GCA
        (r'\*\*' + re.escape(project_name) + r'\*\*:?\s*-?\s*Total GCA:\s*(\d{1,3}(?:,\d{3})*)\s*SF', "Markdown bold with Total GCA"),
        # Pattern 2: Just project name then closest number
        (re.escape(project_name) + r'.*?(\d{1,3}(?:,\d{3})*)\s*(?:square feet|SF)', "Name then number"),
    ]
    
    for pattern, desc in patterns:
        match = re.search(pattern, sample_response, re.IGNORECASE | re.DOTALL)
        
        if match:
            extracted_value = int(match.group(1).replace(',', ''))
            expected_value = expected[project_id]
            status = "✅" if extracted_value == expected_value else "❌"
            print(f"  {desc}:")
            print(f"    {status} Extracted: {extracted_value:,} SF (Expected: {expected_value:,} SF)")
            break
    else:
        print(f"  ❌ No match found with any pattern!")

print("\n" + "=" * 60)
